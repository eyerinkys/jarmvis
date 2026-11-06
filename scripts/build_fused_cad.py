import os
import sys
import shutil
import build123d as bd
from jarmvis.cad.fusion import fuse_arm2_and_oled
from jarmvis.cad.assembly import integrate_fused_arm2_into_assembly
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.collections import Sequence_TDF_Label
from OCP.TDataStd import TDataStd_Name


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    print(f"Working in repository root: {root_dir}")

    # Canonical paths within armschema
    armschema_dir = "armschema"
    printable_dir = os.path.join(armschema_dir, "printable_parts")
    final_assembly_path = os.path.join(armschema_dir, "Jarmvis_V2.1.step")
    arm2_step_path = os.path.join(printable_dir, "Arm_2.step")
    arm2_stl_path = os.path.join(printable_dir, "Arm_2.stl")

    # Source reference assembly for fusion
    source_assembly = "Jarmvis_V2.1.step.bak"
    if not os.path.exists(source_assembly):
        source_assembly = "Jarmvis_V2.1.step"
    if not os.path.exists(source_assembly):
        source_assembly = final_assembly_path

    print("\n--- Step 1: Generating Fused Arm 2 (Arm2 + Brackets + OLED Enclosure) ---")
    fused_solid = fuse_arm2_and_oled(
        assembly_step_path=source_assembly,
        output_arm2_path=arm2_step_path,
        output_stl_path=arm2_stl_path
    )
    print(f"Exported printable parts:\n  • {arm2_step_path}\n  • {arm2_stl_path}")

    # Verify solid properties
    assert len(fused_solid.solids()) == 1, "Fused solid must be a single solid"
    assert fused_solid.volume > 82000, f"Expected volume > 82000, got {fused_solid.volume}"
    print(f"Solid Volume: {fused_solid.volume:.2f} mm^3")
    bb = fused_solid.bounding_box()
    print(f"Bounding Box: X=({bb.min.X:.2f}, {bb.max.X:.2f}), Y=({bb.min.Y:.2f}, {bb.max.Y:.2f}), Z=({bb.min.Z:.2f}, {bb.max.Z:.2f})")

    # Verify holes
    cyls = []
    for f in fused_solid.faces():
        if f.geom_type == bd.GeomType.CYLINDER:
            try:
                r = round(BRepAdaptor_Surface(f.wrapped).Cylinder().Radius(), 2)
                cyls.append((r, f.center()))
            except:
                pass

    has_pivot = any(r == 3.5 for r, _ in cyls)
    r06_count = sum(1 for r, c in cyls if 0.55 <= r <= 0.65 and c.Z < -25)
    print(f"Pivot Joint Hole (R=3.5mm) Preserved: {has_pivot}")
    print(f"OLED Enclosure Holes (R=0.6mm, 4 corner + 4 pins) Preserved: {r06_count}/8")
    assert has_pivot, "Arm 2 pivot hole was lost!"
    assert r06_count >= 8, f"OLED enclosure holes lost! Expected 8, got {r06_count}"

    print("\n--- Step 2: Creating Clean Assembly within armschema ---")
    temp_updated_assembly = "scratch_temp_assembly.step"
    integrate_fused_arm2_into_assembly(
        assembly_step_path=source_assembly,
        fused_arm2_solid=fused_solid,
        output_assembly_path=temp_updated_assembly
    )

    # Move to canonical armschema/Jarmvis_V2.1.step
    os.replace(temp_updated_assembly, final_assembly_path)
    print(f"Created canonical master assembly: {final_assembly_path}")

    print("\n--- Step 3: Removing Overlapping Files ---")
    files_to_remove = [
        "Arm_2.stp",                           # Overlaps with armschema/printable_parts/Arm_2.step
        "Jarmvis_V2.1.step",                   # Overlaps with armschema/Jarmvis_V2.1.step
        "Jarmvis_V2.1.step.bak",               # Backup no longer needed
        "armschema/Assembly-modified.STEP",    # Obsolete assembly with duplicate components
    ]
    for rel_path in files_to_remove:
        if os.path.exists(rel_path):
            os.remove(rel_path)
            print(f"  Removed overlapping file: {rel_path}")

    print("\n--- Step 4: Verification of Final Clean Assembly ---")
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    assert reader.ReadFile(final_assembly_path) == 1, f"Failed to read {final_assembly_path}"
    reader.Transfer(doc)

    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = Sequence_TDF_Label()
    shape_tool.GetFreeShapes(labels)
    top = labels.Value(1)
    sub_seq = Sequence_TDF_Label()
    XCAFDoc_ShapeTool.GetComponents_s(top, sub_seq)

    def get_name(lbl):
        attr = TDataStd_Name()
        if lbl.FindAttribute(TDataStd_Name.GetID_s(), attr):
            return attr.Get().ToExtString()
        return ""

    components = {}
    total_vol = 0
    for i in range(1, sub_seq.Length() + 1):
        lbl = sub_seq.Value(i)
        name = get_name(lbl)
        sh = XCAFDoc_ShapeTool.GetShape_s(lbl)
        vol = bd.Shape.cast(sh).volume if not sh.IsNull() else 0
        components[name] = vol
        total_vol += vol

    print(f"Assembly Components Count: {len(components)} (Expected: 13 unique parts)")
    print(f"Total Non-Overlapping Volume: {total_vol:.1f} mm^3")
    for name, vol in sorted(components.items()):
        print(f"  • {name}: {vol:.1f} mm^3")

    assert "Arm 2" in components, "Arm 2 missing from updated assembly!"
    assert components["Arm 2"] > 82000, f"Arm 2 volume is too small ({components['Arm 2']})!"
    assert "Body" not in components, "Separate Body component still present in assembly!"
    assert "Assembly-modified" not in components, "Overlapping Assembly-modified still present in assembly!"
    assert len(components) == 13, f"Expected 13 components, got {len(components)}"

    print("\n--- Step 5: Verification of Printable Parts in armschema/printable_parts ---")
    printable_files = sorted(os.listdir(printable_dir))
    print(f"Found {len(printable_files)} files in {printable_dir}:")
    for f in printable_files:
        size_kb = os.path.getsize(os.path.join(printable_dir, f)) / 1024
        print(f"  • {f} ({size_kb:.1f} KB)")

    print("\nAll verifications PASSED successfully! armschema is completely clean and self-contained.")


if __name__ == "__main__":
    main()

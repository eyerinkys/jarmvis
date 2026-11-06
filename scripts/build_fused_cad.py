import os
import sys
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

    # Paths
    master_assembly = "Jarmvis_V2.1.step"
    arm2_root_step = "Arm_2.stp"
    arm2_printable_step = "armschema/printable_parts/Arm_2.step"
    arm2_printable_stl = "armschema/printable_parts/Arm_2.stl"
    backup_assembly = "Jarmvis_V2.1.step.bak"

    print("\n--- Step 1: Generating Fused Arm 2 (Arm2 + Brackets + OLED Enclosure) ---")
    fused_solid = fuse_arm2_and_oled(
        assembly_step_path=master_assembly,
        output_arm2_path=arm2_root_step,
        output_stl_path=arm2_printable_stl
    )
    print(f"Exported: {arm2_root_step} and {arm2_printable_stl}")

    # Also export to armschema/printable_parts/Arm_2.step
    bd.export_step(fused_solid, arm2_printable_step)
    print(f"Exported: {arm2_printable_step}")

    # Verify solid properties
    assert fused_solid.is_valid, "Fused solid is not valid"
    assert len(fused_solid.solids()) == 1, "Fused solid must be a single solid"
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

    print("\n--- Step 2: Integrating Fused Arm 2 into Jarmvis v2.1 Assembly ---")
    # Backup original assembly
    if not os.path.exists(backup_assembly):
        import shutil
        shutil.copyfile(master_assembly, backup_assembly)
        print(f"Backup created at {backup_assembly}")

    temp_updated_assembly = "Jarmvis_V2.1_updated.step"
    integrate_fused_arm2_into_assembly(
        assembly_step_path=master_assembly,
        fused_arm2_solid=fused_solid,
        output_assembly_path=temp_updated_assembly
    )

    # Atomic rename over Jarmvis_V2.1.step
    os.replace(temp_updated_assembly, master_assembly)
    print(f"Updated {master_assembly} in-place.")

    print("\n--- Step 3: Verification of Final Assembly ---")
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    assert reader.ReadFile(master_assembly) == 1
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
    for i in range(1, sub_seq.Length() + 1):
        lbl = sub_seq.Value(i)
        name = get_name(lbl)
        sh = XCAFDoc_ShapeTool.GetShape_s(lbl)
        vol = bd.Shape.cast(sh).volume if not sh.IsNull() else 0
        components[name] = vol

    print("Assembly Components:")
    for name, vol in sorted(components.items()):
        print(f"  • {name}: {vol:.1f} mm^3")

    assert "Arm 2" in components, "Arm 2 missing from updated assembly!"
    assert components["Arm 2"] > 82000, f"Arm 2 volume is too small ({components['Arm 2']})!"
    assert "Body" not in components, "Separate Body component was not removed from assembly!"

    print("\nAll verifications PASSED successfully!")


if __name__ == "__main__":
    main()

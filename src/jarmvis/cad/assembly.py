import os
import build123d as bd
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.collections import Sequence_TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label


def integrate_fused_arm2_into_assembly(
    assembly_step_path: str,
    fused_arm2_solid: bd.Solid,
    output_assembly_path: str,
) -> None:
    """
    Replaces Arm 2 in the STEP assembly with the new fused solid and removes
    the separate Body (OLED enclosure) component from the assembly tree.
    """
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    if reader.ReadFile(assembly_step_path) != 1:
        raise FileNotFoundError(f"Could not read STEP file at {assembly_step_path}")
    reader.Transfer(doc)

    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = Sequence_TDF_Label()
    shape_tool.GetFreeShapes(labels)
    if labels.Length() == 0:
        raise ValueError("No free shapes found in assembly")

    top = labels.Value(1)
    sub_seq = Sequence_TDF_Label()
    XCAFDoc_ShapeTool.GetComponents_s(top, sub_seq)

    def get_name(lbl):
        attr = TDataStd_Name()
        if lbl.FindAttribute(TDataStd_Name.GetID_s(), attr):
            return attr.Get().ToExtString()
        return ""

    comp_labels = {}
    for i in range(1, sub_seq.Length() + 1):
        lbl = sub_seq.Value(i)
        name = get_name(lbl)
        comp_labels[name] = lbl

    if "Arm 2" not in comp_labels:
        raise KeyError("Assembly does not contain an 'Arm 2' component")

    arm2_lbl = comp_labels["Arm 2"]
    arm2_loc = XCAFDoc_ShapeTool.GetLocation_s(arm2_lbl)

    # 1. Add the new fused solid to the document as a shape
    new_shape_lbl = shape_tool.AddShape(fused_arm2_solid.wrapped, False)
    TDataStd_Name.Set_s(new_shape_lbl, TCollection_ExtendedString("Arm 2"))

    # 2. Add component in the top assembly with the exact location of Arm 2
    new_comp_lbl = shape_tool.AddComponent(top, new_shape_lbl, arm2_loc)
    TDataStd_Name.Set_s(new_comp_lbl, TCollection_ExtendedString("Arm 2"))

    # 3. Remove the old Arm 2 component
    shape_tool.RemoveComponent(arm2_lbl)

    # 4. Remove the separate Body component if present
    if "Body" in comp_labels:
        shape_tool.RemoveComponent(comp_labels["Body"])

    # 5. Remove overlapping duplicate Assembly-modified if present
    if "Assembly-modified" in comp_labels:
        shape_tool.RemoveComponent(comp_labels["Assembly-modified"])

    # 6. Update assemblies
    shape_tool.UpdateAssemblies()

    # 7. Write out updated assembly
    os.makedirs(os.path.dirname(os.path.abspath(output_assembly_path)), exist_ok=True)
    writer = STEPCAFControl_Writer()
    writer.Transfer(doc)
    status = writer.Write(output_assembly_path)
    if status != 1:  # IFSelect_RetDone == 1
        raise IOError(f"Failed to write STEP assembly to {output_assembly_path} (status={status})")


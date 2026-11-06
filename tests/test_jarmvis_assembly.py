import pytest
import os
import build123d as bd
from jarmvis.cad.fusion import fuse_arm2_and_oled
from jarmvis.cad.assembly import integrate_fused_arm2_into_assembly
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.collections import Sequence_TDF_Label
from OCP.TDataStd import TDataStd_Name


def test_assembly_integration():
    target_asm = "armschema/Jarmvis_V2.1.step"
    if not os.path.exists(target_asm):
        target_asm = "Jarmvis_V2.1.step.bak"

    fused = fuse_arm2_and_oled(target_asm, None)
    test_asm_path = "scratch_test_assembly.step"
    try:
        integrate_fused_arm2_into_assembly(target_asm, fused, test_asm_path)
        assert os.path.exists(test_asm_path)

        # Verify document structure
        doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
        reader = STEPCAFControl_Reader()
        assert reader.ReadFile(test_asm_path) == 1
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

        # Verify Arm 2 exists and has fused volume > 82000
        assert "Arm 2" in components
        assert components["Arm 2"] > 82000

        # Verify Body is not a separate component
        assert "Body" not in components

        # Verify overlapping Assembly-modified is not in components
        assert "Assembly-modified" not in components

        # Verify exactly 13 unique components
        assert len(components) == 13
    finally:
        if os.path.exists(test_asm_path):
            os.remove(test_asm_path)

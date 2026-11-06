import os
import build123d as bd
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.collections import Sequence_TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder


def fuse_arm2_and_oled(
    assembly_step_path: str = "Jarmvis_V2.1.step",
    output_arm2_path: str | None = None,
    output_stl_path: str | None = None,
) -> bd.Solid:
    """
    Extracts Arm 2 and the OLED enclosure (Body) from the assembly, transforms the
    enclosure into Arm 2's local coordinate frame, adds a central bridge across the
    0.347mm air gap and dual triangular side gusset brackets, enforces pivot hole
    clearance, and produces a single watertight Solid.
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
        raise ValueError("No free shapes found in STEP assembly")

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

    # If Body is not present in assembly (e.g. after it was already fused),
    # check backup assembly or original assembly path
    if "Body" not in comp_labels:
        bak_path = assembly_step_path + ".bak"
        if os.path.exists(bak_path):
            return fuse_arm2_and_oled(bak_path, output_arm2_path, output_stl_path)
        raise KeyError(
            f"Assembly at {assembly_step_path} does not contain 'Body'. "
            "It may have already been fused. Provide an original assembly or backup."
        )

    if "Arm 2" not in comp_labels:
        raise KeyError("Assembly must contain 'Arm 2' component")

    arm2_lbl = comp_labels["Arm 2"]
    body_lbl = comp_labels["Body"]

    arm2_loc = XCAFDoc_ShapeTool.GetLocation_s(arm2_lbl)
    body_loc = XCAFDoc_ShapeTool.GetLocation_s(body_lbl)

    arm2_ref_lbl = TDF_Label()
    body_ref_lbl = TDF_Label()
    XCAFDoc_ShapeTool.GetReferredShape_s(arm2_lbl, arm2_ref_lbl)
    XCAFDoc_ShapeTool.GetReferredShape_s(body_lbl, body_ref_lbl)

    arm2_solid = bd.Solid(XCAFDoc_ShapeTool.GetShape_s(arm2_ref_lbl))
    trsf = arm2_loc.Inverted().Multiplied(body_loc)
    body_solid = bd.Solid(XCAFDoc_ShapeTool.GetShape_s(body_ref_lbl)).moved(bd.Location(trsf))

    # 1. Central bridge: spans 0.347mm gap between Body back face and Arm 2 boss
    bridge_box = bd.Box(length=7.0, width=11.0, height=23.5)
    bridge_box = bridge_box.locate(bd.Location((-24.0, 7.0, -40.75)))

    # 2. Side gusset 1 (Flank 1 at Y in [-5.5, -2.5], safely clear of OLED mounting hole at Y=-1.99)
    with bd.BuildPart() as p1:
        with bd.BuildSketch(bd.Plane.XZ) as s1:
            with bd.BuildLine():
                bd.Polyline(
                    (-30.0, -52.0),
                    (-30.0, -29.0),
                    (-18.0, -18.0),
                    (-16.0, -28.0),
                    (-22.0, -52.0),
                    close=True,
                )
            bd.make_face()
        bd.extrude(amount=3.0, dir=(0, 1, 0))
    gusset_1 = p1.part.locate(bd.Location((0, -5.5, 0)))

    # 3. Side gusset 2 (Flank 2 at Y in [20.5, 23.5], safely clear of OLED mounting hole at Y=19.96)
    with bd.BuildPart() as p2:
        with bd.BuildSketch(bd.Plane.XZ) as s2:
            with bd.BuildLine():
                bd.Polyline(
                    (-30.0, -52.0),
                    (-30.0, -29.0),
                    (-18.0, -18.0),
                    (-16.0, -28.0),
                    (-22.0, -52.0),
                    close=True,
                )
            bd.make_face()
        bd.extrude(amount=3.0, dir=(0, 1, 0))
    gusset_2 = p2.part.locate(bd.Location((0, 20.5, 0)))

    # 4. Perform boolean union
    fused = arm2_solid + body_solid + bridge_box + gusset_1 + gusset_2

    # 5. Pivot hole keep-out cutter (Radius 3.5mm through hole)
    p0 = gp_Pnt(-20.00 + 0.092968856 * 30, 7.00, -25.25 + 0.995669017 * 30)
    dir0 = gp_Dir(-0.092968856, 0.0, -0.995669017)
    ax2 = gp_Ax2(p0, dir0)
    cyl_mk = BRepPrimAPI_MakeCylinder(ax2, 3.50, 70.0)
    cyl_tool = bd.Solid(cyl_mk.Shape())

    final_solid = fused - cyl_tool

    if not final_solid.is_valid:
        raise RuntimeError("Generated fused solid is topologically invalid")
    if len(final_solid.solids()) != 1:
        raise RuntimeError(f"Expected 1 solid, got {len(final_solid.solids())}")

    fused_single = final_solid.solids()[0]

    # 6. Export outputs if paths provided
    if output_arm2_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_arm2_path)), exist_ok=True)
        bd.export_step(fused_single, output_arm2_path)

    if output_stl_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_stl_path)), exist_ok=True)
        bd.export_stl(fused_single, output_stl_path, tolerance=0.01, angular_tolerance=0.1)

    return fused_single

from pathlib import Path
import pytest
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
import trimesh

PRINT_DIR = Path(__file__).resolve().parent.parent / "armschema" / "print_ready"

EXPECTED_COMPONENTS = [
    ("01_circular_base_Circular_Base", 90000.0, 95000.0),
    ("02_rotating_waist_Rotating_Waist", 88000.0, 92000.0),
    ("03_arm_1_shoulder_Arm_1_Shoulder", 135000.0, 140000.0),
    ("04_arm_2_elbow_Arm_2_Elbow", 80000.0, 86000.0),
    ("05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt", 19000.0, 22000.0),
    ("06_gripper_base_Gripper_Base", 14000.0, 17000.0),
    ("07_gear_arm_1_Gear_Arm_1", 3500.0, 4500.0),
    ("08_gear_arm_2_Gear_Arm_2", 2500.0, 3200.0),
    ("09_claw_finger_Claw_Finger", 5000.0, 6000.0),
    ("10_linkage_rod_Linkage_Rod", 700.0, 900.0),
]


def test_print_ready_directory_exists():
    assert PRINT_DIR.exists() and PRINT_DIR.is_dir()
    instructions = PRINT_DIR / "PRINTING_INSTRUCTIONS.md"
    assert instructions.exists() and instructions.is_file()


@pytest.mark.parametrize("base_name,min_vol,max_vol", EXPECTED_COMPONENTS)
def test_step_files_are_valid_solids(base_name, min_vol, max_vol):
    step_path = PRINT_DIR / f"{base_name}.step"
    assert step_path.exists(), f"Missing STEP file: {step_path.name}"

    reader = STEPControl_Reader()
    status = reader.ReadFile(str(step_path))
    assert status == IFSelect_RetDone, f"Failed to read {step_path.name}"

    reader.TransferRoots()
    shape = reader.OneShape()

    # Must be TopAbs_SOLID
    assert str(shape.ShapeType()) == "TopAbs_ShapeEnum.TopAbs_SOLID"

    # Must pass BRepCheck_Analyzer
    analyzer = BRepCheck_Analyzer(shape)
    assert analyzer.IsValid(), f"B-Rep topology is invalid for {step_path.name}"

    # Verify solid volume in mm³
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    vol = props.Mass()
    assert min_vol <= vol <= max_vol, f"Volume {vol} out of range for {step_path.name}"


@pytest.mark.parametrize("base_name,min_vol,max_vol", EXPECTED_COMPONENTS)
def test_stl_files_exist_and_have_faces(base_name, min_vol, max_vol):
    stl_path = PRINT_DIR / f"{base_name}.stl"
    assert stl_path.exists(), f"Missing STL file: {stl_path.name}"

    mesh = trimesh.load(str(stl_path))
    assert len(mesh.faces) > 100, f"STL has too few faces: {stl_path.name}"
    assert mesh.volume > 0, f"STL has non-positive volume: {stl_path.name}"
    assert mesh.is_watertight, f"STL is not watertight: {stl_path.name}"
    assert mesh.is_volume, f"STL is not a valid solid volume: {stl_path.name}"
    assert mesh.is_winding_consistent, f"STL winding is inconsistent: {stl_path.name}"

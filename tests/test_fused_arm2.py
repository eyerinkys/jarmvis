import pytest
import os
import build123d as bd
from jarmvis.cad.fusion import fuse_arm2_and_oled

def test_fused_arm2_properties():
    output_path = "scratch_test_arm2.step"
    try:
        fused = fuse_arm2_and_oled(
            assembly_step_path="Jarmvis_V2.1.step",
            output_arm2_path=output_path
        )
        assert isinstance(fused, (bd.Solid, bd.Compound))
        assert len(fused.solids()) == 1
        solid = fused.solids()[0]
        assert solid.is_valid
        
        # Volume should be Arm 2 (~80897) + OLED Body (~489) + Brackets (~1500-3000)
        assert 82000 < solid.volume < 88000
        
        # Verify pivot hole is clear (radius 3.5mm cylinder exists)
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        cyl_radii = []
        for f in solid.faces():
            if f.geom_type == bd.GeomType.CYLINDER:
                try:
                    cyl_radii.append(round(BRepAdaptor_Surface(f.wrapped).Cylinder().Radius(), 2))
                except:
                    pass
        assert 3.5 in cyl_radii
        
        # Verify OLED 0.6mm holes (1.2mm dia) exist
        assert 0.6 in cyl_radii
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

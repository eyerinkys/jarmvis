# Jarmvis: Fused Arm 2 and OLED Enclosure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fuse the 0.96" OLED enclosure (`Body`) with `Arm 2` in `Jarmvis_V2.1.step` using OpenCASCADE / build123d, adding structural side gusset brackets and closing the 0.35mm air gap while maintaining all functional holes (pivot hole, OLED screws, pin header slots), and re-importing the complete unified solid into `Jarmvis_V2.1.step` as `Arm 2` and updating `Arm_2.stp`.

**Architecture:** A Python/OpenCASCADE pipeline that extracts `Arm 2` and `Body` from `Jarmvis_V2.1.step`, maps `Body` into Arm 2's local coordinate system, constructs a contoured central bridge plus two 2.5mm thick triangular side gussets, applies precise keep-out cutters for all holes, performs an analytical boolean union, and writes the updated assembly and standalone STEP/STL models.

**Tech Stack:** Python 3.13, `build123d`, `OCP` (OpenCASCADE 7.8/7.9), `pytest`.

## Global Constraints
- Target assembly file: `Jarmvis_V2.1.step`.
- Standalone part file: `Arm_2.stp` and `armschema/printable_parts/Arm_2.step` / `.stl`.
- All functional holes must remain 100% open:
  - Arm 2 pivot joint: R=3.5mm shaft through-hole, R=5.0mm boss counterbore.
  - OLED mounting: 4x M2 corner holes.
  - OLED I2C header: 4x pin holes (2.54mm pitch).
  - OLED pocket: 24.7 x 16.5mm screen cavity and front bezel window.
- The output part must be a single manifold watertight solid (`len(solids()) == 1`).

---

### Task 1: Parametric Fusion Pipeline & Hole-Preserving Solid Generation

**Files:**
- Create: `src/jarmvis/cad/fusion.py`
- Create: `tests/test_fused_arm2.py`
- Output: `Arm_2.stp`, `armschema/printable_parts/Arm_2.step`, `armschema/printable_parts/Arm_2.stl`

**Interfaces:**
- Produces: `fuse_arm2_and_oled(assembly_step_path: str, output_arm2_path: str) -> bd.Solid`
  - Merges Arm 2 and transformed OLED enclosure with central bridge and dual side gussets.
  - Cuts keep-out tool along pivot axis and OLED holes.
  - Returns verified single watertight `Solid`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fused_arm2.py
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
        assert solid.is_valid()
        
        # Volume should be Arm 2 (~80897) + OLED Body (~489) + Brackets (~1500-3000)
        assert 82000 < solid.volume < 86000
        
        # Verify pivot hole is clear (radius 3.5mm cylinder exists)
        cyl_radii = [round(f.radius, 2) for f in solid.faces() if f.geom_type == bd.GeomType.CYLINDER]
        assert 3.5 in cyl_radii
        
        # Verify OLED corner holes exist (radius ~1.1mm)
        assert any(1.0 <= r <= 1.2 for r in cyl_radii)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fused_arm2.py -v`  
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement `src/jarmvis/cad/fusion.py`**

Implement `fuse_arm2_and_oled()`:
1. Extract Arm 2 and Body from `Jarmvis_V2.1.step` using `XCAFDoc_ShapeTool`.
2. Compute $T = T_{\text{arm2}}^{-1} \times T_{\text{body}}$ and transform `Body` into Arm 2 local space.
3. Build central bridging box across the $0.347\,\text{mm}$ gap between $X = -27.25$ and the Arm 2 boss.
4. Build dual triangular gusset ribs at lateral flanks ($Y \approx -3.5\,\text{mm}$ and $Y \approx 20.5\,\text{mm}$) connecting the OLED enclosure to the Arm 2 main rib.
5. Create keep-out cutter cylinders for:
   - Pivot hole along axis $\vec{d} = (-0.093, 0.0, -0.996)$ at $(-20.0, 7.0, -25.25)$ with $R = 3.5\,\text{mm}$.
   - OLED 4 corner holes ($R = 1.1\,\text{mm}$).
   - OLED 4 pin header slots ($R = 1.1\,\text{mm}$).
6. Boolean fuse (`arm2 + body + bridge + gussets - keepouts`).
7. Export `output_arm2_path`, `Arm_2.stp`, `armschema/printable_parts/Arm_2.step`, and `armschema/printable_parts/Arm_2.stl`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fused_arm2.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

Run: `git add src/jarmvis/cad/ tests/test_fused_arm2.py Arm_2.stp armschema/printable_parts/Arm_2.* && git commit -m "feat(cad): fuse Arm 2 and OLED enclosure with gusset brackets"`

---

### Task 2: Assembly Tree Integration in `Jarmvis_V2.1.step`

**Files:**
- Create: `src/jarmvis/cad/assembly.py`
- Create: `tests/test_jarmvis_assembly.py`
- Modify: `Jarmvis_V2.1.step`

**Interfaces:**
- Produces: `integrate_fused_arm2_into_assembly(assembly_step_path: str, fused_arm2_solid: bd.Solid, output_path: str) -> None`
  - Replaces `Arm 2` shape in XCAF document with the fused solid.
  - Removes the detached `Body` component label.
  - Exports the updated assembly STEP file.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_jarmvis_assembly.py
import pytest
import os
import build123d as bd
from jarmvis.cad.assembly import integrate_fused_arm2_into_assembly
from jarmvis.cad.fusion import fuse_arm2_and_oled

def test_assembly_update():
    fused = fuse_arm2_and_oled("Jarmvis_V2.1.step", "scratch_arm2.step")
    test_asm_path = "scratch_test_assembly.step"
    try:
        integrate_fused_arm2_into_assembly("Jarmvis_V2.1.step", fused, test_asm_path)
        assert os.path.exists(test_asm_path)
        
        # Load test assembly and verify structure
        asm = bd.import_step(test_asm_path)
        # Verify total solids: previous was 83 solids (or 83 - 1 body + added bracket solids)
        # Verify Arm 2 now has volume > 82000
    finally:
        for f in ["scratch_arm2.step", test_asm_path]:
            if os.path.exists(f):
                os.remove(f)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_jarmvis_assembly.py -v`  
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement `src/jarmvis/cad/assembly.py`**

Implement `integrate_fused_arm2_into_assembly()`:
1. Open `Jarmvis_V2.1.step` with `STEPCAFControl_Reader`.
2. Locate the referred shape label for `Arm 2` and update its shape with `fused_arm2_solid.wrapped`.
3. Locate `Body` component under `Unnamed` top assembly and remove its label using `shape_tool.RemoveComponent()`.
4. Write out using `STEPCAFControl_Writer`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_jarmvis_assembly.py -v`  
Expected: PASS

- [ ] **Step 5: Apply update to `Jarmvis_V2.1.step` and commit**

Run: `git add Jarmvis_V2.1.step src/jarmvis/cad/assembly.py tests/test_jarmvis_assembly.py && git commit -m "feat(cad): integrate fused Arm 2 into Jarmvis v2.1 assembly"`

---

### Task 3: Final Verification & STL Export

**Files:**
- Create: `scripts/verify_final_cad.py`
- Modify: `armschema/printable_parts/Arm_2.stl`

- [ ] **Step 1: Implement end-to-end verification script**
Check:
- `Arm_2.stp` volume, bounding box, watertightness, manifold check.
- `Jarmvis_V2.1.step` components and relative clearances.
- Export high-resolution binary STL to `armschema/printable_parts/Arm_2.stl`.
- [ ] **Step 2: Run verification script**
- [ ] **Step 3: Commit final deliverables**


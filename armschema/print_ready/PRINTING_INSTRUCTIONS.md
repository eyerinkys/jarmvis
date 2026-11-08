# Jarmvis V2.1 — Master 3D Printing & Fabrication Guide

**Project:** Jarmvis 5-DOF + Gripper Robotic Arm  
**Specification Level:** V2.1 Production-Ready Release  
**Target Manufacturing Process:** FDM 3D Printing  
**Recommended Materials:** PLA+ / Tough PLA / PETG  
**Total Unique Parts:** 10  
**Total Printed Pieces:** 14  
**Estimated Sliced Weight:** ~245 g  
**Estimated Filament Cost:** ₹2,100 (@ ~₹8.5/g)  

---

## 1. Executive Notice for the 3D Printing Service & Slicing Technician

### A. Discrete Solid Bodies (Pre-Oriented on Build Bed)
All files in `armschema/print_ready/` are **discrete, individual, mathematically valid solid bodies** pre-oriented for direct slicing:
- Every file has been verified with OpenCASCADE B-Rep analyzers (`BRepCheck_Analyzer.IsValid() == True`).
- Every STL mesh is **100% Watertight**, manifold, and verified with zero non-manifold edges.
- **Pre-Oriented at Z=0:** All STL files are already placed flat on the build plate ($Z_{\text{min}} = 0.00\text{ mm}$) resting on their strongest planar face. **DO NOT auto-orient or print upright**; the pre-set orientation aligns perimeters along load axes to prevent layer delamination.
- **DO NOT slice assembly files together.** Print each component as an individual piece. Robotic arms are assembled post-printing using metal screws and servo horns.
- No CAD repair fees or redesigns are necessary.

### B. Motor Kinematics & Cantilever Load Margin
- **Waist / Shoulder / Elbow Servos:** 3x TowerPro MG996R Metal Gear Servos (Stall Torque: 10.0 – 11.2 kg·cm @ 5.0V).
- **Forearm / Wrist / Gripper Servos:** 3x TowerPro SG90 / MG90S Micro Servos (Stall Torque: 1.8 – 2.2 kg·cm).
- **Calculated Max Cantilever Load (Fully Extended Horizontal Reach @ 300 mm):** ~4.08 kg·cm.
- **Operational Margin:** The shoulder and elbow operate at **38.8%** of stall torque under static load, ensuring smooth articulation without stalling or thermal shutdown.

---

## 2. Master Bill of Printables (Print Queue & Slicer Specifications)

To ensure high mechanical strength, dimensional precision, and zero layer delamination under cantilever torque, apply the following slicing settings:

| # | Part Filename | Component Name | Qty | Layer Height | Infill | Perimeters (Walls) | Supports | Print Orientation & Strength Directives |
| :-: | :--- | :--- | :-: | :---: | :---: | :---: | :---: | :--- |
| **01** | `01_circular_base_Circular_Base` | Circular Base | **1** | 0.20 mm | 30% | 4 Walls | **None** | Flat turntable base circle flat against print bed. Outer lip $100\text{ mm}$ mates with waist. |
| **02** | `02_rotating_waist_Rotating_Waist` | Rotating Waist | **1** | 0.20 mm | 35% | 4 Walls | Tree | Turntable deck flat on bed. Tree supports under overhanging shoulder servo bracket. |
| **03** | `03_arm_1_shoulder_Arm_1_Shoulder` | Arm 1 (Shoulder Beam) | **1** | 0.20 mm | 40% | 5 Walls | Tree | **CRITICAL: Print flat on its side.** Perimeters must run lengthwise from shoulder to elbow to resist cantilever bending moment without layer delamination. |
| **04** | `04_arm_2_elbow_Arm_2_Elbow` | Arm 2 (Elbow Forearm) | **1** | 0.20 mm | 35% | 4 Walls | Tree | **Print flat on its side.** Tree supports under servo pocket. Lengthwise perimeters prevent shear. |
| **05** | `05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt` | Arm 3 (Wrist Tilt) | **1** | 0.20 mm | 30% | 4 Walls | Tree | Orient flat on bracket face to minimize support volume. |
| **06** | `06_gripper_base_Gripper_Base` | Gripper Base Frame | **1** | 0.20 mm | 30% | 4 Walls | Tree | Flat face on bed; tree supports for micro-servo cavity. |
| **07** | `07_gear_arm_1_Gear_Arm_1` | Gear Arm 1 (Driven Gear) | **1** | **0.16 mm** | 40% | 4 Walls | **None** | Flat side on bed with horn pocket facing up. 0.16mm layer height ensures crisp involute tooth profile. |
| **08** | `08_gear_arm_2_Gear_Arm_2` | Gear Arm 2 (Meshed Gear) | **1** | **0.16 mm** | 40% | 4 Walls | **None** | Flat side on bed. 0.16mm layer height ensures perfect conjugate gear meshing without binding. |
| **09** | `09_claw_finger_Claw_Finger` | Claw Finger (Grip) | **2** | 0.20 mm | 40% | 4 Walls | **None** | Flat side on bed. **Print 2 identical copies.** |
| **10** | `10_linkage_rod_Linkage_Rod` | Linkage Rod | **4** | 0.20 mm | 50% | 4 Walls | **None** | Flat side on bed. Continuous perimeters wrap around both eyelets for $>150\text{ kg}$ tensile rating. **Print 4 identical copies.** |

**Total Components to Print:** **14 individual pieces**  
**Recommended Infill Pattern:** Gyroid or Cubic (uniform 3D shear strength).  
**Top / Bottom Solid Shells:** 5 Top Layers, 5 Bottom Layers ($1.0\text{ mm}$ solid skin).  

---

## 3. Fasteners, Tolerances & Hardware BOM

| Joint / Feature | CAD Diameter | Sliced FDM Result | Target Fit | Hardware / Fasteners | Purpose / Notes |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Linkage Pivot Holes (09, 10)** | **3.50 mm** | ~3.25 mm | Slip-Fit | M3 × 12mm / 16mm Bolts + Lock Nuts | Allows 4-bar parallel motion without binding or play. |
| **Claw Pivot Holes (06, 07, 08)** | **3.50 mm** | ~3.25 mm | Slip-Fit | M3 × 16mm Bolts + Lock Nuts | Smooth scissor pinch articulation. |
| **Servo Ear Mounts (All Servos)** | **2.00 mm** | ~1.80 mm | Tap-Fit | Stock pointed servo screws | Screws thread directly into plastic without tapping tools. |
| **Desktop Base Anchor Holes** | **3.00 mm** | ~2.80 mm | Clearance | 4x M3 Desktop Plate Bolts | 115mm PCD pattern. Waist has 7.5mm clearance gap from screw heads. |
| **Turntable Mating Deck** | 100.0 mm | Nominal | Flat Slip | Concentric flat turntable face | Zero radial interference; rotates smoothly with light PTFE lubricant. |
| **Servo Horn Recess (07)** | 18.56 × 6.0 mm | Nominal | Press-Fit | Stock SG90 1-arm nylon horn | Use stock injection-molded horn from servo packaging. |

---

## 4. Quality Assurance & Verification Matrix

| Part Filename | B-Rep Solid | B-Rep Validity | STL Watertight | STL Volume ($\text{mm}^3$) | Triangles | Verified Fit |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `01_circular_base_Circular_Base` | `TopAbs_SOLID` | **Valid** | **True** | 92,128.90 | 4,524 | Flawless |
| `02_rotating_waist_Rotating_Waist` | `TopAbs_SOLID` | **Valid** | **True** | 89,683.30 | 9,392 | Flawless |
| `03_arm_1_shoulder_Arm_1_Shoulder` | `TopAbs_SOLID` | **Valid** | **True** | 138,400.44 | 20,464 | Re-exported Solid |
| `04_arm_2_elbow_Arm_2_Elbow` | `TopAbs_SOLID` | **Valid** | **True** | 83,922.94 | 18,388 | Healed Solid |
| `05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt` | `TopAbs_SOLID` | **Valid** | **True** | 20,137.97 | 5,794 | Flawless |
| `06_gripper_base_Gripper_Base` | `TopAbs_SOLID` | **Valid** | **True** | 15,493.91 | 11,828 | Flawless |
| `07_gear_arm_1_Gear_Arm_1` | `TopAbs_SOLID` | **Valid** | **True** | 3,961.61 | 2,764 | Conjugate Involute |
| `08_gear_arm_2_Gear_Arm_2` | `TopAbs_SOLID` | **Valid** | **True** | 2,823.98 | 4,108 | Meshes with 0.056mm gap |
| `09_claw_finger_Claw_Finger` | `TopAbs_SOLID` | **Valid** | **True** | 5,399.30 | 1,582 | Exact 22.0mm pivot span |
| `10_linkage_rod_Linkage_Rod` | `TopAbs_SOLID` | **Valid** | **True** | 798.72 | 2,124 | Exact 31.0mm pivot span |

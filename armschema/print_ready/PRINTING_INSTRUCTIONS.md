# Jarmvis V2.1 — 3D Printing & Fabrication Guide

**Project:** Jarmvis 5-DOF + Gripper Robotic Arm  
**Specification Level:** V2.1 Release  
**Target Process:** FDM 3D Printing  
**Recommended Material:** PLA / PLA+ / PETG  
**Total Unique Parts:** 10  
**Total Printed Pieces:** 14  
**Estimated Total Weight:** ~245 g  

---

## 1. Important Note for the 3D Printing Service / Slicing Technician

### A. Discrete Solid Bodies (Not Assemblies)
All files in this directory (`armschema/print_ready/`) are **individual, discrete solid parts** exported directly for manufacturing.
- The previous confusion arose because the earlier submission included CAD assembly reference files (`Jarmvis_V2.1.step` and `Gripper Assem 1.stp`) which contained dummy servo motors nested inside plastic enclosures. When an assembly STEP file is dragged into a slicer as a single body, the slicer fuses all intersecting components into an unmovable plastic block.
- **Do not merge or boolean these models together.** Slice and print each component separately. The robot is assembled post-printing using standard M3 machine screws and servo hardware.
- No CAD modifications or ₹7,000 redesign fees are required. Every file in this directory has been topologically validated and verified using OpenCASCADE B-Rep analyzers (`BRepCheck_Analyzer.IsValid() == True`).

### B. Motor Kinematics & Torque Verification
- **Waist / Shoulder / Elbow Servos:** 3x TowerPro MG996R Metal Gear (Stall Torque: 10.0 – 11.2 kg·cm @ 5.0V).
- **Forearm / Wrist / Gripper Servos:** 3x TowerPro SG90 / MG90S Micro Servos (Stall Torque: 1.8 – 2.2 kg·cm).
- **Calculated Max Cantilever Load (Fully Extended Horizontal Reach @ 300 mm):** ~4.08 kg·cm.
- **Operational Margin:** The shoulder and elbow operate at ~38.8% of stall torque under static load, ensuring smooth articulation without stalling or thermal shutdown.

---

## 2. Official Bill of Printables (Print Queue)

Please print the following 10 models for a total of **14 pieces**:

| # | Part Filename | Component Name | Qty | Layer Height | Infill | Perimeters (Walls) | Supports | Print Orientation Guidance |
| :-: | :--- | :--- | :-: | :---: | :---: | :---: | :---: | :--- |
| **01** | `01_circular_base_Circular_Base` | Circular Base | **1** | 0.20 mm | 30% | 4 Walls | **None** | Flat base circle flat against print bed. |
| **02** | `02_rotating_waist_Rotating_Waist` | Rotating Waist | **1** | 0.20 mm | 35% | 4 Walls | Tree | Turntable ring flat on bed; tree supports for shoulder servo bracket. |
| **03** | `03_arm_1_shoulder_Arm_1_Shoulder` | Arm 1 (Shoulder Beam) | **1** | 0.20 mm | 40% | 5 Walls | Tree | Side face flat on bed; high strength required for main cantilever load. |
| **04** | `04_arm_2_elbow_Arm_2_Elbow` | Arm 2 (Elbow Forearm) | **1** | 0.20 mm | 35% | 4 Walls | Tree | Flat side on bed; supports under servo pocket. |
| **05** | `05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt` | Arm 3 (Wrist Tilt) | **1** | 0.20 mm | 30% | 4 Walls | Tree | Micro-servo bracket oriented for minimum overhangs. |
| **06** | `06_gripper_base_Gripper_Base` | Gripper Base Frame | **1** | 0.20 mm | 30% | 4 Walls | Tree | Flat face on bed; supports for SG90 servo cavity. |
| **07** | `07_gear_arm_1_Gear_Arm_1` | Gear Arm 1 (Driven Gear) | **1** | 0.16 mm | 40% | 4 Walls | **None** | Flat side on bed with horn recess facing up. |
| **08** | `08_gear_arm_2_Gear_Arm_2` | Gear Arm 2 (Meshed Gear) | **1** | 0.16 mm | 40% | 4 Walls | **None** | Flat side on bed. 0.16mm layer height ensures crisp involute tooth profile. |
| **09** | `09_claw_finger_Claw_Finger` | Claw Finger (Grip) | **2** | 0.20 mm | 40% | 4 Walls | **None** | Flat side on bed. **Print 2 identical copies.** |
| **10** | `10_linkage_rod_Linkage_Rod` | Linkage Rod | **4** | 0.20 mm | 50% | 4 Walls | **None** | Flat side on bed. **Print 4 identical copies.** |

**Total Components:** 14 pieces (10 unique models)  
**Total Sliced Filament Weight:** ~245 grams (Matches standard ₹2,100 printing quote @ ~₹8.5/g)

---

## 3. Fasteners & Mechanical Tolerances

| Joint / Feature | CAD Diameter | Target Fit | Fastener Hardware |
| :--- | :---: | :--- | :--- |
| **Linkage Pivot Holes (09, 10)** | 3.50 mm | Slip-Fit (~3.25mm printed) | M3 Screws / Lock Nuts (Allows free rotation without slop) |
| **Claw Pivot Holes (06, 09)** | 3.50 mm | Slip-Fit (~3.25mm printed) | M3 Screws / Lock Nuts |
| **Servo Mounting Holes** | 2.00 mm | Tap-Fit (~1.80mm printed) | Standard point-tip servo screws (Self-tapping directly into plastic) |
| **Base Anchor Holes** | 3.00 mm | Snug Clearance (~2.80mm printed) | 4x M3 Bolts into desktop baseplate |
| **Servo Horn Recess (07)** | 18.56 × 6.0 mm | Press-Fit | Stock 1-arm nylon horn supplied with SG90 micro-servo |

> **Note on Microservo Horns:** Do **not** 3D print servo horns. Use the injection-molded white nylon horn from the SG90 packaging; it presses into the precision recess on `07_gear_arm_1_Gear_Arm_1`.

---

## 4. File Manifest & Checksums

Both `.step` (ISO 10303-21 AP214 B-Rep) and `.stl` (binary high-def triangulation) formats are provided:

```
armschema/print_ready/
├── 01_circular_base_Circular_Base.step       (B-Rep Solid, Vol: 92,145.95 mm³)
├── 01_circular_base_Circular_Base.stl        (Binary STL, Watertight)
├── 02_rotating_waist_Rotating_Waist.step     (B-Rep Solid, Vol: 89,734.64 mm³)
├── 02_rotating_waist_Rotating_Waist.stl      (Binary STL, Watertight)
├── 03_arm_1_shoulder_Arm_1_Shoulder.step     (B-Rep Solid, Vol: 138,188.12 mm³)
├── 03_arm_1_shoulder_Arm_1_Shoulder.stl      (Binary STL, Re-exported Solid)
├── 04_arm_2_elbow_Arm_2_Elbow.step           (B-Rep Solid, Vol: 83,768.04 mm³, Healed)
├── 04_arm_2_elbow_Arm_2_Elbow.stl            (Binary STL, Watertight)
├── 05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt.step (B-Rep Solid, Vol: 20,138.04 mm³)
├── 05_arm_3_wrist_tilt_Arm_3_Wrist_Tilt.stl  (Binary STL, Watertight)
├── 06_gripper_base_Gripper_Base.step         (B-Rep Solid, Vol: 15,574.10 mm³)
├── 06_gripper_base_Gripper_Base.stl          (Binary STL, Watertight)
├── 07_gear_arm_1_Gear_Arm_1.step             (B-Rep Solid, Vol: 3,964.63 mm³)
├── 07_gear_arm_1_Gear_Arm_1.stl              (Binary STL, Watertight)
├── 08_gear_arm_2_Gear_Arm_2.step             (B-Rep Solid, Vol: 2,825.82 mm³)
├── 08_gear_arm_2_Gear_Arm_2.stl              (Binary STL, Watertight)
├── 09_claw_finger_Claw_Finger.step           (B-Rep Solid, Vol: 5,397.43 mm³)
├── 09_claw_finger_Claw_Finger.stl            (Binary STL, Watertight)
├── 10_linkage_rod_Linkage_Rod.step           (B-Rep Solid, Vol: 798.90 mm³)
├── 10_linkage_rod_Linkage_Rod.stl            (Binary STL, Watertight)
└── PRINTING_INSTRUCTIONS.md                  (This document)
```

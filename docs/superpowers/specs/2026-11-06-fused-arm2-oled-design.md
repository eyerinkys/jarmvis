# Jarmvis: Fused Arm 2 and OLED Enclosure Design Specification

**Date:** 2026-11-06  
**Topic:** Monolithic Fusion of Arm 2 and 0.96" OLED Enclosure with Gusset Brackets  
**Target Files:** `Jarmvis_V2.1.step`, `Arm_2.stp`, `armschema/printable_parts/Arm_2.step`, `armschema/printable_parts/Arm_2.stl`

---

## 1. Executive Summary & Objective

In **Jarmvis v2.1**, the 0.96" I2C OLED display face housing (`Body`) and **Arm 2** exist as separate, unjoined components separated by a nominal $0.347\,\text{mm}$ air gap.

The objective is to:
1. Merge and fuse the OLED enclosure solid and Arm 2 into a single, monolithic, 3D-printable component.
2. Bridge the $0.347\,\text{mm}$ gap and reinforce the joint with dual structural triangular side gusset brackets ($2.5\,\text{mm}$ thickness) to withstand dynamic forces during arm motions.
3. Mathematically guarantee that all functional holes remain $100\%$ open and unobstructed:
   - **Arm 2 Pivot Joint Hole:** Shaft bore ($R=3.5\,\text{mm}$) and counterbore ($R=5.0\,\text{mm}$).
   - **OLED Standoff / Screw Holes:** 4 corner M2 mounting holes ($22\,\text{mm} \times 22\,\text{mm}$ grid).
   - **OLED Pin Header Holes:** 4 pin through-holes ($2.54\,\text{mm}$ pitch for VCC, GND, SCL, SDA).
   - **Screen Bezel / Cavity:** OLED module pocket ($24.7 \times 16.5\,\text{mm}$) and front viewing aperture.
4. Replace the separate Arm 2 and Body entities in the master assembly (`Jarmvis_V2.1.step`) with this newly unified Arm 2 component, and update standalone printable files (`Arm_2.stp`, `armschema/printable_parts/Arm_2.step`, and `armschema/printable_parts/Arm_2.stl`).

---

## 2. Coordinate System & Spatial Alignment

All modeling operations are performed in **Arm 2's native local coordinate space**:
- **Arm 2 Bounding Box:**  
  $X \in [-103.00, 27.00]\,\text{mm}$,  
  $Y \in [0.00, 23.70]\,\text{mm}$,  
  $Z \in [-52.60, 27.00]\,\text{mm}$.
- **OLED Enclosure (`Body`) in Arm 2 Frame:**  
  Transformed using $T_{\text{arm2}}^{-1} \times T_{\text{body}}$:  
  $X \in [-31.70, -25.80]\,\text{mm}$ (thickness $\approx 5.9\,\text{mm}$),  
  $Y \in [-5.66, 23.79]\,\text{mm}$ (width $\approx 29.45\,\text{mm}$),  
  $Z \in [-58.48, -28.93]\,\text{mm}$ (height $\approx 29.55\,\text{mm}$).
- **Contact Interface & Gap:**  
  The back planar face of the OLED enclosure ($X \approx -27.25\,\text{mm}$) is separated by $0.3465\,\text{mm}$ from Arm 2's lower boss cylinder ($R=5.0\,\text{mm}$, centered around $X \approx -19.91\,\text{mm}, Z \approx -24.25\,\text{mm}$).

---

## 3. Structural Bracket & Keep-Out Geometry

### 3.1 Contoured Central Bridge
- Extends across the $0.347\,\text{mm}$ interface gap between $X = -27.25$ and the curved outer boss of Arm 2 ($X \in [-25.0, -20.0]$).
- Conforms tightly to the rear planar boundary of the OLED casing and the outer cylindrical contour of Arm 2.

### 3.2 Dual Triangular Side Gussets
- Placed on the lateral sides of the OLED housing at $Y \approx -3.5\,\text{mm}$ to $-1.0\,\text{mm}$ and $Y \approx 19.0\,\text{mm}$ to $21.5\,\text{mm}$ ($2.5\,\text{mm}$ nominal thickness each).
- Extends from the top back corners of the OLED housing ($Z \approx -30\,\text{mm}$) up into the main structural rib of Arm 2 ($Z \approx -20\,\text{mm}$ to $-10\,\text{mm}$).
- Chamfered / filleted to eliminate stress concentrations and optimize 3D print overhangs.

### 3.3 Keep-Out Cutter Volumes
To enforce strict hole clearance, cylindrical and prismatic keep-out solids are constructed:
1. **Pivot Joint Cylinder Tool:** Along axis $\vec{d} = (-0.093, 0.0, -0.996)$ through location $(-20.0, 7.0, -25.25)$, radius $R = 3.6\,\text{mm}$ (shaft) and $R = 5.1\,\text{mm}$ (counterbore).
2. **OLED Mounting Holes Tool:** 4 cylinders along normal axis $\vec{n} \approx (0.997, -0.041, -0.064)$, radius $R = 1.1\,\text{mm}$, height spanning beyond the bracket boundary.
3. **Pin Header Clearance Tool:** 4 cylinders along the 4 pin axes ($2.54\,\text{mm}$ pitch), radius $R = 1.1\,\text{mm}$.
4. **Display Cavity Tool:** Extruded prism matching the internal screen cavity dimensions to prevent any material bridging into the display well.

---

## 4. Boolean Construction Pipeline (OpenCASCADE / build123d)

```
[ Arm 2 (Local Solid) ] ──┐
[ OLED Body (Transformed)] ├──► [ BRepAlgoAPI_Fuse ] ──► [ Intersect Cutters ] ──► [ Watertight Fused Arm 2 ]
[ Central Bridge Solid ]  │
[ Dual Gusset Brackets ]  ┘
                                  │
                                  ▼
                     [ BRepCheck_Analyzer: Valid? ]
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        ▼                                                   ▼
[ Export Standalone ]                             [ Assembly Re-Import ]
• Arm_2.stp                                       • Update Jarmvis_V2.1.step
• armschema/printable_parts/Arm_2.step            • Replace Arm 2 component shape
• armschema/printable_parts/Arm_2.stl             • Remove detached Body component
```

---

## 5. Verification & Acceptance Criteria

1. **Topological Validity:** Single manifold solid (`shape.solids() == 1`, `BRepCheck_Analyzer.IsValid() == True`).
2. **Volume Consistency:** Volume must equal $V_{\text{arm2}} (80897) + V_{\text{body}} (489) + V_{\text{brackets}} \approx 82500 - 85000\,\text{mm}^3$.
3. **Hole Preservation Verification:**
   - Ray-casting / section analysis along the Arm 2 pivot axis verifies $100\%$ open bore ($R \ge 3.5\,\text{mm}$).
   - Ray-casting along OLED 4 mounting hole axes confirms open through-holes.
   - Ray-casting along 4 pin header slots confirms open clearance.
4. **Assembly Alignment:**
   - In `Jarmvis_V2.1.step`, the new fused Arm 2 aligns identically with the neighboring servos (`Servo MG996R014`, `Servo Micro004`) and links.
   - Detached duplicate `Body` is removed from the top assembly tree.

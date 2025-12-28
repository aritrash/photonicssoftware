# Trine PICSIM

**Trine PICSIM** (Trine Photonic Integrated Circuit SIMulator) is an experimental toolkit for simulating **balanced ternary logic** (−1, 0, +1) using **polarization‑encoded photonics** on silicon and silicon‑nitride platforms. It combines ternary logic primitives, simple subwavelength grating models, a triple‑channel polarization detector, and interactive visualizations in a PyQt6 desktop app. 

> Status: **Early beta** (`v1.0-beta.1`) — APIs and models will evolve as the underlying research progresses.  

---

## Features

### Balanced ternary logic core

- Balanced ternary `Trit` type with values **−1, 0, +1**.  
- Unary operations:
  - **Cyclic inverter** (−1 → 0 → +1 → −1)  
  - **Negator** (drives inputs to −1)  
  - **Antinegator** (drives inputs to +1)  
  - **TNOT** (sign‑inversion style ternary NOT)  
- Binary operations:
  - **TAND** — ternary AND defined as the minimum in the order −1 < 0 < +1  
  - **TNAND** — ternary NAND defined as TNOT∘TAND, analogous to Boolean NAND  
- `logic_engine` module for dispatching these operations by name (used directly by the GUI).  

### Polarization encoding and decoding

- Fixed mapping of trits to **linear polarization** angles relative to the laser E‑field:
  - 0 → 0° (reference, parallel to E‑field)  
  - +1 → 120°  
  - −1 → 240°  
- Conversion between:
  - Trit ↔ angle (deg)  
  - Angle ↔ **Jones vector** (Ex, Ey)  
  - Jones vector ↔ **Stokes parameters** and **Poincaré‑sphere coordinates**  
- Serves as the bridge between abstract logic and optical simulation/visualization.  

### Subwavelength grating design (Si / SiN)

- `gratingdesign` module implements a simple **effective‑medium theory (EMT)** design workflow for 1D subwavelength gratings:
  - Inputs:
    - Laser wavelength (nm)  
    - Core material: **intrinsic silicon (Si)** or **silicon nitride (SiN)**  
    - Cladding index (e.g., silica or air)  
  - Outputs:
    - Grating period Λ  
    - Slit width w  
    - Duty cycle f = w / Λ  
    - Effective indices \(n_{\text{eff,TE}}\), \(n_{\text{eff,TM}}\)  
- Uses first‑order EMT formulas for TE/TM and sweeps duty cycle to maximize \(|n_{\text{eff,TE}} - n_{\text{eff,TM}}|\) as a crude polarization‑contrast figure of merit.  
- Includes representative refractive index values for intrinsic Si and SiN in the near‑IR (easily replaceable with more accurate datasets).  

### Triple‑channel polarization detector

- `trichanneldetector` module models a **triple‑channel Malus‑law detector**:
  - Three channels with pass axes at 0°, 120°, and 240° (one per ternary state).  
  - Per‑channel efficiency factors to model ideal or slightly lossy gratings.  
- For an incident polarization angle θ:
  - Uses **Malus law** \(I = \eta\,I_0 \cos^2(\Delta\theta)\) to compute transmitted intensity per channel.  
  - Decodes the trit as the channel with maximum intensity (argmax \(T_i\)).  
- Provides convenience methods to detect from:
  - Angle (deg)  
  - `PolarizationState`  
  - Ideal trits (for round‑trip tests)  

### Visualization helpers

- `visualizationhelpers` module (Matplotlib) for:
  - **Angle‑circle 3D plot**:
    - Unit circle in x–y plane  
    - Canonical ternary polarization states (−1, 0, +1)  
    - Current output state as a highlighted marker  
  - **Poincaré sphere 3D plot**:
    - Wireframe unit sphere  
    - Canonical states and current output point via Stokes parameters  
  - **2D Jones‑vector plot**:
    - Magnitudes and phases of Ex and Ey in side‑by‑side subplots  
- All exposed as functions returning `matplotlib.figure.Figure`, ready to be embedded in PyQt6 via `FigureCanvasQTAgg`.  

### PyQt6 desktop GUI

- **Grating tab**
  - Inputs:
    - Wavelength (nm)  
    - Material (Si / SiN)  
  - Outputs:
    - Period (nm)  
    - Slit width (nm)  
    - Duty cycle  
- **Logic tab**
  - Function dropdown populated from `logic_engine`:
    - `Cyclic`, `Negator`, `Antinegator`, `TNOT`, `TAND`, `TNAND`  
  - Trit input dropdowns (−1, 0, +1) with automatic handling of unary vs binary operations.  
  - Mode toggle:
    - **Ideal logic**: runs gates directly on trits.  
    - **Physical mode**: encodes trits to polarization, passes through triple‑channel detector, then runs gates on decoded trits.  
  - Embedded Matplotlib views for:
    - Angle circle  
    - Poincaré sphere  
    - Jones vector  

---

## Installation

### Requirements

- Python 3.10+ (recommended)  
- PyQt6  
- Matplotlib  
- NumPy  

Install dependencies (example):

```bash
pip install pyqt6 matplotlib numpy
```

If you plan to modify the physics or add numerical features, you may also want:

```bash
pip install scipy
```

---

## Running the GUI

From the repository root (the folder that contains `photology_simulator/`), run:

```bash
python -m photology_simulator.gui.main_window
```

If you use VS Code, set your working directory to the repo root and configure a launch configuration that runs the module `photology_simulator.gui.main_window`.  

---

## Repository structure

A typical layout looks like:

```bash
photology_simulator/
-init.py
-ternaryops.py # Trit enum and basic ternary ops
-polarization_encoder.py # Trit ↔ angle ↔ Jones ↔ Stokes
-gratingdesign.py # EMT-based subwavelength grating design
-trichanneldetector.py # Triple-channel Malus-law detector
-logic_engine.py # Operation selection and evaluation
-visualizationhelpers.py # Matplotlib-based plots for GUI
-gui/
|-init.py
|-main_window.py # PyQt6 main window and tabs
tests/
... # (optional) pytest-based tests
```

Names may differ slightly depending on how you organized the files, but the roles are as above.

---

## Usage overview

### 1. Explore grating designs

1. Open the GUI.  
2. Go to the **Grating** tab.  
3. Set a laser wavelength (e.g. 1550 nm) and material (Si / SiN).  
4. Click **Design grating**.  
5. Read off:
   - Period (nm)  
   - Slit width (nm)  
   - Duty cycle  
6. Use these as initial design guidelines for polarization‑selective gratings in your PICs.  

### 2. Experiment with ternary logic

1. Switch to the **Logic** tab.  
2. Choose a function (e.g. `TNAND`).  
3. Enter one or two trits depending on the operation.  
4. Select:
   - Ideal logic mode — see pure ternary behavior.  
   - Physical mode — see how the triple‑channel detector and polarization encoding affect the result.  
5. Click **Run** to:
   - Compute the output trit.  
   - Visualize the corresponding polarization state on:
     - The angle circle  
     - The Poincaré sphere  
     - The Jones‑vector plot  

---

## Limitations and future work

**Current limitations**

- Physics models are **first‑order**:
  - Grating design uses simple EMT and a contrast metric; no full RCWA/FDTD calibration yet.  
  - Triple‑channel detector is Malus‑law only, without noise or fabrication non‑idealities. 
- Gate set is **minimal**:
  - Only core ternary operations (Cyclic, Negator, Antinegator, TNOT, TAND, TNAND).  
  - No ternary adders, MUX/DEMUX, or complex gate networks yet.  
- No **project persistence**:
  - Simulations cannot yet be saved/loaded as project files; figure metadata export is not implemented.  
- Platform focus:
  - Developed and tested primarily on **Windows**; other platforms may need minor Qt/Matplotlib tweaks.  

**Planned directions**

- Add microring‑based device models and gate layouts.  
- Extend gate library (ternary half‑adders, full adders, multiplexers, memory).  
- Improve grating/detector realism (better material models, device‑specific calibration).  
- Project save/load and parameter export for reproducible research.  

---

## Contributing

Contributions and feedback are very welcome.

- **Issues:** Use the GitHub issue tracker for bug reports and feature requests.  
- **Pull requests:**  
  - Keep new modules small and focused (logic vs optics vs GUI).  
  - Include at least a minimal test (or a reproducible description) for new features.  
- **Style:**  
  - Python type hints where reasonable.  
  - Prefer small, composable functions and explicit imports.  

---

## License

MIT License

Copyright (c) 2025 Aritrash Sarkar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Acknowledgements

The models and design approach draw on standard references in balanced ternary computing, Jones/Stokes polarization formalisms, and subwavelength grating effective‑medium theory. 

Trine PICSIM is being developed as part of ongoing research into ternary photonic computing and microring‑based photonic integrated circuits.

This research is being conducted by students of the <strong>Department of Computer Science and Engineering</strong>, Meghnad Saha Institute of Technology, Kolkata 700150, WB, India

Contributors within or outside the department are welcome, and your names shall be updated under here. Currently, the research team is consisted of: <strong>Aritrash Sarkar, Adrija Ghosh, Pritam Mondal (Students, CSE-MSIT)</strong>.

The team extends their gratitude towards:
1. Prof. (Dr.) Subhrapratim Nath (HoD, CSE-MSIT)
2. Prof. (Dr.) Sudipta Ghosh (Professor, ECE-MSIT)
3. Prof. (Dr.) Utpal Gangopadhyay (Head of R&D - CARREST, MSIT)
4. Prof. (Dr.) Surama Biswas (Associate Professor, CSE-MSIT)
5. Tanushree Chakraborty (Asst. Professor, CSE-MSIT)
6. Papiya Das (Asst. Professor, CSE-MSIT)
7. Arpan Chakraborty (Tech Admin, CSE-MSIT)
8. Soumitra Khan (Technical Assistant, CSE-MSIT)
9. Dr. Sukhendu Jana (Asst. Professor - Physics, BSH-MSIT)
10. Ramij Hasan Shaik (Teaching Asst., CSE-MSIT)
11. Roheet Purkayastha (Student, CSE-MSIT)
12. Ankana Debnath (Student, CSE-MSIT)
13. Soumalya Dey (Student, CSE-MSIT)
14. Sayan Bera (Student, CSE-MSIT)
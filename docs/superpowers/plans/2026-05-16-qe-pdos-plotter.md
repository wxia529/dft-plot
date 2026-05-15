# QE PDOS Plotter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a QE PDOS file reader and plotter that reads Quantum ESPRESSO PDOS output files from disk and plots them using the same styling as the existing VASP plotter.

**Architecture:** New module `dftplot/dos/qe_plotter.py` with file parsing and plotting logic, reusing all config/constants from the existing `plotter.py`. Single entry point `plot_qe_dos(data_dir, prefix)`.

**Tech Stack:** Python, NumPy, Matplotlib

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `dftplot/dos/qe_plotter.py` | Create | QE PDOS file parser + plotter |
| `dftplot/dos/__init__.py` | Create | Export `plot_qe_dos` |

## Task Dependencies

```
Task 1: Parse total DOS (pdos_tot)
    ↓
Task 2: Parse projected DOS (pdos_atm files)
    ↓
Task 3: Plot QE DOS (reuse plotter.py styling)
    ↓
Task 4: Export + integration test
```

---

### Task 1: Parse Total DOS (`pdos_tot`)

**Files:**
- Create: `dftplot/dos/qe_plotter.py`

- [ ] **Step 1: Write the parser function for total DOS**

Add to `dftplot/dos/qe_plotter.py`:

```python
import os
import re
import numpy as np


def _parse_pdos_tot(filepath):
    """Parse QE pdos_tot file.
    
    Args:
        filepath: Path to {prefix}.pdos_tot file.
        
    Returns:
        Tuple of (energies, dos_up, dos_down) as numpy arrays.
    """
    data = np.loadtxt(filepath, comments="#")
    energies = data[:, 0]
    dos_up = data[:, 1]
    dos_down = data[:, 2]
    return energies, dos_up, dos_down
```

- [ ] **Step 2: Test the parser manually**

Run:
```python
from dftplot.dos.qe_plotter import _parse_pdos_tot
energies, dos_up, dos_down = _parse_pdos_tot("data/dos/sxh.pdos_tot")
print(f"Energies: {energies[:5]}")
print(f"DOS up: {dos_up[:5]}")
print(f"Shape: {energies.shape}")
```
Expected: Arrays with 4018 elements, energies starting around -24.11 eV

- [ ] **Step 3: Commit**

```bash
git add dftplot/dos/qe_plotter.py
git commit -m "feat: add QE pdos_tot parser"
```

---

### Task 2: Parse Projected DOS (pdos_atm files)

**Files:**
- Modify: `dftplot/dos/qe_plotter.py`

- [ ] **Step 1: Add filename parser and orbital mapping**

Append to `dftplot/dos/qe_plotter.py`:

```python
# QE orbital component ordering per l (from upflib/ylmr2.f90)
QE_ORBITAL_COMPONENTS = {
    "s": [""],  # single component, no suffix
    "p": ["pz", "px", "py"],
    "d": ["dz2", "dzx", "dzy", "dx2y2", "dxy"],
    "f": ["fz3", "fxz2", "fyz2", "fxyz", "fy3x2", "fzx2", "fx3"],
}


def _parse_filename(filename):
    """Parse QE PDOS filename to extract atom info.
    
    Args:
        filename: e.g. 'sxh.pdos_atm#91(Bi)_wfc#5(d)'
        
    Returns:
        Dict with keys: atom_num, element, wfc_num, orbital
    """
    pattern = r"pdos_atm#(\d+)\(([A-Z][a-z]?)\)_wfc#(\d+)\(([a-z]+)\)"
    match = re.search(pattern, filename)
    if not match:
        return None
    return {
        "atom_num": int(match.group(1)),
        "element": match.group(2),
        "wfc_num": int(match.group(3)),
        "orbital": match.group(4),
    }


def _parse_pdos_atm(filepath):
    """Parse a single QE pdos_atm file.
    
    Args:
        filepath: Path to pdos_atm file.
        
    Returns:
        Tuple of (info, energies, ldos_up, ldos_down, pdos_components)
        where pdos_components is list of (label, up_array, down_array)
    """
    info = _parse_filename(os.path.basename(filepath))
    if info is None:
        raise ValueError(f"Cannot parse filename: {filepath}")
    
    data = np.loadtxt(filepath, comments="#")
    energies = data[:, 0]
    ldos_up = data[:, 1]
    ldos_down = data[:, 2]
    
    orbital = info["orbital"]
    components = QE_ORBITAL_COMPONENTS.get(orbital, [])
    n_components = len(components)
    
    # Each component has 2 columns: pdos_up, pdos_down
    pdos_components = []
    elem = info["element"]
    for i, comp in enumerate(components):
        col_idx = 3 + i * 2
        if col_idx + 1 >= data.shape[1]:
            break
        comp_up = data[:, col_idx]
        comp_down = data[:, col_idx + 1]
        if comp:
            label = f"{elem}_{comp}"
        else:
            label = f"{elem}_{orbital}"
        pdos_components.append((label, comp_up, comp_down))
    
    return info, energies, ldos_up, ldos_down, pdos_components
```

- [ ] **Step 2: Test the filename parser**

Run:
```python
from dftplot.dos.qe_plotter import _parse_filename, _parse_pdos_atm

info = _parse_filename("sxh.pdos_atm#91(Bi)_wfc#5(d)")
print(info)
# Expected: {'atom_num': 91, 'element': 'Bi', 'wfc_num': 5, 'orbital': 'd'}

info, energies, ldos_up, ldos_down, components = _parse_pdos_atm("data/dos/sxh.pdos_atm#1(H)_wfc#3(p)")
print(f"Components: {[c[0] for c in components]}")
print(f"LDOS shape: {ldos_up.shape}")
```
Expected: Components = ['H_pz', 'H_px', 'H_py'], LDOS shape = (4018,)

- [ ] **Step 3: Commit**

```bash
git add dftplot/dos/qe_plotter.py
git commit -m "feat: add QE pdos_atm parser with orbital component extraction"
```

---

### Task 3: Build Main Parser and Plotter

**Files:**
- Modify: `dftplot/dos/qe_plotter.py`

- [ ] **Step 1: Add `parse_qe_pdos` function**

Append to `dftplot/dos/qe_plotter.py`:

```python
def parse_qe_pdos(data_dir, prefix="sxh"):
    """Read all QE PDOS files from directory.
    
    Args:
        data_dir: Directory containing QE PDOS output files.
        prefix: Filename prefix (default 'sxh').
        
    Returns:
        Dict compatible with plotting logic:
        - 'energies': np.array
        - 'fermi_energy': 0.0
        - 'up': total DOS up
        - 'down': total DOS down
        - '{Element}_{orbital}': projected DOS arrays
    """
    tot_file = os.path.join(data_dir, f"{prefix}.pdos_tot")
    energies, tot_up, tot_down = _parse_pdos_tot(tot_file)
    
    result = {
        "energies": energies,
        "fermi_energy": 0.0,
        "up": tot_up,
        "down": tot_down,
    }
    
    # Find all pdos_atm files
    pattern = re.compile(rf"^{re.escape(prefix)}\.pdos_atm#")
    atm_files = sorted([
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if pattern.search(f) and f.endswith(")")
    ])
    
    for filepath in atm_files:
        info, _, ldos_up, ldos_down, components = _parse_pdos_atm(filepath)
        elem = info["element"]
        orbital = info["orbital"]
        
        # Add LDOS (sum of all m components)
        ldos_label = f"{elem}_{orbital}"
        result[f"{ldos_label}_up"] = ldos_up
        result[f"{ldos_label}_down"] = ldos_down
        
        # Add individual m-components
        for label, comp_up, comp_down in components:
            result[f"{label}_up"] = comp_up
            result[f"{label}_down"] = comp_down
    
    return result
```

- [ ] **Step 2: Test parse_qe_pdos**

Run:
```python
from dftplot.dos.qe_plotter import parse_qe_pdos
data = parse_qe_pdos("data/dos", prefix="sxh")
print(f"Keys: {list(data.keys())[:10]}...")
print(f"Total keys: {len(data.keys())}")
print(f"H_p_up shape: {data['H_pz_up'].shape}")
```
Expected: Dict with energies, up/down, and many element_orbital_up/down keys

- [ ] **Step 3: Add `plot_qe_dos` function (reuses plotter.py config)**

Append to `dftplot/dos/qe_plotter.py`:

```python
from dftplot.dos.plotter import (
    ALIGN_TO_FERMI,
    SHOW_TOTAL_DOS,
    SHOW_FERMI_LINE,
    X_LIM,
    Y_LIM,
    ORDER_MODE,
    MANUAL_ORDER,
    COLOR_MODE,
    MANUAL_COLORS,
    ELEMENT_COLORS,
    ORBITAL_COLORS,
    ELEMENT_ORBITAL_COLORS,
    LEGEND_LOC,
    LEGEND_NCOL,
    COLOR_TOTAL,
    GENERAL_FONT_SIZE,
    LEGEND_FONT_SIZE,
    AUTO_SAVE_FIGURE,
    SAVE_FIGURE_PATH,
    SAVE_FIGURE_DPI,
    get_sorted_labels,
    extract_base_labels,
    get_pdos_color,
    format_legend_label,
    apply_custom_ticks,
    save_figure_if_needed,
)
import matplotlib.pyplot as plt
import numpy as np


def plot_qe_dos(data_dir, prefix="sxh"):
    """Read QE PDOS files and plot total + projected DOS.
    
    Args:
        data_dir: Directory containing QE PDOS output files.
        prefix: Filename prefix (default 'sxh').
    """
    dos_data = parse_qe_pdos(data_dir, prefix)
    
    # Energy alignment (QE energies already relative to E_F)
    plot_energy = dos_data["energies"]
    fermi_line = 0.0
    xlabel_text = r"Energy (eV) relative to E$_F$"
    
    dos_up = dos_data["up"]
    dos_dw = dos_data["down"]
    has_spin = np.any(dos_dw) and not np.allclose(dos_up, dos_dw)
    
    # Label processing
    ignore_keys = {"energies", "fermi_energy", "up", "down"}
    raw_prefixed_labels = [k for k in dos_data.keys() if k not in ignore_keys]
    raw_labels = extract_base_labels(raw_prefixed_labels)
    sorted_labels = get_sorted_labels(raw_labels, mode=ORDER_MODE, manual_order=MANUAL_ORDER)
    
    # Color palette
    if COLOR_MODE == "manual":
        palette = MANUAL_COLORS
    else:
        palette = [
            "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e",
            "#9467bd", "#8c564b", "#e377c2",
        ]
    
    # Plotting
    fig, ax = plt.subplots(figsize=(6, 4.5))
    mask_view = (plot_energy >= X_LIM[0]) & (plot_energy <= X_LIM[1])
    y_max_trackers = []
    
    # Total DOS
    if SHOW_TOTAL_DOS:
        ax.plot(plot_energy, dos_up, c=COLOR_TOTAL, lw=1, label="Total", zorder=1)
        ax.plot(plot_energy, -dos_dw, c=COLOR_TOTAL, lw=1, zorder=1)
        if np.any(mask_view):
            y_max_trackers.extend([dos_up[mask_view].max(), np.abs(dos_dw[mask_view]).max()])
    
    # Projected DOS
    for i, label in enumerate(sorted_labels):
        color = get_pdos_color(label, palette, i)
        legend_label = format_legend_label(label)
        
        if f"{label}_up" in dos_data and f"{label}_down" in dos_data:
            y_up = dos_data[f"{label}_up"]
            y_dw = dos_data[f"{label}_down"]
        elif label in dos_data:
            y_up = dos_data[label]
            y_dw = np.zeros_like(plot_energy)
        else:
            continue
        
        if has_spin and np.any(y_dw):
            ax.plot(plot_energy, y_up, lw=1.5, c=color, label=legend_label)
            ax.plot(plot_energy, -y_dw, lw=1.5, c=color)
            ax.fill_between(plot_energy, 0, y_up, color=color, alpha=0.2)
            ax.fill_between(plot_energy, 0, -y_dw, color=color, alpha=0.2)
            if np.any(mask_view):
                y_max_trackers.extend([y_up[mask_view].max(), np.abs(y_dw[mask_view]).max()])
        else:
            ax.plot(plot_energy, y_up, lw=1.5, c=color, label=legend_label)
            ax.fill_between(plot_energy, 0, y_up, color=color, alpha=0.2)
            if np.any(mask_view):
                y_max_trackers.append(y_up[mask_view].max())
    
    # Formatting
    curr_max = np.max(y_max_trackers) if y_max_trackers else 1.0
    if Y_LIM:
        ax.set_ylim(Y_LIM)
    else:
        ylim_top = curr_max * 1.25
        ax.set_ylim(-ylim_top, ylim_top)
    
    if SHOW_FERMI_LINE:
        ax.axvline(fermi_line, ls="--", c="gray", lw=1.0, label="E$_F$")
    ax.axhline(0, c="black", lw=0.5)
    ax.set_xlim(X_LIM)
    ax.set_xlabel(xlabel_text)
    ax.set_ylabel("Density of states (states/eV)")
    apply_custom_ticks(ax)
    ax.legend(loc=LEGEND_LOC, frameon=False, fontsize=LEGEND_FONT_SIZE, ncol=LEGEND_NCOL)
    
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    
    plt.tight_layout()
    save_figure_if_needed(fig)
    plt.show()
```

- [ ] **Step 4: Test the plotter**

Run:
```python
from dftplot.dos.qe_plotter import plot_qe_dos
plot_qe_dos("data/dos", prefix="sxh")
```
Expected: Plot window with total DOS (black) and projected DOS lines, Fermi level marker

- [ ] **Step 5: Commit**

```bash
git add dftplot/dos/qe_plotter.py
git commit -m "feat: add plot_qe_dos with full styling from plotter.py"
```

---

### Task 4: Export and Integration

**Files:**
- Create: `dftplot/dos/__init__.py`

- [ ] **Step 1: Create `__init__.py`**

Create `dftplot/dos/__init__.py`:

```python
from dftplot.dos.plotter import plot_vasp_dos
from dftplot.dos.qe_plotter import plot_qe_dos

__all__ = ["plot_vasp_dos", "plot_qe_dos"]
```

- [ ] **Step 2: Test import**

Run:
```python
from dftplot.dos import plot_qe_dos
print("Import OK")
```
Expected: No errors, function available

- [ ] **Step 3: Final commit**

```bash
git add dftplot/dos/__init__.py
git commit -m "feat: export plot_qe_dos from dftplot.dos"
```

---

## Self-Review

**Spec coverage:**
- Parse total DOS (pdos_tot) → Task 1 ✓
- Parse projected DOS (pdos_atm files) → Task 2 ✓
- QE orbital ordering (pz/px/py, dz2/dzx/...) → Task 2 (QE_ORBITAL_COMPONENTS) ✓
- Spin handling (up/down detection) → Task 3 ✓
- Config sharing from plotter.py → Task 3 (imports all constants) ✓
- Label convention (Element_orbital) → Task 2 ✓
- Fermi energy = 0.0 → Task 3 ✓
- Export from dftplot.dos → Task 4 ✓

**Placeholder scan:** No TBDs, TODOs, or vague instructions found ✓

**Type consistency:** All function signatures consistent across tasks ✓

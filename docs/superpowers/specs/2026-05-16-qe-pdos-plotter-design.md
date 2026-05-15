# QE PDOS Plotter Design

## Overview

New module `dftplot/dos/qe_plotter.py` that reads Quantum ESPRESSSO PDOS output files from disk and plots them using the same styling as the existing VASP plotter.

## API

```python
def plot_qe_dos(data_dir: str, prefix: str = "sxh") -> None:
    """Read QE PDOS files and plot total + projected DOS.
    
    Args:
        data_dir: Directory containing QE PDOS output files.
        prefix: Filename prefix (default "sxh" for sxh.pdos_tot, etc.).
    """
```

## File Parsing

### Total DOS (`{prefix}.pdos_tot`)
- Format: `E DOSup(E) DOSdw(E) PDOSup(E) PDOSdw(E)`
- Read with `np.loadtxt`, skip header line starting with `#`

### Projected DOS (`{prefix}.pdos_atm#N(X)_wfc#M(l)`)
- Filename encodes: atom number N, element X, wfc number M, orbital type l
- Format: `E LDOSup LDOSdw PDOSup PDOSdw [PDOS_m_up PDOS_m_dw ...]`
- For s: 1 PDOS component
- For p: 3 PDOS components (pz, px, py per QE ordering)
- For d: 5 PDOS components (dz2, dzx, dzy, dx2-y2, dxy per QE ordering)
- For f: 7 PDOS components

### QE Orbital Ordering (from upflib/ylmr2.f90)
Real spherical harmonics order:
- l=1 (p): pz (m=0), px (cos m=±1), py (sin m=±1)
- l=2 (d): dz2 (m=0), dzx (cos m=±1), dzy (sin m=±1), dx2-y2 (cos m=±2), dxy (sin m=±2)
- l=3 (f): 7 components following same pattern

## Architecture

### Components
1. **`parse_qe_pdos(data_dir, prefix)`** - Reads all PDOS files, returns dict compatible with plotting logic
2. **`plot_qe_dos(data_dir, prefix)`** - Main entry point, calls parser then plots
3. **Internal helpers** - filename parsing, orbital label generation

### Config Sharing
- Import all constants from `plotter.py` (colors, labels, sorting, fonts, etc.)
- Reuse `get_sorted_labels`, `format_legend_label`, `get_pdos_color`, `ORBITAL_MATH_LABELS`
- QE-specific orbital order mapping defined locally

### Data Flow
```
data_dir/*.pdos* files
    ↓
parse_qe_pdos() → dict with keys:
    - "energies": np.array
    - "fermi_energy": float (set to 0, QE energies already relative)
    - "up": total DOS up
    - "down": total DOS down (if spin-polarized)
    - "H_s": H atom s-orbital total
    - "H_pz": H atom pz orbital
    - "Bi_dz2": Bi atom dz2 orbital
    - etc.
    ↓
plot_qe_dos() → reuses plotter.py styling logic
```

## Label Convention

Labels follow pattern: `{Element}_{orbital}` or `{Element}_{orbital}_up`/`_down` for spin-polarized.

Examples:
- `H_s` - Hydrogen s-orbital (sum of all m components)
- `H_pz` - Hydrogen pz orbital
- `Bi_dz2` - Bismuth dz2 orbital
- `I_p` - Iodine p-orbital total (sum of px, py, pz)

For multi-component orbitals (p, d, f), both the total (LDOS) and individual m-components are plotted.

## Spin Handling

QE output is always spin-polarized (has up/down columns). The plotter:
- Detects if up ≠ down (truly spin-polarized) vs up == down (unpolarized)
- If unpolarized: plot single line, fill between
- If spin-polarized: plot up positive, down negative (same as VASP plotter)

## Fermi Energy

QE PDOS energies are already relative to Fermi level. Set `fermi_energy = 0.0` and use `ALIGN_TO_FERMI = True` behavior (no shift needed).

## Testing

Manual testing via notebook or Python:
```python
from dftplot.dos.qe_plotter import plot_qe_dos
plot_qe_dos("data/dos", prefix="sxh")
```

## Files Created/Modified

| File | Action |
|------|--------|
| `dftplot/dos/qe_plotter.py` | Create - main QE PDOS reader and plotter |
| `dftplot/dos/__init__.py` | Update - export `plot_qe_dos` |

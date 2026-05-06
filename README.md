# DFT Plot

Tools for visualizing DFT calculation results (VASP).

## Features

- DOS plotting using py4vasp
- Easy customization via Jupyter notebooks
- Modular design for adding new plot types (band structure, charge density, etc.)

## Installation

```bash
pip install -e .
```

For development with Jupyter:

```bash
pip install -e ".[dev]"
```

## Quick Start

1. Put your VASP output files in the `data/` directory
2. Open `notebooks/dos.ipynb`
3. Run the notebook

```python
from dftplot.dos import plotter
from py4vasp import Calculation

calc = Calculation.from_path("data/dos")

# Configure
plotter.SHOW_TOTAL_DOS = False
plotter.X_LIM = [-5, 5]
plotter.COLOR_MODE = "mapped"  # use ORBITAL_COLORS/ELEMENT_COLORS first
plotter.ELEMENT_ORBITAL_COLORS = {"V": {"dxy": "#1f77b4", "dx2-y2": "#ff7f0e"}}
plotter.ENABLE_CUSTOM_TICKS = True
plotter.X_TICK_INTERVAL = 1.0
plotter.Y_TICK_INTERVAL = 2.0
plotter.AUTO_SAVE_FIGURE = True
plotter.SAVE_FIGURE_PATH = "dos.png"
plotter.SAVE_FIGURE_DPI = 600

# Plot
plotter.plot_vasp_dos(calc.dos.to_dict(selection="d(Fe), p(O)"))
```

## Directory Structure

```
dft-plot/
├── notebooks/           # Jupyter notebooks (user entry point)
├── dftplot/             # Core package
│   ├── dos/             # DOS plotting
│   ├── band/            # Band structure (TODO)
│   ├── charge/          # Charge density (TODO)
│   └── utils/           # Utilities
├── data/                # Your VASP output files (.gitignore)
├── examples/            # Example data
└── README.md
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `X_LIM` | Energy range (eV) | `[-5, 5]` |
| `Y_LIM` | DOS range | `None` (auto) |
| `GENERAL_FONT_SIZE` | Base font size | `14` |
| `LEGEND_LOC` | Legend position | `"upper left"` |
| `ALIGN_TO_FERMI` | Shift energy to Fermi level | `True` |
| `SHOW_TOTAL_DOS` | Show total DOS line | `True` |
| `SHOW_FERMI_LINE` | Show Fermi level line | `True` |
| `AUTO_SAVE_FIGURE` | Auto-save figure during plotting | `True` |
| `SAVE_FIGURE_PATH` | Output path for auto-saved figure | `"dos.png"` |
| `SAVE_FIGURE_DPI` | DPI for auto-saved figure | `600` |
| `COLOR_MODE` | Color strategy: `auto` / `manual` / `mapped` | `"auto"` |
| `MANUAL_COLORS` | Fallback/explicit color list (manual mode) | `[]` |
| `ELEMENT_ORBITAL_COLORS` | Per-element orbital map (mapped mode, highest priority) | `{}` |
| `ELEMENT_COLORS` | Element color map (mapped mode) | `{"Sc": "#5FBAAF", "Cu": "#C29FD0"}` |
| `ORBITAL_COLORS` | Orbital color map (mapped mode) | `{"dxy": "...", ...}` |
| `ENABLE_CUSTOM_TICKS` | Enable fixed tick intervals | `False` |
| `X_TICK_INTERVAL` | X tick spacing when enabled | `None` |
| `Y_TICK_INTERVAL` | Y tick spacing when enabled | `None` |

## License

MIT

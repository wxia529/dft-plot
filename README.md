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
| `x_lim` | Energy range (eV) | `[-5, 5]` |
| `y_lim` | DOS range | `None` (auto) |
| `font_size` | Font size | `14` |
| `legend_loc` | Legend position | `"upper left"` |
| `align_to_fermi` | Shift energy to Fermi level | `True` |
| `show_total_dos` | Show total DOS line | `False` |
| `show_fermi_line` | Show Fermi level line | `False` |

## License

MIT

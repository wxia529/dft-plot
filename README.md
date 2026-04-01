# DFT Plot

Tools for visualizing DFT calculation results (VASP).

## Features

- DOS plotting from `vaspout.h5` or `DOSCAR`
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

1. Put your VASP output files (`vaspout.h5`, `DOSCAR`, etc.) in the `data/` directory
2. Open `notebooks/01_dos_plotting.ipynb`
3. Modify the filepath and run

```python
from dftplot import read_vaspout, plot_dos

# Read data
dos_data = read_vaspout("data/vaspout.h5")

# Plot
plot_dos(dos_data, save_path="dos.png", x_lim=[-10, 10])
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

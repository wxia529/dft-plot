# AGENTS.md - Repository Guidelines

## Project Overview

DFT Plot is a Python package for visualizing DFT (Density Functional Theory) calculation results from VASP. The package provides tools for plotting DOS (Density of States), with planned support for band structures and charge density.

## Build & Development Commands

### Installation
```bash
# Install package in editable mode
pip install -e .

# Install with development dependencies (Jupyter)
pip install -e ".[dev]"
```

### Running Code
```bash
# Open Jupyter notebook (main user interface)
jupyter lab notebooks/dos.ipynb

# Run Python script directly
python -c "from dftplot import plot_vasp_dos"
```

### Testing
```bash
# No formal test suite yet - tests are manual via notebooks
# Test by running notebook cells or importing modules
python -c "from dftplot.dos import plot_vasp_dos; print('OK')"
```

### Linting & Formatting
```bash
# No linter configured yet - add ruff/flake8 as needed
# Check imports are organized (stdlib, third-party, local)
```

## Code Style Guidelines

### Imports
- Order: standard library → third-party → local packages
- Use absolute imports from `dftplot` package
- Example:
  ```python
  import numpy as np
  import matplotlib.pyplot as plt
  
  from dftplot.dos import plotter
  ```

### Naming Conventions
- **Functions**: `snake_case` (e.g., `plot_vasp_dos`)
- **Variables**: `snake_case` (e.g., `dos_data`, `fermi_energy`)
- **Constants**: `UPPER_CASE` (e.g., `FONT_SIZE`, `X_LIM`)
- **Modules**: `snake_case` (e.g., `plotter.py`, `io.py`)

### Function Signatures
- Use docstrings with `Args:` and `Returns:` sections

### Type Hints
- Optional but encouraged for new code
- No strict type checking enforced yet

### Error Handling
- Raise exceptions for invalid inputs
- Use descriptive error messages
- Catch specific exceptions (not bare `except:`)

### Formatting
- Use double quotes for strings: `"text"`
- Use f-strings for formatting: `f"{value}"`
- Max line length: ~100 chars (flexible)

## Project Structure

```
dft-plot/
├── notebooks/           # Jupyter notebooks (user entry)
├── dftplot/             # Core package
│   ├── __init__.py      # Main exports
│   ├── dos/             # DOS plotting (implemented)
│   │   ├── __init__.py
│   │   └── plotter.py   # Main plotting logic
│   ├── band/            # Band structure (TODO)
│   ├── charge/          # Charge density (TODO)
│   └── utils/
│       └── __init__.py
├── data/                # User VASP files (.gitignore)
├── examples/            # Example data
├── pyproject.toml       # Package config
└── README.md
```

## Key Patterns

### Module Pattern
Each plotting module (dos, band, charge) should have:
- `__init__.py` - exports main function
- `plotter.py` - core plotting logic with config constants

### Data Flow
1. User places VASP files in `data/`
2. Notebook uses `py4vasp` to read data: `calc.dos.to_dict(selection="...")`
3. Data passed to `plot_vasp_dos(dos_data)`
4. Plot saved or displayed

### Configuration
- Global constants at module top (e.g., `FONT_SIZE`, `X_LIM`)
- Functions accept `**kwargs` to override defaults

## Adding New Features

### New Plot Type (e.g., Band Structure)
1. Create `dftplot/band/` directory
2. Add `__init__.py` and `plotter.py`
3. Implement `plot_band()` function
4. Export in `dftplot/__init__.py`
5. Add notebook `notebooks/02_band_plotting.ipynb`

### New File Format Support
1. Add reader function in appropriate module
2. Follow existing pattern in `plotter.py`
3. Add docstring with Args/Returns

## Git Workflow

- Commit messages: imperative mood ("Add feature", "Fix bug")
- Keep commits focused and atomic
- No commits to main without review (if collaborating)

## Notes for Agents

- **DO NOT** modify user's original plotting logic unless fixing bugs
- **DO** preserve existing function names and signatures
- **DO** maintain backward compatibility
- **PREFER** adding new functions over modifying existing ones
- The `data/` directory is in `.gitignore` - never commit VASP output files

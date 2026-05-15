import os

import numpy as np


def _parse_pdos_tot(filepath):
    """Parse QE pdos_tot file.
    
    Note: QE energies are already relative to the Fermi level.
    
    Args:
        filepath: Path to {prefix}.pdos_tot file.
        
    Returns:
        Tuple of (energies, dos_up, dos_down) as numpy arrays.
        
    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If data has fewer than 3 columns.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    data = np.loadtxt(filepath, comments="#")
    if data.ndim == 1:
        data = data.reshape(-1, data.shape[0])
    if data.shape[1] < 3:
        raise ValueError(f"Expected at least 3 columns, got {data.shape[1]}")
    
    energies = data[:, 0]
    dos_up = data[:, 1]
    dos_down = data[:, 2]
    return energies, dos_up, dos_down

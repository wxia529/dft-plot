import os
import re

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
        data = data.reshape(1, -1)
    if data.shape[1] < 3:
        raise ValueError(f"Expected at least 3 columns, got {data.shape[1]}")
    
    energies = data[:, 0]
    dos_up = data[:, 1]
    dos_down = data[:, 2]
    return energies, dos_up, dos_down


QE_ORBITAL_COMPONENTS = {
    "s": [""],
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
        
    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If data has fewer than 3 columns.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    info = _parse_filename(os.path.basename(filepath))
    if info is None:
        raise ValueError(f"Cannot parse filename: {filepath}")
    
    data = np.loadtxt(filepath, comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.shape[1] < 3:
        raise ValueError(f"Expected at least 3 columns, got {data.shape[1]}")
    
    energies = data[:, 0]
    ldos_up = data[:, 1]
    ldos_down = data[:, 2]
    
    orbital = info["orbital"]
    components = QE_ORBITAL_COMPONENTS.get(orbital, [])
    
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

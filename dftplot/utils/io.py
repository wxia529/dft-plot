import h5py
import numpy as np


def read_vaspout(filepath):
    """
    Read DOS data from vaspout.h5 file.

    Args:
        filepath: path to vaspout.h5

    Returns:
        dict with energies, fermi_energy, up, down, and orbital projections
    """
    dos_data = {}

    with h5py.File(filepath, "r") as f:
        dos_data["energies"] = f["dos/energies"][:]
        dos_data["fermi_energy"] = float(f["electronic/fermi_level"][()])

        if "dos/spin_0" in f:
            dos_data["up"] = f["dos/spin_0"][:]
            if "dos/spin_1" in f:
                dos_data["down"] = f["dos/spin_1"][:]
            else:
                dos_data["down"] = np.zeros_like(dos_data["up"])
        else:
            dos_data["up"] = f["dos/total"][:]
            dos_data["down"] = np.zeros_like(dos_data["up"])

        if "dos/projectors" in f:
            proj = f["dos/projectors"]
            for key in proj.keys():
                proj_data = proj[key][:]
                if proj_data.ndim == 2:
                    dos_data[f"{key}_up"] = proj_data[:, 0]
                    if proj_data.shape[1] > 1:
                        dos_data[f"{key}_down"] = proj_data[:, 1]
                else:
                    dos_data[f"{key}_up"] = proj_data[:]
                    dos_data[f"{key}_down"] = np.zeros_like(proj_data[:])

    return dos_data


def read_doscar(filepath):
    """
    Read DOS data from DOSCAR file.

    Args:
        filepath: path to DOSCAR

    Returns:
        dict with energies, fermi_energy, up, down
    """
    with open(filepath, "r") as f:
        lines = f.readlines()

    fermi_energy = float(lines[5].split()[3])

    dos_lines = lines[6:]
    energies = []
    dos_up = []
    dos_down = []

    for line in dos_lines:
        parts = line.split()
        if len(parts) >= 2:
            energies.append(float(parts[0]))
            dos_up.append(float(parts[1]))
            if len(parts) >= 3:
                dos_down.append(float(parts[2]))
            else:
                dos_down.append(0.0)

    return {
        "energies": np.array(energies),
        "fermi_energy": fermi_energy,
        "up": np.array(dos_up),
        "down": np.array(dos_down),
    }

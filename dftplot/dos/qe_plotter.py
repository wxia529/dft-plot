import os
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from dftplot.dos.plotter import (
    SHOW_TOTAL_DOS,
    SHOW_FERMI_LINE,
    X_LIM,
    Y_LIM,
    ENABLE_CUSTOM_TICKS,
    X_TICK_INTERVAL,
    Y_TICK_INTERVAL,
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

DEFAULT_COLOR_PALETTE = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#ff7f0e",
    "#9467bd",
    "#8c564b",
    "#e377c2",
]


def _parse_pdos_tot(filepath):
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


def _match_atom_filter(info, atom_filter):
    if atom_filter is None:
        return True
    for item in atom_filter:
        if isinstance(item, int) and info["atom_num"] == item:
            return True
        if isinstance(item, str) and info["element"] == item:
            return True
    return False


def parse_qe_pdos(data_dir, prefix="sxh", atom_filter=None, group_by=None):
    tot_file = os.path.join(data_dir, f"{prefix}.pdos_tot")
    energies, tot_up, tot_down = _parse_pdos_tot(tot_file)

    result = {
        "energies": energies,
        "fermi_energy": 0.0,
        "up": tot_up,
        "down": tot_down,
    }

    pattern = re.compile(rf"^{re.escape(prefix)}\.pdos_atm#")
    atm_files = sorted([
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if pattern.search(f) and f.endswith(")")
    ])

    if group_by == "element":
        elem_up = {}
        elem_down = {}
        for filepath in atm_files:
            info, _, ldos_up, ldos_down, components = _parse_pdos_atm(filepath)
            if not _match_atom_filter(info, atom_filter):
                continue
            elem = info["element"]
            if elem not in elem_up:
                elem_up[elem] = np.zeros_like(ldos_up)
                elem_down[elem] = np.zeros_like(ldos_down)
            elem_up[elem] += ldos_up
            elem_down[elem] += ldos_down
        for elem in sorted(elem_up.keys()):
            result[f"{elem}_up"] = elem_up[elem]
            result[f"{elem}_down"] = elem_down[elem]

    elif group_by == "orbital":
        orb_up = {}
        orb_down = {}
        for filepath in atm_files:
            info, _, ldos_up, ldos_down, components = _parse_pdos_atm(filepath)
            if not _match_atom_filter(info, atom_filter):
                continue
            orbital = info["orbital"]
            if orbital not in orb_up:
                orb_up[orbital] = np.zeros_like(ldos_up)
                orb_down[orbital] = np.zeros_like(ldos_down)
            orb_up[orbital] += ldos_up
            orb_down[orbital] += ldos_down
        for orbital in sorted(orb_up.keys()):
            result[f"{orbital}_up"] = orb_up[orbital]
            result[f"{orbital}_down"] = orb_down[orbital]

    else:
        for filepath in atm_files:
            info, _, ldos_up, ldos_down, components = _parse_pdos_atm(filepath)
            if not _match_atom_filter(info, atom_filter):
                continue
            elem = info["element"]
            orbital = info["orbital"]

            ldos_label = f"{elem}_{orbital}"
            result[f"{ldos_label}_up"] = ldos_up
            result[f"{ldos_label}_down"] = ldos_down

            for label, comp_up, comp_down in components:
                result[f"{label}_up"] = comp_up
                result[f"{label}_down"] = comp_down

    return result


def plot_qe_dos(data_dir, prefix="sxh", atom_filter=None, group_by=None):
    dos_data = parse_qe_pdos(data_dir, prefix, atom_filter=atom_filter, group_by=group_by)

    plot_energy = dos_data["energies"]
    fermi_line = 0.0
    xlabel_text = r"Energy (eV) relative to E$_F$"

    dos_up = dos_data["up"]
    dos_dw = dos_data["down"]
    has_spin = np.any(dos_dw) and not np.allclose(dos_up, dos_dw)

    ignore_keys = {"energies", "fermi_energy", "up", "down"}
    raw_prefixed_labels = [k for k in dos_data.keys() if k not in ignore_keys]
    raw_labels = extract_base_labels(raw_prefixed_labels)
    sorted_labels = get_sorted_labels(raw_labels, mode=ORDER_MODE, manual_order=MANUAL_ORDER)

    if COLOR_MODE == "manual":
        palette = MANUAL_COLORS
    else:
        palette = DEFAULT_COLOR_PALETTE

    fig, ax = plt.subplots(figsize=(6, 4.5))
    mask_view = (plot_energy >= X_LIM[0]) & (plot_energy <= X_LIM[1])
    y_max_trackers = []

    if SHOW_TOTAL_DOS:
        if has_spin:
            ax.plot(plot_energy, dos_up, c=COLOR_TOTAL, lw=1, label="Total", zorder=1)
            ax.plot(plot_energy, -dos_dw, c=COLOR_TOTAL, lw=1, zorder=1)
            if np.any(mask_view):
                y_max_trackers.extend([dos_up[mask_view].max(), np.abs(dos_dw[mask_view]).max()])
        else:
            ax.plot(plot_energy, dos_up, c=COLOR_TOTAL, lw=1, label="Total", zorder=1)
            ax.fill_between(plot_energy, 0, dos_up, color="gray", alpha=0.1)
            if np.any(mask_view):
                y_max_trackers.append(dos_up[mask_view].max())

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

    curr_max = np.max(y_max_trackers) if y_max_trackers else 1.0
    if Y_LIM:
        ax.set_ylim(Y_LIM)
    else:
        ylim_top = curr_max * 1.25
        if has_spin:
            ax.set_ylim(-ylim_top, ylim_top)
        else:
            ax.set_ylim(0, ylim_top)

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

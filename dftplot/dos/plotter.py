import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import re

# ==========================================
#           GLOBAL CONFIGURATION
# ==========================================
# --- 1. Basic Plotting Switches ---
ALIGN_TO_FERMI = True  # True: Shift energy so Fermi level is at 0 eV.
SHOW_TOTAL_DOS = False  # True: Plot the total DOS (black line).
SHOW_FERMI_LINE = False  # True: Show Fermi plots

# --- 2. Axis Limits ---
X_LIM = [-5, 5]  # X-axis range (Energy in eV).
Y_LIM = None  # Y-axis range (DOS units). Set to None for auto-scaling.

# --- 3. Sorting & Ordering Logic ---
ORDER_MODE = "auto"  # Options: 'auto' (Metals first) or 'manual'.
MANUAL_ORDER = ["Fe", "Ti", "O", "N"]  # Order of elements if mode is 'manual'.
COLOR_MODE = "auto"  # Options: 'auto' (default palette) or 'manual'.
MANUAL_COLORS = []  # Custom hex codes or color names if mode is 'manual'.

# --- 4. Aesthetics ---
LEGEND_LOC = "upper left"  # Position of the legend.
LEGEND_NCOL = 1  #
COLOR_TOTAL = "k"  # Color for the total DOS line.

# --- 5. Font Configuration (NEW: Separated Sizes) ---
GENERAL_FONT_SIZE = 14  # 坐标轴标签、刻度等通用字体大小
LEGEND_FONT_SIZE = 10  # 图例专用的字体大小 (独立控制)

# --- Global Style Settings ---
mpl.rcParams["font.family"] = "Arial"
mpl.rcParams["font.size"] = GENERAL_FONT_SIZE  # 应用通用字体大小
mpl.rcParams["font.weight"] = "bold"
mpl.rcParams["axes.labelweight"] = "bold"
mpl.rcParams["axes.unicode_minus"] = False

# --- Helper Constant for 'auto' sorting ---
NON_METALS = {
    "H",
    "He",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "Se",
    "Br",
}


def get_sorted_labels(labels, mode="auto", manual_order=None):
    """
    Sorts PDOS labels based on the selected mode.
    """

    def get_element(label):
        match = re.match(r"([A-Z][a-z]?)", label)
        return match.group(1) if match else label

    if mode == "manual" and manual_order:
        priority_map = {k: i for i, k in enumerate(manual_order)}

        def manual_key(lbl):
            return (priority_map.get(get_element(lbl), priority_map.get(lbl, 999)), lbl)

        return sorted(labels, key=manual_key)

    else:
        metals, non_metals, others = [], [], []
        for label in labels:
            elem = get_element(label)
            if elem in NON_METALS:
                non_metals.append(label)
            elif re.match(r"[A-Z][a-z]?", elem):
                metals.append(label)
            else:
                others.append(label)
        return sorted(metals) + sorted(non_metals) + sorted(others)


def extract_base_labels(labels):
    """
    Extract base labels by stripping _up/_down suffixes.
    For spin-polarized data from py4vasp, keys like 'V_d_up' and 'V_d_down'
    should be merged into a single base label 'V_d'.

    Args:
        labels: List of label strings (may contain _up/_down suffixes)

    Returns:
        List of unique base labels with suffixes stripped
    """
    base_labels = set()
    for label in labels:
        if label.endswith("_up") or label.endswith("_down"):
            base_labels.add(label.rsplit("_", 1)[0])
        else:
            base_labels.add(label)
    return list(base_labels)


def plot_vasp_dos(dos_data):
    """
    Main plotting function.
    """

    # ---------------- 1. Data Parsing & Energy Alignment ----------------
    raw_energy = np.array(dos_data["energies"])
    efermi_val = float(dos_data["fermi_energy"])

    if ALIGN_TO_FERMI:
        plot_energy = raw_energy - efermi_val
        fermi_line = 0.0
        xlabel_text = r"Energy (eV) relative to E$_F$"
    else:
        plot_energy = raw_energy
        fermi_line = efermi_val
        xlabel_text = "Absolute Energy (eV)"

    # Support py4vasp to_dict() format (uses 'total' instead of 'up'/'down')
    if "total" in dos_data:
        dos_up = np.array(dos_data["total"])
        has_spin = False
        dos_dw = None
    else:
        dos_up = np.array(dos_data["up"])
        has_spin = "down" in dos_data and np.any(dos_data["down"])
        dos_dw = np.array(dos_data["down"]) if has_spin else None

    # ---------------- 2. Label Processing & Color Setup ----------------
    ignore_keys = ["energies", "fermi_energy", "up", "down", "total"]
    raw_prefixed_labels = [k for k in dos_data.keys() if k not in ignore_keys]
    raw_labels = extract_base_labels(raw_prefixed_labels)

    sorted_labels = get_sorted_labels(
        raw_labels, mode=ORDER_MODE, manual_order=MANUAL_ORDER
    )

    if COLOR_MODE == "manual" and MANUAL_COLORS:
        palette = MANUAL_COLORS
    else:
        palette = [
            "#1f77b4",
            "#d62728",
            "#2ca02c",
            "#ff7f0e",
            "#9467bd",
            "#8c564b",
            "#e377c2",
        ]

    # ---------------- 3. Plotting Execution ----------------
    fig, ax = plt.subplots(figsize=(6, 4.5))

    mask_view = (plot_energy >= X_LIM[0]) & (plot_energy <= X_LIM[1])
    y_max_trackers = []

    # --- A. Plot Total DOS (Optional) ---
    if SHOW_TOTAL_DOS:
        if has_spin:
            ax.plot(plot_energy, dos_up, c=COLOR_TOTAL, lw=1, label="Total", zorder=1)
            ax.plot(plot_energy, -dos_dw, c=COLOR_TOTAL, lw=1, zorder=1)
            if np.any(mask_view):
                y_max_trackers.extend(
                    [dos_up[mask_view].max(), np.abs(dos_dw[mask_view]).max()]
                )
        else:
            ax.plot(plot_energy, dos_up, c=COLOR_TOTAL, lw=1, label="Total", zorder=1)
            ax.fill_between(plot_energy, 0, dos_up, color="gray", alpha=0.1)
            if np.any(mask_view):
                y_max_trackers.append(dos_up[mask_view].max())

    # --- B. Plot PDOS (Projected DOS) ---
    for i, label in enumerate(sorted_labels):
        color = palette[i % len(palette)]

        # Check for spin-polarized data: try label_up/label_down first
        if f"{label}_up" in dos_data and f"{label}_down" in dos_data:
            y_up = dos_data[f"{label}_up"]
            y_dw = dos_data[f"{label}_down"]
        elif label in dos_data:
            y_up = dos_data[label]
            y_dw = np.zeros_like(raw_energy)
        else:
            y_up = np.zeros_like(raw_energy)
            y_dw = np.zeros_like(raw_energy)

        if has_spin and np.any(y_dw):
            ax.plot(plot_energy, y_up, lw=1.5, c=color, label=label)
            ax.plot(plot_energy, -y_dw, lw=1.5, c=color)
            ax.fill_between(plot_energy, 0, y_up, color=color, alpha=0.2)
            ax.fill_between(plot_energy, 0, -y_dw, color=color, alpha=0.2)

            if np.any(mask_view):
                y_max_trackers.extend(
                    [y_up[mask_view].max(), np.abs(y_dw[mask_view]).max()]
                )
        else:
            ax.plot(plot_energy, y_up, lw=1.5, c=color, label=label)
            ax.fill_between(plot_energy, 0, y_up, color=color, alpha=0.2)
            if np.any(mask_view):
                y_max_trackers.append(y_up[mask_view].max())

    # ---------------- 4. Final Formatting ----------------
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

    # --- NEW: Independent Legend Font Size ---
    ax.legend(
        loc=LEGEND_LOC, frameon=False, fontsize=LEGEND_FONT_SIZE, ncol=LEGEND_NCOL
    )

    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    plt.tight_layout()
    plt.show()

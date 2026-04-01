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

# --- 5. Font Configuration ---
FONT_SIZE = 14  # 统一字体大小 (坐标轴标签、刻度、图例)
FONT_FAMILY = "Arial"  # 字体家族
FONT_BOLD = False  # True: 字体加粗 (坐标轴、图例)
MATHTEXT_ENABLED = False  # True: 启用 mathtext 自定义字体

# --- Global Style Settings ---
mpl.rcParams["font.family"] = FONT_FAMILY
mpl.rcParams["axes.unicode_minus"] = False

if FONT_BOLD:
    mpl.rcParams["font.weight"] = "bold"
    mpl.rcParams["axes.labelweight"] = "bold"

if MATHTEXT_ENABLED:
    mpl.rcParams["mathtext.fontset"] = "custom"
    mpl.rcParams["mathtext.rm"] = FONT_FAMILY
    mpl.rcParams["mathtext.it"] = f"{FONT_FAMILY}:italic"
    mpl.rcParams["mathtext.bf"] = f"{FONT_FAMILY}:bold"

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

    dos_up = np.array(dos_data["up"])
    has_spin = "down" in dos_data and np.any(dos_data["down"])
    dos_dw = np.array(dos_data["down"]) if has_spin else None

    # ---------------- 2. Label Processing & Color Setup ----------------
    ignore_keys = ["energies", "fermi_energy", "up", "down"]
    raw_labels = list(
        set(
            [
                k.replace("_up", "").replace("_down", "")
                for k in dos_data.keys()
                if k not in ignore_keys
            ]
        )
    )

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

        y_up = dos_data.get(f"{label}_up", np.zeros_like(raw_energy))
        y_dw = dos_data.get(f"{label}_down", np.zeros_like(raw_energy))

        if has_spin:
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
    ax.set_xlabel(xlabel_text, fontsize=FONT_SIZE)
    ax.set_ylabel("Density of states (states/eV)", fontsize=FONT_SIZE)
    # ax.set_ylabel(r'Density of states/states$\cdot$eV$^{-1}$', fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)

    ax.legend(loc=LEGEND_LOC, frameon=False, fontsize=FONT_SIZE, ncol=LEGEND_NCOL)

    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    plt.tight_layout()
    plt.show()

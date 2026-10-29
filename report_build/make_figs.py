import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from model import storage_bits, cycles_for

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

BLUE, BLUE_E = "#DCEBF8", "#2F6DA8"
YEL, YEL_E = "#FFF4CC", "#B8860B"
PUR, PUR_E = "#EADCF4", "#7A4EA3"
GRN, GRN_E = "#DDF0DD", "#3C8A3C"
RED, RED_E = "#FBE3E0", "#C0392B"
GRY, GRY_E = "#F0F0F0", "#808080"


def box(ax, x, y, w, h, text, fc, ec, fs=9, ls="-", bold=False, lw=1.3):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                       fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p0, p1, color="#333333", ls="-", style="-|>", rad=0.0, lw=1.3, text=None, tpos=None, fs=7.5):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=11, color=color, lw=lw, ls=ls,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if text:
        tx, ty = tpos if tpos else ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.08)
        ax.text(tx, ty, text, ha="center", va="center", fontsize=fs, color="#222222")


def fig_workflow():
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    ax.text(0.1, 6.35, "Implemented flow (this report)", fontsize=10, fontweight="bold", color=BLUE_E)
    row1 = [
        ("1. Problem formulation\ny = Ax, pruning,\nCSR data modelling", BLUE, BLUE_E),
        ("2. SystemVerilog RTL\nbram_bank, mac_unit,\ncontroller, top", BLUE, BLUE_E),
        ("3. Behavioural simulation\ntb_mac_unit,\ntb_sparse_cim_top", BLUE, BLUE_E),
    ]
    xs = [0.1, 3.6, 7.1]
    for (t, fc, ec), x in zip(row1, xs):
        box(ax, x, 4.55, 2.8, 1.45, t, fc, ec, fs=9)
    arrow(ax, (2.95, 5.27), (3.55, 5.27))
    arrow(ax, (6.45, 5.27), (7.05, 5.27))
    box(ax, 7.1, 2.75, 2.8, 1.45, "4. Vivado OOC synthesis\nxc7z020clg484-1\n(LUT / FF / BRAM / DSP)", GRN, GRN_E)
    box(ax, 3.6, 2.75, 2.8, 1.45, "5. Characterisation\nutilisation, timing\n(10.32 ns), vectorless power", GRN, GRN_E)
    box(ax, 0.1, 2.75, 2.8, 1.45, "6. Documentation\niSES paper and\nminor project report", YEL, YEL_E)
    arrow(ax, (8.5, 4.5), (8.5, 4.25))
    arrow(ax, (7.05, 3.47), (6.45, 3.47))
    arrow(ax, (3.55, 3.47), (2.95, 3.47))
    ax.text(0.1, 2.25, "System-integration roadmap (Chapter 3.20 - 3.23 and Chapter 6)", fontsize=10,
            fontweight="bold", color=RED_E)
    rd = ["Multi-row CSR FSM\n+ self-checking TB", "AXI4-Lite IP\npackaging", "Block design\nZynq PS + PL",
          "Bitstream, .xsa\nexport", "Vitis C driver\n+ board test"]
    for i, t in enumerate(rd):
        x = 0.1 + i * 2.0
        box(ax, x, 0.45, 1.6, 1.2, t, RED, RED_E, fs=8, ls="--")
        if i < 4:
            arrow(ax, (x + 1.64, 1.05), (x + 1.96, 1.05), color=RED_E, ls="--")
    fig.savefig(os.path.join(OUT, "gen_fig_workflow.png"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_soc():
    fig, ax = plt.subplots(figsize=(9, 6.4))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8)
    ax.axis("off")
    # PS
    box(ax, 0.1, 0.4, 3.1, 7.2, "", "#F7F7FB", PUR_E, lw=1.6)
    ax.text(1.65, 7.3, "Processing System (PS)", ha="center", fontsize=10, fontweight="bold", color=PUR_E)
    box(ax, 0.35, 5.5, 2.6, 1.3, "Dual ARM Cortex-A9\n(bare-metal / PetaLinux)", PUR, PUR_E, fs=8.5)
    box(ax, 0.35, 3.85, 2.6, 1.2, "M_AXI_GP0 master\n(0x4000_0000 window)", PUR, PUR_E, fs=8.5)
    box(ax, 0.35, 2.4, 2.6, 1.0, "DDR3 controller\n(program / CSR image)", PUR, PUR_E, fs=8.5)
    box(ax, 0.35, 0.7, 2.6, 1.2, "FCLK_CLK0, FCLK_RESET0_N,\nIRQ_F2P", PUR, PUR_E, fs=8)
    # interconnect
    box(ax, 3.7, 3.55, 1.1, 1.8, "AXI\nInter-\nconnect", YEL, YEL_E, fs=9)
    arrow(ax, (2.98, 4.45), (3.68, 4.45), text="AXI4", tpos=(3.33, 4.7))
    # PL
    box(ax, 5.3, 0.4, 5.6, 7.2, "", "#F5FAF5", GRN_E, lw=1.6)
    ax.text(8.1, 7.3, "Programmable Logic (PL)", ha="center", fontsize=10, fontweight="bold", color=GRN_E)
    box(ax, 5.55, 5.2, 2.0, 1.7, "AXI4-Lite slave\nwrapper: CTRL, STATUS,\nNNZ, ROW, RESULT\n(done -> IRQ_F2P)", BLUE, BLUE_E, fs=7.6)
    box(ax, 5.55, 2.9, 2.0, 1.7, "AXI BRAM\nController(s)\n+ BRAM port mux", BLUE, BLUE_E, fs=8.2)
    box(ax, 8.55, 5.2, 2.15, 1.7, "sparse_cim_top\n(Sparse-CIM PE)\ncontroller + mac_unit", GRN, GRN_E, fs=8.2, bold=True)
    box(ax, 8.55, 0.7, 2.15, 3.55, "", GRY, GRY_E)
    ax.text(9.62, 3.95, "True dual-port BRAM", ha="center", fontsize=7.8, fontweight="bold")
    for i, t in enumerate(["bank_values", "bank_col_idx", "bank_vector"]):
        box(ax, 8.7, 2.85 - i * 0.98, 1.85, 0.75, t + "\n(RAMB18E1)", "white", GRY_E, fs=7.8)
    arrow(ax, (4.82, 4.7), (5.53, 5.9))
    arrow(ax, (4.82, 4.2), (5.53, 3.8))
    arrow(ax, (7.57, 6.35), (8.53, 6.35))
    ax.text(8.05, 6.6, "start, nnz", ha="center", fontsize=7)
    arrow(ax, (8.53, 5.65), (7.57, 5.65))
    ax.text(8.05, 5.35, "done, result", ha="center", fontsize=7)
    arrow(ax, (7.57, 3.75), (8.68, 2.5), text="Port B (write)", tpos=(7.85, 3.25), fs=7)
    arrow(ax, (9.62, 5.18), (9.62, 4.28))
    ax.text(10.05, 4.72, "Port A\n(read)", ha="left", fontsize=7)
    arrow(ax, (2.98, 1.3), (5.28, 1.3), ls="--", color="#555555", text="clk, rst_n", tpos=(4.1, 1.55))
    fig.savefig(os.path.join(OUT, "gen_fig_soc.png"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_storage():
    M = N = 64
    sp = [50, 60, 70, 80, 90, 95]
    dense, csr8, csrmin, coo = [], [], [], []
    for s in sp:
        nnz = round(M * N * (100 - s) / 100)
        d = storage_bits(M, N, nnz)
        dense.append(d["dense"] / 8 / 1024)
        csrmin.append(d["csr"] / 8 / 1024)
        coo.append(d["coo"] / 8 / 1024)
        csr8.append((nnz * 8 + nnz * 8 + (M + 1) * 16) / 8 / 1024)
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    w = 0.2
    xs = range(len(sp))
    ax.bar([x - 1.5 * w for x in xs], dense, w, label="Dense", color="#9DB7D5", edgecolor="#2F6DA8")
    ax.bar([x - 0.5 * w for x in xs], coo, w, label="COO (minimum-width indices)", color="#F2D88C", edgecolor="#B8860B")
    ax.bar([x + 0.5 * w for x in xs], csrmin, w, label="CSR (minimum-width indices)", color="#A9D6A9", edgecolor="#3C8A3C")
    ax.bar([x + 1.5 * w for x in xs], csr8, w, label="CSR (byte-wide index banks)", color="#D9B8EA", edgecolor="#7A4EA3")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{s}%" for s in sp])
    ax.set_xlabel("Sparsity (fraction of zero weights)")
    ax.set_ylabel("Storage (KiB)")
    ax.set_title("Storage of a 64 x 64 INT8 weight tile", fontsize=10)
    for i, v in enumerate(csrmin):
        ax.text(i + 0.5 * w, v + 0.05, f"{v:.1f}", ha="center", fontsize=7)
    ax.legend(fontsize=7.5, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(os.path.join(OUT, "gen_fig_storage.png"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_speedup():
    M = N = 64
    sp = list(range(50, 100, 5))
    fsm, pip = [], []
    for s in sp:
        nnz = round(M * N * (100 - s) / 100)
        fsm.append((3 * M * N + 2) / cycles_for(nnz))
        pip.append((M * N) / cycles_for(nnz))
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.plot(sp, fsm, "-o", color="#2F6DA8", label="vs. dense scan on the same 3-cycle PE", ms=4)
    ax.plot(sp, pip, "-s", color="#C0392B", label="vs. ideal 1-MAC/cycle dense engine", ms=4)
    ax.axhline(1.0, color="#777777", ls="--", lw=1)
    ax.set_xlabel("Sparsity (%)")
    ax.set_ylabel("Cycle-count speedup (x)")
    ax.set_title("Latency speedup of the zero-skipping PE, 64 x 64 tile", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25)
    fig.savefig(os.path.join(OUT, "gen_fig_speedup.png"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig_workflow()
    fig_soc()
    fig_storage()
    fig_speedup()
    print("figures written to", OUT)

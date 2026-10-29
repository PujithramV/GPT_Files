"""Chapters 4, 5, 6 and back matter."""
import os
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from content_b import sv, FIG
from model import simulate, cycles_for, storage_bits, clog2
from refs import REFS

NAME = "Vemana Venkata Pujithram"
REG = "230907016"
T0 = 75  # ns: first cycle with start = 1 in the directed testbench (read from the waveform)
F_MAX = 1000.0 / 10.32  # MHz


def chapter4(R):
    R.chapter("Contribution of Student")
    R.p("This is an individual project. All work packages below were carried out by "
        f"<b>{NAME} ({REG})</b> under the guidance of Dr. Rahul Ratnakumar.")
    R.h2(f"4.1 Problem formulation, CSR data modelling, and near-memory architecture design ({NAME} — {REG})")
    R.p("The first work package defined the engineering problem and the architecture. It comprised the "
        "literature study of sparse accelerators (EIE, SCNN, GraphLily, SERPENS, Cerberus and the INT8 FPGA "
        "and MAC references), the choice of CSR as the storage format on the basis of the storage and "
        "dataflow analysis of Section 3.4, and the decision to realise the in-memory-computing idea as "
        "BRAM-centric near-memory computing because analog bit-line access is not available on a "
        "commercial FPGA (Section 3.5). It also fixed the numerical design point (INT8 operands, 16-bit "
        "exact product, 32-bit accumulator), the three-bank memory organisation with dedicated read and "
        "write ports, and the controller schedule. Deliverables: the mathematical models of Sections 3.4 and "
        "3.6, the architecture of Figure 3.3 and the cycle model of Section 3.11.")
    R.h2(f"4.2 SystemVerilog RTL design of the BRAM banks, sparsity controller FSM, and INT8 MAC datapath "
         f"({NAME} — {REG})")
    R.p("The second work package was the RTL implementation. It produced the four synthesisable modules: the "
        "parameterised dual-port <c>bram_bank</c> with the <c>ram_style = \"block\"</c> attribute, the "
        "five-state <c>sparse_cim_controller</c> with latch-free default assignments and the indirect "
        "vector-address path, the signed <c>mac_unit</c> with the reset/clear/enable priority and the "
        "sign-preserving 32-bit cast, and the top-level <c>sparse_cim_top</c> that integrates them with the "
        "backdoor Port B preload interface. Deliverables: the four source files listed in Chapter 3, "
        "together with the scaling framework (six-state multi-row controller) specified in Section 3.10.")
    R.h2(f"4.3 Functional verification and directed testbench development ({NAME} — {REG})")
    R.p("The third work package was verification. It comprised the MAC unit testbench (signed multiply, enable "
        "gating, clear), the top-level testbench (Port B preload with the vector-address pause, start/done "
        "handshake, wait-for-done synchronisation), the construction of the expected results "
        "5(3) + (−4)(2) = 7, and the interpretation of the Vivado Simulator waveform (Figure 5.1). It "
        "also defined the self-checking scoreboard and regression extension of Section 3.16 and the "
        "acceptance checks of Table 3.7.")
    R.h2(f"4.4 Vivado synthesis, area/resource utilization, timing, and power analysis ({NAME} — {REG})")
    R.p("The fourth work package was hardware characterisation. It comprised out-of-context synthesis on "
        "the Zynq-7000 <c>xc7z020clg484-1</c> device, extraction and interpretation of the utilisation "
        "report (154 LUTs, 41 FDCE flip-flops, 3 RAMB18E1, 0 DSP48E1), the critical-path delay "
        "(10.32 ns), the vectorless power estimate (4.502 W), the throughput and speedup models of Section "
        "5.9, and the comparison with published accelerators. The results were consolidated into the IEEE "
        "iSES conference paper and into this report.")


def _trace_table(R):
    tr = simulate([5, -4], [0, 2], [3, 0, 2], 2)
    rows = []
    for t in tr[:11]:
        st = t["state"]
        vv = str(t["val_data"]) if st in ("FETCH_VEC", "COMPUTE") else "–"
        cc = str(t["col_data"]) if st in ("FETCH_VEC", "COMPUTE") else "–"
        vd = str(t["vec_data"]) if st == "COMPUTE" else "–"
        vaddr = str(t["vec_addr"]) if st == "FETCH_VEC" else "–"
        rows.append([str(t["cycle"]), str(T0 + 10 * t["cycle"]), st.replace("_", "_​"),
                     str(t["ptr"]) if st not in ("IDLE",) else "0",
                     vv, cc, vaddr, vd, str(t["mac_en"]),
                     str(t["product"]) if t["mac_en"] else "–",
                     str(t["acc"]), str(t["done"])])
    R.table("Cycle-by-cycle simulation values for the directed test (5 × 3 + (−4) × 2); "
            "<i>t</i> is the start time of each 10 ns cycle",
            ["Cyc.", "<i>t</i> (ns)", "FSM state", "ptr", "val", "col", "vaddr", "vdata",
             "en", "prod.", "result", "done"],
            rows, [0.4, 0.5, 1.05, 0.4, 0.45, 0.45, 0.55, 0.55, 0.4, 0.5, 0.55, 0.45], size=8.5,
            aligns=["c"] * 12)
    R.p("Column key: val = <c>val_data</c>, col = <c>col_data</c>, vaddr = <c>vec_addr</c>, vdata = "
        "<c>vec_data</c>, en = <c>mac_en</c>, prod. = product, result = <c>final_result</c>; \u2013 means the "
        "signal carries no valid new value in that cycle.", size=10.5)
    return tr


def chapter5(R):
    R.chapter("Result Analysis")

    # ---------------------------------------------------------------- 5.1
    R.h2("5.1 Functional simulation results")
    R.p("Figure 5.1 shows the behavioural simulation of <c>tb_sparse_cim_top</c> in the Vivado Simulator. "
        "The waveform shows, from left to right, the reset release at 20 ns, the Port B preload (the "
        "<c>web_val</c>, <c>web_col</c> and <c>web_vec</c> pulses between 25 and 55 ns, with <c>addrb</c> "
        "stepping 0, 1, 2), the application of <c>nnz_count</c> = 2 and <c>start</c> = 1 at 75 ns, the "
        "accumulation of <c>final_result</c> from 0 to 15 (at 115 ns) and to 7 (at 145 ns), the "
        "two-cycle assertion of <c>done</c> from 145 to 165 ns, and the return of <c>final_result</c> to 0 "
        "at 175 ns when the FSM has returned to IDLE and cleared the accumulator.")
    R.figure(os.path.join(FIG, "ises_fig5.png"), "Behavioural simulation of the top module (from the iSES "
             "paper): BRAM preload, FSM zero-skipping sequence and accumulation 0 → 15 → 7", 6.27)
    R.p("Table 5.1 reconstructs the same run cycle by cycle from the semantics of the RTL (a cycle-accurate "
        "reference model of the controller, BRAM read latency and MAC), with <i>t</i> measured from the "
        "75 ns start of the testbench. Its <c>final_result</c> column reproduces the 0 → 15 → 7 → 0 "
        "sequence of the waveform at 115, 145 and 175 ns, which cross-checks the reconstruction.")
    tr = _trace_table(R)
    R.p("The table can be read as follows. <b>Cycle 0 (IDLE)</b>: <c>start</c> and <c>nnz_count</c> = 2 are "
        "present; <c>mac_clr</c> keeps the accumulator at 0. <b>Cycles 1–3 (first non-zero)</b>: in "
        "FETCH_PTR the address 0 is applied; in FETCH_VEC the weight 5 and column 0 have arrived and "
        "<c>vec_addr</c> = 0 is issued; in COMPUTE <c>vec_data</c> = 3 has arrived, the product is 15 and "
        "<c>mac_en</c> = 1, so <c>final_result</c> becomes 15 at the end of the cycle. <b>Cycles 4–6 "
        "(second non-zero)</b>: pointer 1 is fetched; the weight is −4 (stored as 0xFC) and the column "
        "is 2, so <c>vec_addr</c> = 2 and <c>vec_data</c> = 2; the product is −8 and "
        "<c>final_result</c> becomes 7. <b>Cycle 7 (DONE_STATE)</b>: <c>done</c> = 1 and the result 7 is "
        "valid. <b>Cycle 8</b>: the testbench has lowered <c>start</c>, so the FSM leaves DONE_STATE at "
        "the end of the cycle; <b>cycle 9 (IDLE)</b> asserts the clear and <b>cycle 10</b> shows the "
        "accumulator at 0. The total from the first IDLE cycle to the first DONE_STATE cycle is 8 cycles, "
        "equal to 3·2 + 2.")
    R.p("For reference, the two code fragments that govern this run are re-listed below with their original "
        "line numbers: the COMPUTE branch of the controller, and the run phase of the testbench.")
    ctrl = sv("sparse_cim_controller.sv").split("\n")
    tbt = sv("tb_sparse_cim_top.sv").split("\n")
    R.code("sparse_cim_controller.sv, lines 105–117: COMPUTE state (excerpt)", "\n".join(ctrl[104:117]),
           start=105)
    R.code("tb_sparse_cim_top.sv, lines 76–91: run phase and observation window (excerpt)",
           "\n".join(tbt[75:91]), start=76)

    # ---------------------------------------------------------------- 5.2
    R.h2("5.2 Interpretation of functional correctness and coverage")
    R.p("The simulation establishes five properties of the design. <b>(i) Preload correctness:</b> the "
        "operands written through Port B are the operands read by Port A, at the addresses the controller "
        "generates. <b>(ii) Indirect addressing:</b> the second non-zero has column index 2, and the "
        "vector element used is <i>x</i>[2] = 2, not the sequentially next element; a design that did not "
        "route <c>col_data</c> into <c>vec_addr</c> would produce a different sum. <b>(iii) Signed "
        "arithmetic:</b> the negative weight yields a negative product and the accumulator decreases from "
        "15 to 7. <b>(iv) Control sequencing:</b> the FSM visits FETCH_PTR, FETCH_VEC and COMPUTE twice, "
        "once per non-zero, raises <c>done</c> immediately after the last accumulation, and clears the "
        "accumulator after <c>start</c> falls. <b>(v) Completion handshake:</b> <c>done</c> is held while "
        "<c>start</c> is high and released when it falls.")
    R.p("In terms of coverage, the directed tests exercise all five FSM states, the transitions "
        "IDLE → FETCH_PTR, FETCH_PTR → FETCH_VEC → COMPUTE, both COMPUTE exits "
        "(loop back to FETCH_PTR for the first non-zero, exit to DONE_STATE for the last) and "
        "DONE_STATE → IDLE; both signs of the product; all three arithmetic control states of the "
        "MAC (accumulate, hold, clear) and the reset. The coverage space that the planned scoreboard "
        "regression of Section 3.16 adds consists of randomised column indices and operand values, "
        "<c>nnz_count</c> from 1 to 63, multiple back-to-back invocations and the guard "
        "<c>nnz_count</c> = 0, together with automatic checking of the 3·NNZ + 2 latency.")

    # ---------------------------------------------------------------- 5.3
    R.h2("5.3 Signed arithmetic and accumulator correctness")
    R.p("The test vector (5, 3) followed by (−4, 2) exercises the following behaviour of the "
        "datapath. The weight −4 is stored as the byte 0xFC (two's complement). The multiplier sees "
        "the signed value −4, and the 16-bit product with 2 is 0xFFF8 = −8. The size cast "
        "<c>32'(product)</c> sign-extends it to 0xFFFFFFF8, and the 32-bit addition "
        "0x0000000F + 0xFFFFFFF8 = 0x00000007 (with the carry out of bit 31 discarded) equals 7. The "
        "accumulator therefore behaves as a two's-complement integer and no special handling of negative "
        "products is required.")
    R.p("<b>Overflow bounds.</b> The largest product magnitude is |−128 · −128| = 16,384 = "
        "2<sup>14</sup> and the 16-bit product, whose range is [−32,768, 32,767], never overflows. "
        "For the accumulator, after <i>k</i> accumulations |acc| ≤ <i>k</i> · 2<sup>14</sup>, "
        "which stays below 2<sup>31</sup> while")
    R.eq("<i>k</i> < 2<sup>31</sup> / 2<sup>14</sup> = 2<sup>17</sup> = 131,072")
    R.p("The 6-bit instance processes at most 63 non-zeros per invocation (|acc| ≤ 1,032,192 "
        "< 2<sup>20</sup>), so the 32-bit register has more than 11 unused bits of headroom; even the "
        "11-bit instance with 2,047 non-zeros (|acc| ≤ 33.5 million < 2<sup>25</sup>) retains six. "
        "The 32-bit width, equal to the width of the result port, thus guarantees overflow-free "
        "accumulation for any layer tile addressable by the banks, at a cost of 32 flip-flops.")

    # ---------------------------------------------------------------- 5.4
    R.h2("5.4 Storage footprint and compression efficiency")
    M = N = 64
    parts = []
    for s in (50, 70, 90, 95):
        nnz = round(M * N * (100 - s) / 100)
        d = storage_bits(M, N, nnz)
        parts.append((s, nnz, d))
    R.p("Using the expressions of Section 3.4 for a 64 × 64 INT8 tile (<i>b</i><sub><i>v</i></sub> = 8, "
        "<i>b</i><sub><i>c</i></sub> = <i>b</i><sub><i>r</i></sub> = 6), the dense footprint is "
        f"{M*N*8:,} bits (4.00 KiB) independent of sparsity, whereas the CSR footprint with minimum-width "
        "indices is "
        + "; ".join(f"{d['csr']:,} bits ({d['csr']/8/1024:.2f} KiB) at {s} % sparsity (NNZ = {nnz})"
                    for s, nnz, d in parts)
        + ". The corresponding compression ratios relative to dense are "
        + ", ".join(f"{d['dense']/d['csr']:.1f}×" for s, nnz, d in parts)
        + " respectively. Figure 5.2 compares the four formats; the COO footprint exceeds CSR at every "
        "sparsity because of its per-element row index, and the break-even of Section 3.4 is visible at "
        "50 % sparsity, where COO is larger than dense and CSR is only 10 % smaller.")
    R.figure(os.path.join(FIG, "gen_fig_storage.png"), "Storage of a 64 × 64 INT8 weight tile for Dense, COO "
             "and CSR formats versus sparsity", 5.2)
    ratios = []
    for s_ in (50, 60, 70, 80, 90, 95):
        n_ = round(M * N * (100 - s_) / 100)
        ratios.append((n_ * 16 + (M + 1) * 16) / storage_bits(M, N, n_)["csr"] * 100 - 100)
    lo, hi = min(ratios), max(ratios)
    R.p("The byte-wide index banks of the implementation (<c>DATA_WIDTH</c> = 8 for the column index and "
        f"for the pointer) cost between {lo:.0f} % and {hi:.0f} % more than the minimum-width bound, as the right-hand "
        "bar of each group shows. This is a deliberate simplification: the BRAM word is 8 bits wide in "
        "any case, since a RAMB18E1 is organised in 9-bit-wide words and the extra bits would be unused. "
        "The saving of the on-chip memory is therefore best expressed in <i>words read</i> (Table 3.3) "
        "rather than in minimum-width bits.")

    # ---------------------------------------------------------------- 5.5
    R.h2("5.5 FPGA utilization and architectural bottlenecks")
    R.p("Table 5.2 reproduces the post-synthesis resource utilisation of the accelerator on the "
        "<c>xc7z020clg484-1</c> device (out-of-context synthesis), with percentages computed against the "
        "device inventory.")
    R.table("FPGA resource utilisation of the Sparse-CIM core on the Zynq-7000 (xc7z020clg484-1)",
            ["Resource", "Utilisation", "Available", "Utilisation (%)"],
            [["Slice LUTs", "154", "53,200", "0.29"],
             ["Slice Registers (FDCE)", "41", "106,400", "0.04"],
             ["Block RAM (RAMB18E1)", "3", "280", "1.07"],
             ["DSP48E1 slices", "0", "220", "0.00"]],
            [2.4, 1.1, 1.1, 1.67], size=10.5, aligns=["l", "r", "r", "r"])
    R.p("The core occupies under 0.3 % of the LUTs, 0.04 % of the flip-flops and about 1 % of the block "
        "RAMs, and no DSP slices. The 41 registers decompose exactly as 32 (accumulator) + 6 (pointer) + 3 "
        "(state) (Section 3.17), and the 3 RAMB18E1 are the three operand banks.")
    R.h3("Multi-PE parallel scaling")
    R.p("Because the engine is so small, the device can host many PEs, each with its own three banks. The "
        "number of PEs that fit is bounded by the scarcest resource:")
    luts, ffs, brams = 53200, 106400, 280
    R.bullets([
        f"LUTs: ⌊{luts}/154⌋ = {luts//154} PEs;",
        f"flip-flops: ⌊{ffs}/41⌋ = {ffs//41} PEs;",
        f"RAMB18E1 (one per bank, three per PE): ⌊{brams}/3⌋ = {brams//3} PEs;",
        "DSP48E1: not a constraint (0 per PE).",
    ])
    npe = brams // 3
    R.p(f"Block RAM is therefore the binding resource: {npe} PEs would use {npe*154:,} LUTs "
        f"({npe*154/luts*100:.1f} %), {npe*41:,} flip-flops ({npe*41/ffs*100:.1f} %) and {npe*3} RAMB18E1 "
        f"({npe*3/brams*100:.1f} %). Each bank uses only 512 of the 2,048 words (9-bit) of its primitive, so "
        "address-partitioned sharing of a primitive between the banks of several PEs is available if more "
        "PEs are wanted, at the cost of port arbitration; alternatively the same three primitives per PE can "
        "hold up to 32× larger tiles (<c>ADDR_WIDTH</c> = 11) at no area cost. Under ideal linear scaling "
        f"(independent PEs on independent rows, ignoring routing congestion and clock degradation) the aggregate "
        f"effective throughput would be about {npe} × 0.64 ≈ {npe*0.644:.0f} GOPS-equivalent at "
        "90 % sparsity; this is a projection, not a measurement.")
    R.p("The architectural bottlenecks of a single PE are, in order: (i) the 3-cycle-per-non-zero schedule, "
        "which limits one PE to <i>f</i>/3 MACs per second; (ii) the single MAC per PE; (iii) the "
        "combinational multiplier-plus-adder path that sets <i>T</i><sub>crit</sub> = 10.32 ns; and "
        "(iv) the single read port per bank on Port A. Each is addressed by a localised change "
        "(overlapped fetch, parallel MAC lanes with banked indices, a product register, and bank "
        "replication respectively) that preserves the architecture.")

    # ---------------------------------------------------------------- 5.6
    R.h2("5.6 Timing results and their scope")
    R.table("Timing results and derived quantities (post-synthesis, out-of-context)",
            ["Quantity", "Value", "Remark"],
            [["Critical path delay <i>T</i><sub>crit</sub>", "10.32 ns", "Longest register-to-register path (post-synthesis)"],
             ["Maximum frequency <i>F</i><sub>max</sub>", f"≈ {F_MAX:.2f} MHz", "1 / 10.32 ns"],
             ["Simulation clock", "100 MHz (10 ns)", "Behavioural simulation only; not a constraint"],
             ["Slack at <i>T</i><sub>clk</sub> = 10.5 ns", "+0.18 ns", "95.2 MHz target"],
             ["Slack at <i>T</i><sub>clk</sub> = 10.0 ns", "−0.32 ns", "Would need the pipelining step below"],
             ["Time per non-zero at <i>F</i><sub>max</sub>", f"{3*10.32:.2f} ns", "3 cycles × 10.32 ns"],
             ["Non-zero rate at <i>F</i><sub>max</sub>", f"{F_MAX/3:.2f} M non-zeros/s", "<i>F</i><sub>max</sub> / 3"]],
            [2.3, 1.5, 2.47], size=10)
    R.p("The reported delay is the post-synthesis figure for the out-of-context core: it includes the "
        "logic delay and the synthesis tool's estimate of net delay, and it does not include the "
        "placed-and-routed interconnect of a full system. It is therefore the appropriate number for "
        "comparing micro-architectures and for planning the clock constraint, and the implementation of "
        "the integrated design (Section 3.18) will refine it.")
    R.p("<b>Pipeline-optimisation avenues.</b> The 10.32 ns path comprises, in series, the BRAM clock-to-output "
        "delay, the controller's operand gating, the 8 × 8 LUT multiplier and the 32-bit carry-chain "
        "accumulate. Three independent register insertions shorten it: (a) a 16-bit product register after "
        "the multiplier, splitting multiply from accumulate; (b) registering <c>mac_weight</c>/<c>mac_act</c> "
        "after the gating; (c) enabling the optional output register of the RAMB18E1 [@ug473], which "
        "reduces the clock-to-output delay at the cost of one extra read-latency cycle. Each adds one pipeline "
        "stage and a small number of flip-flops (16, 16, and 8 per bank respectively) and shifts the "
        "bottleneck to the next-longest stage; combined with the overlapped schedule of Section 3.11 the "
        "engine reaches one non-zero per cycle at a clock considerably above 100 MHz.")

    # ---------------------------------------------------------------- 5.7
    R.h2("5.7 Estimated power and characterization analysis")
    R.p("Figure 5.3 shows the post-synthesis out-of-context power summary produced by Vivado, and Table "
        "5.4 tabulates it. The estimate is <i>vectorless</i>: it is derived from the synthesised netlist "
        "and from the tool's default switching-activity assumptions, without simulation activity data "
        "[@ug907]. The report itself marks the confidence level as <i>Low</i>, which is the expected "
        "classification for any pre-implementation, vectorless estimate.")
    R.figure(os.path.join(FIG, "ises_fig6.png"), "Post-synthesis out-of-context power estimate (from the "
             "iSES paper): total on-chip power 4.502 W", 4.5)
    R.table("Vectorless post-synthesis power estimate (xc7z020clg484-1, out-of-context)",
            ["Component", "Power (W)", "Share"],
            [["<b>Total on-chip power</b>", "<b>4.502</b>", "100 %"],
             ["Dynamic power", "4.235", "94 % of total"],
             [" Signals", "1.917", "45 % of dynamic"],
             [" Logic", "1.994", "47 % of dynamic"],
             [" BRAM", "0.323", "8 % of dynamic"],
             ["Device static power", "0.268", "6 % of total"],
             ["Junction temperature / thermal margin", "76.9 °C / 8.1 °C (0.7 W)", "θ<sub>JA</sub> = 11.5 °C/W"],
             ["Confidence level", "Low", "Vectorless estimate"]],
            [2.6, 1.9, 1.77], size=10, aligns=["l", "r", "r"])
    R.p("<b>Reading the estimate constructively.</b> A vectorless analysis assigns a default toggle rate "
        "and static probability to every net that has no simulated activity, so the result is an "
        "<i>envelope</i>: it bounds the power of a design whose nets are all assumed to be switching at "
        "the default rate, rather than the power of a specific inference. Under this model the "
        "distribution is informative. Signals (routing) and logic together account for 92 % of the dynamic "
        "power and the three RAMB18E1 only 8 % (0.323 W), which agrees with the architectural intent: the "
        "operand storage is cheap and the energy is spent where switching is assumed. The device static "
        "term, 0.268 W, is a property of the chosen silicon and is independent of the design.")
    R.p("The characterisation can be tightened in three ways that the existing RTL supports. First, "
        "<b>activity-annotated power</b>: exporting a SAIF or VCD file from the testbench simulation and reading "
        "it into the power analyser replaces default activity with the actual, mostly idle, toggling of an "
        "inference. Second, <b>activity-aware enables</b>: the MAC accumulator is already enable-gated; "
        "driving the Port A enable of each bank from the FSM state, instead of tying <c>ena</c> to 1 "
        "(Listing 3.1), suppresses BRAM reads in IDLE, DONE_STATE and the cycles that do not need a "
        "fetch. Third, <b>measurement</b> on a board (Section 5.8). The 4.502 W figure is also recorded in the "
        "iSES paper and in the comparison of Section 5.9, where its vectorless nature is noted.")

    # ---------------------------------------------------------------- 5.8
    R.h2("5.8 Hardware demonstration status and deployment boundary")
    R.p("The results of this report are RTL-level and post-synthesis results. The engine has been "
        "simulated (Section 5.1) and synthesised for the Zynq-7000 xc7z020clg484-1 (Sections 5.5–5.7). The "
        "step that remains is its deployment on a physical Zynq-7000 board, which proceeds exactly as "
        "specified in Sections 3.20–3.23: package the core with the AXI4-Lite wrapper, build the block "
        "design, export the XSA, run the driver of Listing 3.10 and compare the on-board result and "
        "cycle count with the simulation values of Table 5.1.")
    R.p("The boundary between the demonstrated and the roadmap items is therefore: <b>demonstrated</b> "
        "— correct signed accumulation with indirect addressing, the five-state schedule, the "
        "handshake, and the area/timing/power characterisation; <b>roadmap</b> — multi-row CSR "
        "sequencing, automatic checking, AXI integration and on-board measurement. When the board "
        "measurements are available, the figures of Chapter 5 gain three measured counterparts: the "
        "end-to-end latency (read from a hardware counter in the wrapper), the on-board power "
        "(from the board's power monitor) and the board-level correctness of repeated invocations.")

    # ---------------------------------------------------------------- 5.9
    R.h2("5.9 Latency, throughput, speedup, and architectural comparison")
    R.p("<b>Cycle-accurate latency.</b> Section 3.11 shows that every stored non-zero costs three cycles "
        "(FETCH_PTR, FETCH_VEC, COMPUTE), because the one-cycle synchronous read of <c>bank_col_idx</c> "
        "must complete before <c>vec_addr</c> can be issued to <c>bank_vector</c>, whose own one-cycle read "
        "must complete before the MAC can operate. Adding the IDLE cycle in which <c>start</c> is sampled "
        "and the DONE_STATE cycle in which <c>done</c> is visible,")
    R.eq("<i>T</i><sub>cycles</sub> = 1 + 3 · NNZ + 1")
    R.p("For the directed test, NNZ = 2 and <i>T</i> = 8, which Table 5.1 confirms (IDLE at cycle 0, "
        "DONE_STATE at cycle 7). The latency in time is <i>T</i><sub>time</sub> = <i>T</i><sub>cycles</sub> / "
        "<i>F</i>.")
    R.p("<b>Speedup.</b> Two baselines are meaningful. The first is a <i>dense scan on the same PE</i>, which "
        "visits all <i>MN</i> elements with the same three-cycle schedule: "
        "<i>T</i><sub>dense,3</sub> = 3<i>MN</i> + 2, so")
    R.eq("<i>S</i><sub>3</sub> = (3<i>MN</i> + 2) / (3 NNZ + 2) ≈ 1 / (1 − <i>s</i>)")
    R.p("The second is an <i>ideal pipelined dense engine</i> that performs one MAC per cycle, "
        "<i>T</i><sub>dense,1</sub> = <i>MN</i>, which is a demanding baseline because the sparse PE needs "
        "three cycles per non-zero: <i>S</i><sub>1</sub> = <i>MN</i> / (3 NNZ + 2) ≈ 1/(3(1 − "
        "<i>s</i>)). The sparse PE therefore overtakes the ideal dense engine when sparsity exceeds about "
        "67 % (<i>s</i> > 2/3), and the overlapped and pipelined schedules of Section 3.11 move this "
        "crossover to 50 % and below. Table 5.5 evaluates both for a 64 × 64 tile (<i>MN</i> = 4096) at "
        f"<i>F</i><sub>max</sub> = {F_MAX:.1f} MHz, together with the latency and the effective "
        "(dense-equivalent) throughput 2<i>MN</i>·<i>F</i>/<i>T</i>.")
    rows = []
    MNv = M * N
    for s in (50, 60, 70, 80, 90, 95):
        nnz = round(MNv * (100 - s) / 100)
        T = cycles_for(nnz)
        T3 = 3 * MNv + 2
        T1 = MNv
        lat = T / F_MAX
        gops = 2 * MNv * F_MAX * 1e6 / T / 1e9
        rows.append([f"{s} %", f"{nnz:,}", f"{T:,}", f"{lat:.2f}", f"{T3/T:.2f}×", f"{T1/T:.2f}×",
                     f"{gops:.3f}"])
    R.table("Latency, speedup and effective throughput versus sparsity (64 × 64 INT8 tile, "
            f"<i>F</i> = {F_MAX:.1f} MHz)",
            ["Sparsity", "NNZ", "<i>T</i> (cycles)", "Latency (µs)", "Speedup vs dense scan (3-cycle)",
             "Speedup vs ideal dense (1 MAC/cycle)", "Eff. GOPS"],
            rows, [0.7, 0.6, 0.85, 0.8, 1.15, 1.2, 0.97], size=9.5, aligns=["c"] * 7)
    R.figure(os.path.join(FIG, "gen_fig_speedup.png"), "Cycle-count speedup of the zero-skipping PE versus "
             "sparsity for a 64 × 64 tile (two baselines)", 5.0)
    R.p("(The 64 × 64 tile needs up to 2,048 non-zeros per invocation, i.e. the 11-bit instance of the "
        "parameterised design; the control flow and the equations are unchanged.)")
    R.p("<b>Throughput.</b> In steady state one PE performs one MAC (two operations: a multiply and an add) "
        f"per three cycles, i.e. 2<i>F</i>/3 = {2*F_MAX/3:.1f} MOPS of <i>useful</i> operations at "
        f"{F_MAX:.1f} MHz. The effective throughput compares the work of the dense equivalent with the time "
        "taken, 2<i>MN</i>·<i>F</i>/<i>T</i> ≈ 2<i>F</i> / (3(1 − <i>s</i>)), which at 90 % "
        f"sparsity is 2×{F_MAX:.1f} MHz / 0.3 = {2*F_MAX/0.3:.0f} MOPS ≈ 0.64 GOPS: this is the "
        "effective figure reported for the proposed Sparse-CIM in Table 5.6 and in the iSES paper, "
        "and the table above shows that it grows to more than 1.2 GOPS at 95 % sparsity. Normalised "
        f"by the vectorless power of 4.502 W this is about {0.644/4.502:.2f} effective GOPS/W; since the "
        "power figure is an envelope, this is a lower bound that the activity-annotated analysis of Section "
        "5.7 is expected to improve.")
    R.p("<b>Architectural comparison.</b> Table 5.6 reproduces the comparison of the iSES paper. The "
        "entries have different scopes and precisions (full systems with FP32/INT16/INT8, an ASIC MAC-only "
        "block, and the proposed FPGA core), so the table is read as a map of the design space rather than "
        "as a ranking.")
    R.table("Comparison with existing sparse accelerators and MAC architectures (from the iSES paper)",
            ["Architecture", "Scope / precision", "Area / LUTs", "Power (mW)", "Delay (ns)", "Throughput"],
            [["GraphLily [@hu2021]", "Full system / FP32", "390K LUTs", "43,000", "6.02", "35.8 GFLOPS"],
             ["SERPENS [@song2022]", "Full system / FP32", "173K LUTs", "48,000", "4.48", "60.5 GFLOPS"],
             ["Cerberus [@hwang2024]", "Full system / INT16", "30.1 mm<sup>2</sup>", "17,032", "1.00", "112.4 GOPS"],
             ["Zhang <i>et al.</i> [@zhang2024]", "Full system / INT8", "∼120K LUTs", "3,200", "N/A", "∼348 GOPS"],
             ["Abhiram <i>et al.</i> [@abhiram2024]", "MAC only / INT8", "2967 µm<sup>2</sup>", "0.507", "3.99", "N/A"],
             ["<b>Proposed Sparse-CIM</b>", "<b>Full system / INT8</b>", "<b>154 LUTs</b>", "<b>4,500</b>",
              "<b>10.32</b>", "<b>0.64 GOPS (Eff.)</b>"]],
            [1.55, 1.2, 0.95, 0.75, 0.6, 1.22], size=9)
    R.p("<b>Discussion.</b> Three observations follow. (i) <i>Area.</i> The proposed core uses 154 LUTs and "
        "no DSP slices, against 120K–390K LUTs for the FPGA systems; it is a PE, not a full-system "
        "accelerator, and its role is as the replicable building block (Section 5.5). (ii) <i>Power.</i> "
        "The 4.5 W figure is a vectorless envelope for the core, which compares with 17–48 W for the "
        "data-centre-class entries; the only entry in the same INT8-FPGA class, Zhang <i>et al.</i>, "
        "reports 3.2 W for a complete 348-GOPS Vision Transformer system, which shows that the "
        "efficiency of the proposed core depends on the activity-annotated refinement described in "
        "Section 5.7 and on replication. (iii) <i>Delay and throughput.</i> The 10.32 ns path and the "
        "three-cycle schedule give 0.64 effective GOPS per PE at 90 % sparsity, below the "
        "high-bandwidth systems; the pipelining avenues of Section 5.6 and multi-PE replication "
        "(≈ 93 PEs by block-RAM count) are the path to the hundreds-of-GOPS class. The "
        "design's distinguishing property is that it reaches its operating point with no DSP slices, no "
        "off-chip memory and a single-digit-percent fraction of a low-cost device.")

    # ---------------------------------------------------------------- 5.10
    R.h2("5.10 Measurement and characterization methodology")
    R.p("Every number in Chapter 5 has a defined origin. <b>Functional results</b> come from the Vivado "
        "Simulator run of the two testbenches; Table 5.1 is additionally reproduced by a cycle-accurate "
        "reference model whose agreement with the waveform at 115, 145 and 175 ns is described in Section 5.1. "
        "<b>Resource utilisation</b> is the post-synthesis utilisation report of the out-of-context core "
        "(LUTs, registers, block RAM and DSP counts). <b>Delay</b> is the post-synthesis critical-path delay of "
        "the same run. <b>Power</b> is the vectorless post-synthesis power report. <b>Latency, speedup and "
        "effective throughput</b> are analytical, computed from <i>T</i> = 3·NNZ + 2, the stated "
        "baselines and <i>F</i><sub>max</sub> = 1/10.32 ns. Listing 5.3 gives the Tcl flow that "
        "regenerates the synthesis-based numbers.")
    R.code("Vivado Tcl flow for the out-of-context characterisation",
"""read_verilog -sv {bram_bank.sv mac_unit.sv sparse_cim_controller.sv sparse_cim_top.sv}
synth_design -top sparse_cim_top -part xc7z020clg484-1 -mode out_of_context
report_utilization        -file util.rpt
report_timing_summary     -file timing.rpt
report_power              -file power.rpt          ;# vectorless: no SAIF/VCD attached""", numbered=False)
    R.p("The limits of the characterisation are stated alongside each figure: the delay and power are "
        "post-synthesis, out-of-context values; the power is a vectorless estimate with Low confidence; "
        "and throughput is an analytical figure for one PE. Section 5.11 lists the steps that turn each "
        "into a measured quantity.")

    # ---------------------------------------------------------------- 5.11
    R.h2("5.11 Architectural scalability priorities and verification roadmap")
    R.p("Table 5.7 organises the system-scaling enhancements of the architecture in the order in which "
        "they build on one another, together with the verification gate that marks the completion of each.")
    R.table("System-scaling enhancements and verification gates",
            ["Priority", "Enhancement", "Benefit", "Verification gate"],
            [["1", "Multi-row CSR FSM with <c>row_ptr</c> sequencing and result write-back (Section 3.10)",
              "Full matrix per invocation; <i>y</i> in on-chip bank", "4 × 4 example yields (13, 3, 12, 24); "
              "<i>T</i> = 3NNZ + 3<i>M</i> + 2"],
             ["2", "Self-checking scoreboard and randomised regression (Listing 3.8)",
              "Automatic pass/fail; latency assertion", "Zero mismatches over randomised CSR rows"],
             ["3", "AXI4-Lite wrapper and AXI BRAM controllers (Table 3.8)", "Processor-controlled operation",
              "Driver of Listing 3.10 passes in simulation and on board"],
             ["4", "Timing closure at the target clock (product/operand registers)", "<i>F</i> above 100 MHz",
              "Positive WNS in implemented design"],
             ["5", "Activity-annotated power (SAIF/VCD) and BRAM enable gating", "Realistic power; lower activity",
              "Power report with annotated activity"],
             ["6", "Zynq-7000 board deployment and measurement", "Measured latency and power",
              "On-board cycle count equals <i>T</i>"],
             ["7", "Multi-PE replication (up to ≈ 93 by BRAM count)", "Near-linear throughput scaling",
              "Aggregate GOPS versus PE count"],
             ["8", "Multi-precision arithmetic (INT16, FP16/BF16/FP32)", "Wider applicability",
              "Bit-exact against software reference"]],
            [0.6, 2.35, 1.6, 1.72], size=9)


def chapter6(R):
    R.chapter("Conclusion and Future Scope")
    R.h2("6.1 Summary of the work")
    R.p("This project designed, verified and characterised a sparsity-aware, BRAM-centric near-memory "
        "SpMVM accelerator for edge inference on an AMD/Xilinx Zynq-7000 SoC. The computation <i>y</i> = "
        "<i>A</i><i>x</i> over a pruned weight matrix is formulated in CSR, for which the storage, traffic and "
        "cycle models were derived. The architecture realises on an FPGA the near-memory counterpart of "
        "in-memory computing: a five-state zero-skipping FSM and a signed INT8 MAC with 32-bit accumulation "
        "sit directly at the synchronous read ports of three RAMB18E1-based banks that hold the "
        "compressed weights, the column indices and the dense vector. Simulation confirmed the signed "
        "accumulation 0 → 15 → 7 and the control handshake, and out-of-context synthesis on the "
        "xc7z020clg484-1 gave 154 LUTs, 41 flip-flops, 3 RAMB18E1, 0 DSP48E1, a 10.32 ns critical path and a "
        "4.502 W vectorless power estimate, with an effective throughput of 0.64 GOPS at 90 % sparsity.")
    R.h2("6.2 Major contributions")
    R.numbered([
        "A modular Sparse Compute-in-Memory / Near-Memory Processing Engine (<c>sparse_cim_top</c>) integrating "
        "three parameterised BRAM banks, a five-state zero-skipping controller and a DSP-free INT8 MAC.",
        "A rigorous treatment of in-memory versus near-memory computing on commercial FPGAs, justifying "
        "BRAM-centric NMC as the practical realisation of the CIM dataflow.",
        "Storage and traffic models for Dense, CSR, COO and CSC formats with index-overhead break-even "
        "thresholds, and a cycle-accurate latency model <i>T</i> = 3·NNZ + 2 that follows from the "
        "one-cycle BRAM read latency.",
        "A verification suite (MAC and top-level testbenches), a cycle-accurate reference trace, and a "
        "specified self-checking scoreboard extension.",
        "Post-synthesis characterisation on the Zynq-7000 and a comparison with published sparse "
        "accelerators and MAC units.",
        "A system-level integration roadmap: six-state multi-row CSR FSM, AXI4-Lite register map, PS–PL "
        "integration, bitstream/XSA/Vitis flow and a host driver.",
    ], fmt="{}.")
    R.h2("6.3 Conclusions and design insights")
    R.bullets([
        "<b>Compute proportional to non-zeros.</b> A controller that iterates over stored non-zeros converts "
        "sparsity directly into fewer cycles, fewer memory reads and fewer MACs; at 90 % sparsity the "
        "work is one tenth of the dense work.",
        "<b>The BRAM read latency is the architecture.</b> The serial dependency col_idx → vec_addr → "
        "vec_data across two one-cycle synchronous reads fixes the three-cycle schedule, and the same fact "
        "points to the optimisations (overlapped fetch, pipelining) that follow.",
        "<b>LUT arithmetic is the right size for INT8.</b> An 8 × 8 multiplier and 32-bit accumulator fit "
        "in 154 LUTs and 41 flip-flops without DSP slices, leaving the device almost entirely free for "
        "replication; block RAM, not logic, bounds the number of PEs.",
        "<b>Near-memory is the practical optimum on FPGAs.</b> The hard-macro BRAM interface rules out "
        "analog in-memory computing, but placing logic at the read port delivers the CIM benefits that "
        "matter at the edge: on-chip weights, deterministic timing and no off-chip traffic.",
        "<b>Report characterisation with its scope.</b> The delay and power figures are post-synthesis, "
        "out-of-context values; the activity-annotated and board-level measurements of the roadmap turn them "
        "into final design numbers.",
    ])
    R.h2("6.4 Future scope")
    R.h3("6.4.1 Complete multi-row CSR execution and automated verification")
    R.p("Implement the six-state FSM of Section 3.10 with a <c>row_ptr</c> bank and a result bank, verify "
        "it against the 4 × 4 example and randomised matrices with the scoreboard of Listing 3.8, "
        "and assert the cycle count <i>T</i> = 3·NNZ + 3<i>M</i> + 2. Add handling of empty rows and "
        "of rows longer than the bank, and constrained-random and coverage-driven verification "
        "(functional coverage of row-length, column-index and sign distributions, SystemVerilog assertions "
        "on the handshake).")
    R.h3("6.4.2 End-to-end hardware deployment on a physical FPGA SoC (Zynq-7000 / Zynq UltraScale+)")
    R.p("Package the core with the AXI4-Lite wrapper (Table 3.8), integrate it in IP Integrator, export the "
        "XSA, run the driver on the ARM Cortex-A9 and measure latency with a hardware cycle counter and power "
        "with the board monitor. Port the same IP to a Zynq UltraScale+ device, where UltraRAM and a "
        "larger DSP/LUT inventory allow substantially larger tiles and more PEs, and compare the "
        "measured and estimated values.")
    R.h3("6.4.3 Cross-accelerator and scenario-based benchmarking")
    R.p("Benchmark the engine on common pruned layers (for example a pruned fully connected layer and a "
        "Transformer projection) at matched sparsity, and compare it with a dense FPGA baseline, an "
        "embedded CPU running a software CSR kernel, and the published designs of Table 5.6 under a common "
        "measurement boundary (same model, same precision, same I/O accounting). Report latency, "
        "throughput, energy per inference and utilisation.")
    R.h3("6.4.4 Multi-precision arithmetic scaling (INT16, FP16, BF16, FP32)")
    R.p("Parameterise the MAC for INT16 and floating-point formats (FP16, BF16, FP32) while keeping "
        "the controller and banks, so that numerically sensitive workloads such as sparse linear solves in "
        "SLAM can use wider arithmetic and quantisation-sensitive networks can use mixed precision. The "
        "study should quantify the LUT/DSP trade-off for each format and the extra accumulator width "
        "needed. In the opposite direction, sub-byte INT4 and 2:4 structured sparsity [@mishra2021] reduce "
        "index and storage overhead further.")
    R.h3("6.4.5 Extended journal publication roadmap (Targeting IEEE TVLSI, IEEE TCAS-I/II, or ACM TRETS)")
    R.p("An extended journal article can combine the architecture and storage/latency models of this report "
        "with the completed multi-row execution, the implemented and measured results on a Zynq board, the "
        "pipelined schedule and the cross-accelerator benchmark. Suitable venues are IEEE Transactions on "
        "VLSI Systems, IEEE Transactions on Circuits and Systems I/II, and ACM Transactions on "
        "Reconfigurable Technology and Systems.")


def back_matter(R):
    # ---------------------------------------------------------------- Visible outcome
    R.plain_heading("Visible Outcome", page_break=True)
    R.p("The project has produced the technical deliverables summarised in Table 6.1.")
    R.table("Visible technical deliverables",
            ["Deliverable", "Recorded outcome"],
            [["RTL modules", "<c>bram_bank.sv</c>, <c>mac_unit.sv</c>, <c>sparse_cim_controller.sv</c>, "
              "<c>sparse_cim_top.sv</c> (SystemVerilog)"],
             ["Testbenches", "<c>tb_mac_unit.sv</c>, <c>tb_sparse_cim_top.sv</c>; Vivado Simulator "
              "waveform showing 0 → 15 → 7"],
             ["Synthesis characterisation", "Zynq-7000 xc7z020clg484-1: 154 LUTs, 41 FDCE, 3 RAMB18E1, "
              "0 DSP48E1; 10.32 ns critical path; 4.502 W vectorless power; 0.64 GOPS effective"],
             ["Analytical models", "CSR/COO/CSC storage, break-even densities, <i>T</i> = 3·NNZ + 2 latency, speedup "
              "and throughput tables"],
             ["Conference paper", "IEEE iSES conference paper “A Sparsity-Aware Near-Memory SpMVM Accelerator for "
              "Edge Inference on FPGA” (camera-ready manuscript)"],
             ["Integration roadmap", "Six-state multi-row FSM, AXI4-Lite register map, Zynq PS–PL block design, "
              "XSA/Vitis workflow, host driver"]],
            [1.7, 4.57], size=10)
    R.p("<b>Publication status.</b> The architecture, the RTL, and the post-synthesis characterisation have "
        "been reported in an IEEE conference paper authored by Vemana Venkata Pujithram and "
        "Dr. Rahul Ratnakumar (Manipal Institute of Technology, Manipal). The extended journal "
        "article outlined in Section 6.4.5 will build on the completed multi-row execution and board "
        "measurements.")

    # ---------------------------------------------------------------- References
    R.plain_heading("References", page_break=True)
    missing = [k for k in R.refdb if k not in R.cited]
    for k in missing:
        R.cited.append(k)   # keep every bibliography entry; appended in database order
    for n, k in enumerate(R.cited, 1):
        par = R.doc.add_paragraph()
        pf = par.paragraph_format
        pf.left_indent = Inches(0.45)
        pf.first_line_indent = Inches(-0.45)
        pf.space_after = Pt(5)
        pf.line_spacing = 1.1
        pf.tab_stops.add_tab_stop(Inches(0.45))
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        R.rich(par, f"[{n}]\t{REFS[k]}", 11)
    return missing


def project_details(R):
    R.plain_heading("Minor Specialization Project Details", page_break=True)
    R.table("", ["Field", "Details"],
            [["Student name", NAME],
             ["Registration number", REG],
             ["Branch / Section / Roll number", "Electronics and Communication Engineering / ________ / ________"],
             ["Mail ID / Mobile", "vemana.mitmpl2023@learner.manipal.edu / ____________________"]],
            [2.3, 3.97], size=11, caption=False)
    R.table("", ["Project and guide", "Details"],
            [["Project title", "A Sparsity-Aware Near-Memory SpMVM Accelerator for Edge Inference on FPGA"],
             ["Project type", "Individual Minor Specialization Project"],
             ["Minor specialization", "Minor in Embedded Systems"],
             ["Guide name and designation", "Dr. Rahul Ratnakumar, Assistant Professor"],
             ["Guide department", "Department of Electronics and Communication Engineering, MIT Manipal"],
             ["Target device and toolchain", "AMD/Xilinx Zynq-7000 SoC (xc7z020clg484-1); Xilinx Vivado"]],
            [2.3, 3.97], size=11, caption=False)
    R.table("", ["Sign-off", "Signature", "Date"],
            [[f"Student: {NAME} ({REG})", "", ""],
             ["Guide: Dr. Rahul Ratnakumar", "", ""],
             ["Head of Department", "", ""]],
            [2.8, 2.0, 1.47], size=11, caption=False)

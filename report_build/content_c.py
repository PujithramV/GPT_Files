"""Chapter 3, Sections 3.13 - 3.24."""
import os
from content_b import sv, FIG


def chapter3b(R):
    # ---------------------------------------------------------------- 3.13
    R.h2("3.13 Sparse accumulation and result interface")
    R.p("The result interface of the implemented core is the pair (<c>final_result</c>, <c>done</c>). "
        "<c>final_result</c> is the live output of the 32-bit accumulator. It is <i>not</i> a latched "
        "output: it takes the value 0 while the FSM rests in IDLE (the clear is asserted), changes after "
        "each COMPUTE, and is final in DONE_STATE. The host therefore samples it only when <c>done</c> = 1. "
        "Because the accumulator is cleared in IDLE and is not cleared in DONE_STATE, the value remains "
        "readable for the whole time <c>done</c> is asserted, i.e. until the host lowers <c>start</c> and "
        "the FSM returns to IDLE.")
    R.p("The accumulation law for one invocation with non-zeros (<i>w</i><sub><i>k</i></sub>, "
        "<i>c</i><sub><i>k</i></sub>), <i>k</i> = 0, …, NNZ−1, is")
    R.eq("acc<sub>0</sub> = 0,   acc<sub><i>k</i>+1</sub> = acc<sub><i>k</i></sub> + "
         "<i>w</i><sub><i>k</i></sub> · <i>x</i>[<i>c</i><sub><i>k</i></sub>],   "
         "<c>final_result</c> = acc<sub>NNZ</sub>")
    R.p("with each step realised by one COMPUTE cycle. This is exactly the row dot product of "
        "Section 3.4 for the row stored in the banks.")
    R.p("<b>Multi-row write-back scaling.</b> For a full matrix the accumulator is the row accumulator of a "
        "larger loop. At the end of each row the WRITEBACK state stores the accumulator into a result BRAM "
        "(address = row index), pulses <c>clr_acc</c> so that the next row starts from zero, and increments "
        "the row counter; <c>row_ptr</c> differences supply each row's length. The result vector "
        "<i>y</i> then resides in an on-chip bank that the host reads through the AXI BRAM controller, "
        "and a single <c>done</c> marks the end of the whole matrix. Counting two cycles of row-pointer "
        "fetch and one write-back cycle per row (Section 3.10), the latency of the extension is")
    R.eq("<i>T</i><sub>multi</sub> = 1 + ∑<sub><i>r</i>=0</sub><sup><i>M</i>−1</sup> "
         "(2 + 3<i>n</i><sub><i>r</i></sub> + 1) + 1 = 3 · NNZ + 3<i>M</i> + 2")
    R.p("where <i>n</i><sub><i>r</i></sub> is the number of non-zeros of row <i>r</i>. For the 4 × 4 "
        "example (NNZ = 6, <i>M</i> = 4) this evaluates to 3·6 + 3·4 + 2 = 32 cycles; an empty "
        "row costs only its three overhead cycles. This is a design estimate for the scaling framework, "
        "to be confirmed by simulation of the extended controller.")

    # ---------------------------------------------------------------- 3.14
    R.h2("3.14 Completion, reset, and repeated invocation")
    R.p("<b>Reset (<c>rst_n</c>).</b> The controller and the MAC use an active-low asynchronous reset "
        "(<c>always_ff @(posedge clk or negedge rst_n)</c>). Asserting <c>rst_n</c> returns the FSM to IDLE, "
        "sets the pointer to 0 and zeros the accumulator immediately, regardless of the clock. Releasing it "
        "is recommended to be synchronised to <c>clk</c> in the integrated system (the processor-system reset "
        "block of Section 3.21 provides this). The BRAM banks are not reset: their contents persist, "
        "which is what allows weights to be reused across invocations.")
    R.p("<b>Clear (<c>clr_acc</c>).</b> The controller asserts <c>mac_clr</c> in every cycle spent in IDLE, so "
        "the accumulator is zero on entry to FETCH_PTR without any explicit initialisation by the host. It "
        "is a <i>synchronous</i> clear, so it acts at a clock edge and allows the FSM to clear the accumulator "
        "at a row boundary without a hard reset of the system (the same signal is used by WRITEBACK in the "
        "multi-row extension).")
    R.p("<b><c>start</c> / <c>done</c> handshake.</b> The protocol is a four-phase level handshake:")
    R.numbered([
        "The host preloads the banks and sets <c>nnz_count</c>.",
        "The host raises <c>start</c>. The FSM leaves IDLE at the next clock edge (if <c>nnz_count</c> > 0).",
        "The FSM runs 3·NNZ cycles and enters DONE_STATE; <c>done</c> rises and <c>final_result</c> is valid.",
        "The host reads the result and lowers <c>start</c>. In DONE_STATE the FSM sees <c>start</c> = 0 and "
        "returns to IDLE; <c>done</c> falls.",
    ], fmt="{}.")
    R.p("<b>DONE_STATE retention.</b> While <c>start</c> stays high the FSM remains in DONE_STATE and "
        "<c>done</c> and <c>final_result</c> remain stable. This retention makes the result safe to read "
        "by a slow host (for example over an AXI register) without a latch or FIFO, and prevents an "
        "accidental second run: re-execution requires an explicit start-low/start-high cycle. A guard is "
        "also provided at the input: <c>start</c> with <c>nnz_count</c> = 0 is ignored, so an empty "
        "invocation cannot underflow the termination compare <c>current_ptr == nnz_count - 1</c>. "
        "<c>start</c> is not examined in FETCH_PTR, FETCH_VEC or COMPUTE, so lowering it mid-run does not "
        "abort the computation.")
    R.p("<b>Repeated invocation.</b> Because the banks persist, a second invocation on the same weights but "
        "a new input vector only rewrites <c>bank_vector</c> through Port B and repeats the handshake, which "
        "is the pattern of repeated inference with a fixed (pruned) layer.")

    # ---------------------------------------------------------------- 3.15
    R.h2("3.15 Module organization and verification hierarchy")
    R.p("The design comprises four RTL modules and two testbenches in six source files. The hierarchy is "
        "<c>sparse_cim_top</c> → {<c>sparse_cim_controller</c>, <c>mac_unit</c>, <c>bram_bank</c> × 3}; "
        "<c>tb_sparse_cim_top</c> instantiates the top level and <c>tb_mac_unit</c> instantiates the MAC "
        "alone. Table 3.6 maps modules to files and roles.")
    R.table("RTL modules and testbenches",
            ["Module", "Source file", "Role", "Instances"],
            [["<c>sparse_cim_top</c>", "sparse_cim_top.sv", "Top level; wires controller, MAC and three BRAM banks; "
              "exposes start/done, <c>nnz_count</c>, result and Port B preload ports", "1 (DUT of <c>tb_sparse_cim_top</c>)"],
             ["<c>sparse_cim_controller</c>", "sparse_cim_controller.sv", "Five-state zero-skipping FSM; address and "
              "MAC control", "1"],
             ["<c>mac_unit</c>", "mac_unit.sv", "Signed INT8 multiplier and 32-bit accumulator", "1"],
             ["<c>bram_bank</c>", "bram_bank.sv", "Parameterised dual-port block-RAM bank", "3 (values, col_idx, vector)"],
             ["<c>tb_mac_unit</c>", "tb_mac_unit.sv", "Directed unit test of the arithmetic datapath", "Simulation only"],
             ["<c>tb_sparse_cim_top</c>", "tb_sparse_cim_top.sv", "Top-level directed test: preload, run, "
              "observe <c>done</c> and result", "Simulation only"]],
            [1.55, 1.6, 2.2, 0.92], size=9)
    R.p("The verification hierarchy is bottom-up. The MAC is first tested in isolation, where the arithmetic "
        "is observable directly at <c>acc_out</c>; the top-level testbench then validates the integrated "
        "behaviour (memory preload, indirect addressing, FSM sequencing and handshake) on a known data set. "
        "Each testbench is self-contained and uses implicit port connection (<c>.*</c>), so adding a port to a "
        "DUT requires no edit to its testbench provided the names match.")

    # ---------------------------------------------------------------- 3.16
    R.h2("3.16 Verification strategy and acceptance checks")
    R.p("Listing 3.6 gives the MAC unit testbench in full. It generates a 100 MHz clock "
        "(<c>always #5 clk = ~clk</c>), applies a reset for 15 ns, and walks the MAC through five "
        "scenarios.")
    R.code("tb_mac_unit.sv – directed testbench for the MAC unit", sv("tb_mac_unit.sv"))
    R.h3("Stimulus phases of tb_mac_unit")
    R.defs([
        ("Initialisation and reset (lines 22–30)", "all inputs are driven to 0 and <c>rst_n</c> is held low "
         "for 15 ns, so the accumulator is cleared by the asynchronous reset before any operand is applied."),
        ("Test 1 – first MAC (lines 32–36)", "<c>en</c> = 1, 5 × 3: the accumulator should load 15."),
        ("Test 2 – signed accumulation (lines 38–41)", "−4 × 2 = −8 is added: "
         "15 + (−8) = 7, verifying negative-operand multiplication and sign-extended accumulation."),
        ("Test 3 – enable low (lines 43–47)", "<c>en</c> = 0 while the operands are set to 10 × 10: the "
         "value must stay 7. This is the “skipped cycle” that models a zero element being bypassed."),
        ("Test 4 – clear (lines 49–54)", "<c>clr_acc</c> = 1 for one cycle: the accumulator returns to 0 "
         "even though <c>en</c> is 0, then <c>clr_acc</c> is released."),
        ("Termination (lines 56–57)", "20 ns of idle time and <c>$finish</c>."),
    ])
    R.p("The intended accumulator sequence is therefore 0 → 15 → 7 → 7 → 0, with each "
        "step taking effect at the clock edge following the stimulus change.")
    R.p("Listing 3.7 gives the top-level testbench.")
    R.code("tb_sparse_cim_top.sv – top-level directed testbench with BRAM preload and start/done handshake",
           sv("tb_sparse_cim_top.sv"))
    R.h3("Stimulus phases of tb_sparse_cim_top")
    R.defs([
        ("Initialisation (lines 32–39)", "clock, reset, <c>start</c>, <c>nnz_count</c> and all preload "
         "signals are set to 0; <c>rst_n</c> is released after 20 ns."),
        ("Phase 1 – preload through Port B (lines 44–74)", "at address 0 the testbench writes weight 5, "
         "column 0 and vector element <i>x</i>[0] = 3 into the three banks; at address 1 it writes weight "
         "−4 and column 2 (with the vector write enable temporarily low, so no vector word is stored at "
         "address 1); finally, with the value and column write enables low, it writes <i>x</i>[2] = 2 at "
         "address 2. The note in the source records the reason for the pause: the compressed arrays are "
         "packed from address 0, whereas the dense vector is indexed by column."),
        ("Phase 2 – run (lines 76–87)", "after 20 ns <c>nnz_count</c> = 2 and <c>start</c> = 1 "
         "are applied; <c>wait(done == 1'b1)</c> blocks until the FSM reaches DONE_STATE, then <c>start</c> is "
         "released one clock later."),
        ("Observation window (lines 89–91)", "50 ns of simulation after the handshake so that the return to "
         "IDLE and the clearing of the accumulator are visible, then <c>$finish</c>."),
    ])
    R.p("<b>Self-checking scoreboard extension.</b> The directed testbenches expose the signals for waveform "
        "inspection and give a precise expected sequence. The natural extension, which the same structure "
        "supports, is a self-checking scoreboard that computes the expected value from the preloaded arrays "
        "with a software golden model and compares it with <c>final_result</c> when <c>done</c> rises. "
        "Together with driving stimulus from non-blocking assignments (so that the sampling order of "
        "stimulus and design at a clock edge is independent of simulator scheduling), randomised "
        "(<c>values</c>, <c>col_idx</c>, <c>vec</c>) tuples and a cycle-count assertion "
        "(<i>T</i> = 3·NNZ + 2), this turns the directed tests into a regression suite. Listing 3.8 "
        "gives the intended scoreboard.")
    R.code("Self-checking scoreboard extension (proposed)",
"""// Golden model: dot product of the preloaded compressed row (testbench shadow arrays)
function automatic int signed golden(input int n);
    int signed acc = 0;
    for (int k = 0; k < n; k++)
        acc += $signed(val_mem[k]) * $signed(vec_mem[col_mem[k][5:0]]);
    return acc;
endfunction

task automatic run_and_check(input int n);
    int cyc = 0;
    @(negedge clk);  nnz_count = n;  start = 1;      // drive away from the active edge
    while (!done) begin @(negedge clk); cyc++; end    // sample away from the active edge
    assert (final_result === golden(n))
        else $error("result %0d != expected %0d", final_result, golden(n));
    assert (cyc == 3*n + 1)                          // IDLE + 3n + DONE
        else $error("latency %0d != %0d", cyc, 3*n + 1);
    @(negedge clk);  start = 0;
endtask""")
    R.table("Acceptance checks for the Sparse-CIM core",
            ["ID", "Check", "Stimulus", "Expected outcome", "Status"],
            [["V1", "Signed multiply", "5 × 3, then −4 × 2 (MAC TB)", "acc: 15 → 7", "Directed test"],
             ["V2", "Enable gating", "<c>en</c> = 0 with operands 10, 10", "acc holds 7", "Directed test"],
             ["V3", "Synchronous clear", "<c>clr_acc</c> = 1", "acc = 0", "Directed test"],
             ["V4", "BRAM preload", "Port B writes, three banks", "Operands stored at stated addresses", "Directed test"],
             ["V5", "Indirect addressing", "col_idx = {0, 2}, <i>x</i>[0] = 3, <i>x</i>[2] = 2", "5(3) + (−4)(2) = 7",
              "Waveform (Figure 5.1)"],
             ["V6", "FSM sequencing", "<c>start</c> = 1, <c>nnz_count</c> = 2", "FETCH_PTR → FETCH_VEC → COMPUTE ""×2 → DONE_STATE",
              "Waveform (Figure 5.1)"],
             ["V7", "Handshake and clear", "Release <c>start</c>", "<c>done</c> falls; accumulator cleared in IDLE",
              "Waveform (Figure 5.1)"],
             ["V8", "Self-checking regression", "Randomised CSR rows, golden model", "Result and cycle count match",
              "Roadmap (Listing 3.8)"],
             ["V9", "Multi-row sequencing", "4 × 4 example, <c>row_ptr</c> = [0,2,3,4,6]", "<i>y</i> = (13, 3, 12, 24)",
              "Roadmap (Section 3.10)"]],
            [0.4, 1.3, 1.75, 1.7, 1.12], size=8.5)

    # ---------------------------------------------------------------- 3.17
    R.h2("3.17 Synthesis and resource optimization")
    R.p("Out-of-context (OOC) synthesis in Vivado synthesises the module as a stand-alone block with no "
        "I/O buffers, so the reported area and power describe the accelerator and not the I/O pads of "
        "the device [@ug901]. Four aspects of the result are explained here and quantified in Section 5.5.")
    R.p("<b>RAMB18E1 inference.</b> Each <c>bram_bank</c> is 64 × 8 = 512 bits. The "
        "<c>ram_style = \"block\"</c> attribute and the registered-read coding style cause synthesis to "
        "infer one RAMB18E1 per bank, giving 3 RAMB18E1 in total (3/280 = 1.07 % of the device). A RAMB18E1 "
        "holds 18 Kb and can be configured as 2K × 9 [@ug473], so each bank uses only about 3 % of the "
        "capacity of its primitive: raising <c>ADDR_WIDTH</c> to 11 (2,048 words) increases the capacity "
        "of every bank 32-fold at <i>no</i> additional block-RAM cost, and is the first step in scaling the "
        "tile size.")
    R.p("<b>LUT-level arithmetic with 0 DSPs.</b> The 8 × 8 signed multiplier, the 32-bit adder, the "
        "operand gating and the pointer logic are all implemented in slice LUTs and carry chains: the "
        "reported run uses 154 slice LUTs (154/53,200 = 0.29 %) and 0 DSP48E1 slices (0/220). The 32-bit "
        "accumulate uses the carry chain, and the 8 × 8 multiplier is the dominant consumer of LUTs, "
        "with the controller's output gating, the pointer incrementer and the end-of-loop comparator "
        "making up the remainder. A DSP48E1 offers a 25 × 18 multiplier [@ug479], so using one for an "
        "8 × 8 product would leave most of it idle while consuming a scarce DSP column site; moving the "
        "multiplier to LUTs removes that constraint, lets the placer put it beside the BRAM column, and "
        "allows dozens of PEs to coexist (Section 5.5). The mapping of arithmetic to LUT fabric is "
        "controlled at synthesis through the DSP-usage settings of Vivado [@ug901]; recording the chosen "
        "setting in the project constraints makes the 0-DSP result reproducible.")
    R.p("<b>FDCE register count.</b> The 41 slice registers, all of type FDCE (D flip-flop with clock enable "
        "and asynchronous clear), decompose exactly into the 32-bit accumulator <c>acc_out</c>, the 6-bit "
        "pointer <c>current_ptr</c> and the 3-bit state register <c>current_state</c>: 32 + 6 + 3 = 41. "
        "The BRAM output registers are inside the RAMB18E1 primitives and are not counted as slice "
        "registers, and the 64 × 8 arrays require no flip-flops. The match between the architectural "
        "state of Sections 3.8–3.12 and the reported register count is a consistency check on the "
        "synthesised netlist.")
    R.p("<b>Latch-free control.</b> The default-assignment style of the combinational block ensures that "
        "synthesis infers no latches; the flip-flop count above is correspondingly free of extra storage "
        "elements.")

    # ---------------------------------------------------------------- 3.18
    R.h2("3.18 Physical implementation methodology")
    R.p("After synthesis, implementation performs placement (assigning each LUT, flip-flop and RAM to a "
        "physical site), routing (selecting programmable interconnect between sites) and timing "
        "closure. In the Zynq-7000 PL the block RAMs are arranged in vertical columns interleaved with the "
        "slice columns, and a net from a RAMB18E1 output to a slice LUT uses the general interconnect "
        "fabric; the delay of that connection is a function of the distance between the two sites. "
        "BRAM-to-logic locality is therefore a physical property that the placer controls rather than a "
        "logical property of the netlist.")
    R.p("For the Sparse-CIM PE this has three practical implications. (i) All fan-out from the BRAM "
        "outputs is small (the weight bus feeds the multiplier gating, the column bus feeds only the "
        "vector address, the vector bus feeds the multiplier gating), so the nets that matter for timing "
        "are few and short once the three banks are placed near the arithmetic. (ii) The use of LUT "
        "arithmetic rather than DSP48E1 leaves the placer free to choose the slice sites nearest to the "
        "RAM columns, whereas a DSP48E1 is fixed to a DSP column. (iii) For multiple PEs, each PE with its "
        "three banks should be kept in one clock region (for example with a Pblock constraint) so that its "
        "memory-to-compute connections remain local. Full place-and-route of the integrated design, "
        "with the block design clock and the AXI interconnect present, is part of the integration roadmap; "
        "the figures reported in this project are post-synthesis out-of-context values.")

    # ---------------------------------------------------------------- 3.19
    R.h2("3.19 Timing constraints and clock interpretation")
    R.p("Two clock-related numbers appear in the project and must be interpreted separately. The "
        "<b>simulation clock</b> is 100 MHz (period 10 ns): the testbenches use <c>always #5 clk = "
        "~clk</c>. It determines the time axis of the waveform (Figure 5.1) but it is not a timing "
        "constraint of the hardware. The <b>critical-path delay</b> of 10.32 ns is the post-synthesis "
        "estimate of the longest register-to-register path through the design, which, from the structure "
        "of the datapath, runs from the BRAM output registers through the operand gating and the "
        "combinational 8 × 8 multiplier and the 32-bit carry chain into the accumulator. The maximum "
        "clock frequency that this path supports is")
    R.eq("<i>F</i><sub>max</sub> = 1 / <i>T</i><sub>crit</sub> = 1 / 10.32 ns ≈ 96.90 MHz")
    R.p("and the setup slack at a target clock period <i>T</i><sub>clk</sub> is "
        "<i>T</i><sub>clk</sub> − <i>T</i><sub>crit</sub> (ignoring clock uncertainty). Hence "
        "<i>T</i><sub>clk</sub> = 10.5 ns (95.2 MHz) gives a margin of +0.18 ns and "
        "<i>T</i><sub>clk</sub> = 11 ns (90.9 MHz) gives +0.68 ns; the 10 ns simulation period would "
        "correspond to −0.32 ns and indicates where the first pipelining step is needed. Listing 3.9 shows "
        "the constraint that expresses a 10.5 ns clock [@ug903].")
    R.code("Clock constraint for implementation (Xilinx Design Constraints)",
           "create_clock -name clk -period 10.500 [get_ports clk]", numbered=False)
    R.p("The path can be shortened without changing the architecture: registering the 16-bit product "
        "between the multiplier and the adder splits the path into two shorter ones (at the cost of one "
        "extra cycle of latency and 16 flip-flops), and registering the gated operands removes the "
        "controller's multiplexing from the path. Either step moves <i>F</i><sub>max</sub> well beyond "
        "100 MHz and keeps the compute rate at one non-zero per three cycles or better (Section 3.11). "
        "In the integrated SoC, the PL clock is generated by the processing system (FCLK_CLK0) at a "
        "frequency chosen to meet this constraint.")

    # ---------------------------------------------------------------- 3.20
    R.h2("3.20 Custom IP packaging and proposed AXI4-Lite interface")
    R.p("To make the accelerator controllable by the ARM Cortex-A9, <c>sparse_cim_top</c> is to be wrapped "
        "as a custom IP core with an AXI4-Lite slave interface [@amba], using the Vivado IP packager "
        "[@ug1118]. The wrapper converts memory-mapped register accesses into the <c>start</c>, "
        "<c>nnz_count</c> and result signals of the core, and exposes the three BRAM banks to the "
        "processor through AXI BRAM controllers [@pg078] on Port B. Table 3.8 gives the proposed register map. "
        "The base address is assigned by the Vivado address editor (typically 0x43C0_0000 for the first IP on "
        "the M_AXI_GP0 port).")
    R.table("Proposed AXI4-Lite register map of the Sparse-CIM IP",
            ["Offset", "Register", "Access", "Bits", "Description"],
            [["0x00", "CTRL", "R/W", "[0] START; [1] SOFT_RESET", "START drives <c>start</c>; the wrapper holds "
              "it until DONE and then releases it; SOFT_RESET drives <c>rst_n</c> low"],
             ["0x04", "STATUS", "R/O", "[0] DONE; [1] BUSY", "DONE mirrors <c>done</c> (sticky until the next START); "
              "BUSY = START ∧ ¬DONE"],
             ["0x08", "NNZ_COUNT", "R/W", "[5:0] (6-bit instance)", "Drives <c>nnz_count</c>: non-zeros per row for the "
              "single-row core, total non-zeros for the multi-row extension"],
             ["0x0C", "ROW_COUNT", "R/W", "[15:0]", "Number of rows <i>M</i> for the multi-row extension; unused by "
              "the single-row core"],
             ["0x10", "RESULT", "R/O", "[31:0] signed", "Drives from <c>final_result</c>; valid when STATUS.DONE = 1"],
             ["Windows", "BRAM banks", "R/W", "8-bit words", "<c>bank_values</c>, <c>bank_col_idx</c>, "
              "<c>bank_vector</c> (and <c>row_ptr</c>/<c>y</c> banks in the extension) at separate AXI BRAM "
              "controller base addresses; written before START"]],
            [0.65, 1.0, 0.6, 1.35, 2.67], size=9)
    R.p("The register semantics map one-to-one onto the handshake of Section 3.14. Because the RTL leaves "
        "DONE_STATE only after <c>start</c> falls, the wrapper either exposes START as a level that software "
        "clears, or (as proposed above) holds an internal start until DONE is observed and then clears it, "
        "making START a write-1 command. The DONE bit may also be routed to the PS interrupt input "
        "(IRQ_F2P) to avoid polling.")

    # ---------------------------------------------------------------- 3.21
    R.h2("3.21 Processing-system and programmable-logic integration")
    R.p("Figure 3.6 shows the proposed integration in the Zynq-7000 SoC. The processing system's "
        "M_AXI_GP0 master port issues AXI transactions to an AXI interconnect, which routes register "
        "accesses to the AXI4-Lite slave wrapper and memory accesses to the AXI BRAM controller(s). The "
        "BRAM banks are true dual-port: Port B is connected to the controller for streaming the CSR arrays and "
        "input vectors written by the ARM processor (or by DMA), and Port A is connected to the "
        "sparse-CIM core exactly as in the simulated design.")
    R.figure(os.path.join(FIG, "gen_fig_soc.png"), "Proposed Zynq-7000 integration: ARM Cortex-A9 PS, AXI "
             "interconnect, AXI4-Lite wrapper, AXI BRAM controllers and the Sparse-CIM PE with dual-port banks", 5.7)
    R.bullets([
        "<b>Clock.</b> The PS supplies FCLK_CLK0 to the AXI interconnect, the wrapper and the core, so "
        "there is a single synchronous domain and no clock-domain crossing inside the PE.",
        "<b>Reset.</b> A processor-system reset block turns FCLK_RESET0_N into the synchronised "
        "<c>rst_n</c> of the core.",
        "<b>Memory ownership.</b> Port B is written by the PS only while BUSY = 0; Port A is read only by "
        "the core. This preserves the conflict-free dual-port discipline of Section 3.9.",
        "<b>Data path.</b> Weights and CSR arrays reside in DDR3 under the PS; at layer load the processor "
        "(or a DMA engine) copies the arrays through the AXI BRAM controller into the on-chip banks, after "
        "which inference runs entirely on-chip.",
        "<b>Completion.</b> DONE is polled over AXI4-Lite or routed to IRQ_F2P.",
    ])
    R.p("The integration is built in Vivado IP Integrator [@ug994]: the IP is added from the "
        "repository, connection automation instantiates the interconnect and reset block, and the Address "
        "Editor assigns the base addresses used by the driver of Section 3.23. Each added PE is an "
        "additional AXI slave with its own windows.")

    # ---------------------------------------------------------------- 3.22
    R.h2("3.22 Bitstream export and embedded-software workflow")
    R.p("Moving from a validated block design to running software follows the sequence in Table 3.9. The "
        "hardware handoff is a <b>.xsa</b> (Xilinx Support Archive) file produced by Vivado's “Export "
        "Hardware” step with the bitstream included; it carries the PL configuration, the address map and "
        "the PS initialisation. Vitis consumes the XSA to create a platform and a domain (bare-metal "
        "<i>standalone</i> for the simplest flow, or PetaLinux/Linux when an operating system is needed) and "
        "generates the board-support package, including the header <c>xparameters.h</c> that defines the IP "
        "base addresses [@ug1400].")
    R.table("Bitstream export and embedded-software workflow",
            ["Step", "Tool", "Input", "Output", "Purpose"],
            [["1", "Vivado IP Packager", "RTL + AXI wrapper", "Custom IP (<c>component.xml</c>)", "Reusable IP core"],
             ["2", "IP Integrator", "IP, PS7, interconnect, BRAM ctrl", "Block design", "SoC structure"],
             ["3", "Vivado", "Block design", "HDL wrapper, address map", "Top-level netlist source"],
             ["4", "Synthesis, implementation, <c>write_bitstream</c>", "HDL, constraints", "<c>.bit</c>", "PL configuration"],
             ["5", "Export Hardware", "Implemented design", "<c>.xsa</c> (with bitstream)", "Hardware handoff"],
             ["6", "Vitis / PetaLinux", "<c>.xsa</c>", "Platform, BSP, <c>xparameters.h</c>", "Software platform"],
             ["7", "Vitis build", "C driver", "<c>.elf</c>", "Executable"],
             ["8", "Program and run", "<c>.bit</c> + <c>.elf</c> (JTAG) or <c>BOOT.BIN</c> (SD)", "Running system",
              "Board execution"]],
            [0.45, 1.35, 1.6, 1.5, 1.37], size=9)
    R.p("The same XSA flow is the route by which the project's synthesised core becomes a board-level demonstrator; "
        "the software of Step 7 is the subject of Section 3.23.")

    # ---------------------------------------------------------------- 3.23
    R.h2("3.23 Host application control flow")
    R.p("The host application performs five actions: (i) convert the pruned INT8 matrix to CSR (offline or "
        "at start-up), (ii) preload the three banks over AXI, (iii) program <c>NNZ_COUNT</c> and set START, "
        "(iv) poll DONE with a timeout, (v) read RESULT and compare with a software reference. Listing 3.10 "
        "gives the driver pseudocode in C for the single-row core; the multi-row extension loops the same "
        "control flow over the row-pointer array.")
    R.code("C driver pseudocode for the Sparse-CIM IP (bare-metal, AXI4-Lite)",
"""#include "xil_io.h"
#include "xparameters.h"          /* defines CIM_BASE, CIM_VAL_BASE, CIM_COL_BASE, CIM_VEC_BASE */

#define REG_CTRL   0x00
#define REG_STATUS 0x04
#define REG_NNZ    0x08
#define REG_RESULT 0x10
#define START_BIT  0x1
#define DONE_BIT   0x1
#define TIMEOUT    1000000u

/* 1. Preload the compressed row and the dense vector into the BRAM banks (Port B) */
void cim_preload(const int8_t *val, const uint8_t *col, const int8_t *vec,
                 unsigned nnz, unsigned n)
{
    for (unsigned k = 0; k < nnz; k++) {
        Xil_Out32(CIM_VAL_BASE + 4*k, (uint8_t)val[k]);   /* two's-complement byte */
        Xil_Out32(CIM_COL_BASE + 4*k, col[k]);
    }
    for (unsigned j = 0; j < n; j++)
        Xil_Out32(CIM_VEC_BASE + 4*j, (uint8_t)vec[j]);
}

/* 2-4. Start, poll DONE, read the signed 32-bit result */
int cim_run(unsigned nnz, int32_t *result)
{
    Xil_Out32(CIM_BASE + REG_NNZ, nnz);
    Xil_Out32(CIM_BASE + REG_CTRL, START_BIT);             /* pulse / set START */

    unsigned t = TIMEOUT;
    while (!(Xil_In32(CIM_BASE + REG_STATUS) & DONE_BIT)) {
        if (--t == 0) return -1;                           /* hardware timeout */
    }
    *result = (int32_t)Xil_In32(CIM_BASE + REG_RESULT);    /* valid while DONE = 1 */
    Xil_Out32(CIM_BASE + REG_CTRL, 0);                     /* release START: FSM -> IDLE */
    return 0;
}

int main(void)
{
    const int8_t  val[2] = { 5, -4 };
    const uint8_t col[2] = { 0, 2 };
    const int8_t  vec[3] = { 3, 0, 2 };
    int32_t y;

    cim_preload(val, col, vec, 2, 3);
    if (cim_run(2, &y) == 0 && y == 7)                     /* expected: 5*3 + (-4)*2 */
        xil_printf("PASS: y = %d\\r\\n", (int)y);
    else
        xil_printf("FAIL\\r\\n");
    return 0;
}""")
    R.p("Two details of the driver follow from the hardware. First, the byte written to a bank is the "
        "two's-complement representation of the INT8 value, so the cast <c>(uint8_t)</c> is a bit-for-bit "
        "copy, and the result is reinterpreted as <c>int32_t</c> on read. Second, START is released only "
        "after RESULT has been read, because the FSM retains DONE_STATE (and the result) until "
        "<c>start</c> falls.")

    # ---------------------------------------------------------------- 3.24
    R.h2("3.24 Edge-inference applications and deployment scenarios")
    R.p("The engine targets the class of workloads in which a fixed, pruned weight matrix is applied to a "
        "stream of dense activation vectors under tight power and latency budgets. Four deployment "
        "families illustrate how the architecture would be used. Each assumes the roadmap integration of "
        "Sections 3.20–3.23; the quantitative results of this report are those of the core itself.")
    R.h3("(a) Pruned CNNs, MLPs and Transformers")
    R.p("Fully connected and projection layers of pruned networks are SpMVM at batch size one. A "
        "tile of the pruned weight matrix, stored as CSR in the three banks, is loaded once per layer; "
        "the activation vector for each inference is written to <c>bank_vector</c>, and the PE returns one "
        "output element per row. Convolutional layers lowered to matrix form and the query/key/value and "
        "feed-forward projections of a small Transformer follow the same pattern. Larger layers are "
        "partitioned into tiles that fit the banks (for the 11-bit instance, 2,048 non-zeros per tile), "
        "processed by one PE in sequence or by several PEs in parallel (Section 5.5). Unstructured pruning "
        "ratios of 70–90 % [@han2015], [@hoefler2021] place these layers in the regime where "
        "Section 5.9 shows speedups of 3× or more over a dense scan.")
    R.h3("(b) TinyML, keyword spotting and audio IoT")
    R.p("Keyword-spotting and sound-event detection run small MLPs or depthwise-separable CNNs on "
        "mel-frequency features every few tens of milliseconds. Their weights are small enough to reside "
        "permanently in on-chip block RAM, so the PE never accesses DRAM during inference; the batch-one, "
        "deterministic, always-on character of the workload matches the engine's cycle-exact latency "
        "<i>T</i> = 3·NNZ + 2 (for a few thousand non-zeros, a few hundred microseconds at about "
        "90 MHz, well within a 20–40 ms audio frame). Between frames the accumulator and FSM idle with "
        "no switching activity.")
    R.h3("(c) Autonomous robotics, LiDAR point-cloud and SLAM graph processing")
    R.p("Mobile robots and drones combine learned perception with sparse numerical kernels. Voxelised LiDAR "
        "point clouds are inherently sparse (most voxels are empty), and sparse convolutions and "
        "graph-based pose optimisation in SLAM reduce to repeated sparse matrix–vector products with "
        "Jacobian or adjacency matrices of fixed structure [@bell2009], [@williams2007]. A fixed sparsity "
        "pattern is the ideal case for a CSR engine: the <c>row_ptr</c>/<c>col_idx</c> arrays are computed "
        "once and reused, and the deterministic latency of the FSM supports hard control-loop deadlines. "
        "Wider arithmetic (INT16 or FP32) would be needed for numerically sensitive solver steps, which "
        "is why the multi-precision scaling of Section 6.4.4 is part of the roadmap.")
    R.h3("(d) Smart healthcare wearables, ECG and EEG biosignal classification")
    R.p("Biosignal classifiers operate on short windows of ECG or EEG samples and use compact 1-D CNNs or "
        "MLPs whose pruned weights fit in a few kilobytes. On-chip storage keeps patient data on the "
        "device, which supports privacy requirements, and a deterministic engine allows the worst-case "
        "latency of an arrhythmia alarm to be bounded analytically. Because the design uses only generic "
        "BRAM and LUT resources, the same RTL can be retargeted to lower-power FPGA families for "
        "wearable form factors, and the effective activity of the engine (the fraction of cycles in which "
        "the MAC is enabled) can be reduced further by gating BRAM enables outside the active states "
        "(Section 5.7).")

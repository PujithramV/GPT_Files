"""Chapter 3, Sections 3.1 - 3.12."""
import os
from model import storage_bits, clog2, cycles_for

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")
SV = os.path.dirname(HERE)


def sv(name):
    with open(os.path.join(SV, name), encoding="utf-8") as f:
        return f.read()


def chapter3a(R):
    R.chapter("Methodology")

    # ---------------------------------------------------------------- 3.1
    R.h2("3.1 Type and nature of the project")
    R.p("This is an individual hardware-design and hardware-characterisation project in the domain of digital "
        "VLSI and computer architecture. Its method is analytical and experimental: the computation is first "
        "formulated mathematically (CSR storage and the zero-skipping dot product), then realised as "
        "synthesisable SystemVerilog RTL, then verified by directed behavioural simulation, and finally "
        "characterised by post-synthesis area, timing and power analysis on a specific commercial device, the "
        "AMD/Xilinx Zynq-7000 <c>xc7z020clg484-1</c>.")
    R.p("The project is a <i>design-space</i> study as much as a design: the choice of storage format, of memory "
        "organisation (near-memory rather than in-memory), of control schedule (three cycles per non-zero) and of "
        "arithmetic mapping (LUT rather than DSP) are each justified quantitatively in this chapter and "
        "evaluated in Chapter 5. The scope of the verified results is the Sparse-CIM processing element; the "
        "system-level integration needed for a complete SoC product is specified as a roadmap in Sections "
        "3.20–3.23.")

    # ---------------------------------------------------------------- 3.2
    R.h2("3.2 Hardware and software requirements")
    R.p("Table 3.1 lists the platform, tool and parameter choices used in the project, together with the "
        "resources that the integration roadmap will additionally require.")
    R.table("Target platform, toolchain and design parameters",
            ["Item", "Specification", "Purpose"],
            [["Target device", "AMD/Xilinx Zynq-7000 SoC <c>xc7z020clg484-1</c> (speed grade –1)",
              "Synthesis and characterisation target"],
             ["Device resources", "53,200 LUTs; 106,400 FFs; 280 RAMB18E1 (140 × 36 Kb); 220 DSP48E1",
              "Denominators for utilisation percentages"],
             ["Design tool", "AMD/Xilinx Vivado Design Suite (synthesis, out-of-context mode)",
              "Synthesis, timing and power estimation"],
             ["Simulator", "Vivado Simulator (xsim)", "Behavioural verification of RTL"],
             ["Language", "SystemVerilog (IEEE 1800-2017) [@ieee1800] with <c>`timescale 1ns / 1ps</c>", "RTL and testbenches"],
             ["Design parameters", "<c>DATA_WIDTH</c> = 8; <c>ADDR_WIDTH</c> = 6; <c>DEPTH</c> = 64",
              "Operand width and bank size"],
             ["Memory inference", "<c>(* ram_style = \"block\" *)</c> on each bank array",
              "Force RAMB18E1 inference"],
             ["Simulation clock", "100 MHz (<c>always #5 clk = ~clk</c>, period 10 ns)",
              "Behavioural simulation only"],
             ["Roadmap hardware", "Zynq-7000 board with ARM Cortex-A9 PS; JTAG/SD boot", "Board deployment"],
             ["Roadmap software", "Vivado IP Integrator, Vitis (bare-metal) or PetaLinux", "Software control of the IP"]],
            [1.35, 3.05, 1.87], size=9.5)

    # ---------------------------------------------------------------- 3.3
    R.h2("3.3 Development workflow")
    R.p("Figure 3.1 shows the development workflow. The solid boxes are the steps carried out and reported in "
        "this project; the dashed boxes are the system-integration steps that continue from the same "
        "RTL baseline. The flow is deliberately linear for the implemented part: each stage produces an "
        "artefact (a mathematical model, RTL files, a waveform, a utilisation/timing/power report) that is "
        "the input to the next, which keeps every reported number traceable to a specific source file and "
        "tool run.")
    R.figure(os.path.join(FIG, "gen_fig_workflow.png"), "Development workflow of the Sparse-CIM accelerator", 6.2)

    # ---------------------------------------------------------------- 3.4
    R.h2("3.4 SpMVM formulation and sparse-data preparation")
    R.p("Let <i>A</i> ∈ ℤ<sup><i>M</i>×<i>N</i></sup> be the INT8 weight matrix, <i>x</i> "
        "∈ ℤ<sup><i>N</i></sup> the INT8 activation vector and NNZ the number of non-zero entries "
        "of <i>A</i>. The dense product is")
    R.eq("<i>y</i><sub><i>i</i></sub> = ∑<sub><i>j</i>=0</sub><sup><i>N</i>−1</sup> "
         "<i>A</i><sub><i>ij</i></sub> <i>x</i><sub><i>j</i></sub>,   <i>i</i> = 0, …, <i>M</i>−1")
    R.p("<b>CSR representation.</b> Compressed Sparse Row storage [@saad2003] represents <i>A</i> by three "
        "one-dimensional arrays: <c>values</c> (length NNZ), the non-zero elements in row-major order; "
        "<c>col_idx</c> (length NNZ), the column index of each stored value; and <c>row_ptr</c> (length "
        "<i>M</i> + 1), where <c>row_ptr[i]</c> is the index in <c>values</c> of the first non-zero of row "
        "<i>i</i> and <c>row_ptr[M]</c> = NNZ. The number of non-zeros in row <i>i</i> is "
        "<c>row_ptr[i+1]</c> − <c>row_ptr[i]</c>. With these arrays the product becomes")
    R.eq("<i>y</i><sub><i>i</i></sub> = ∑<sub><i>k</i>=<c>row_ptr[i]</c></sub><sup><c>row_ptr[i+1]</c>−1</sup> "
         "<c>values[k]</c> · <i>x</i><sub><c>col_idx[k]</c></sub>")
    R.p("<i>Equivalence.</i> Every term of the dense sum with <i>A</i><sub><i>ij</i></sub> = 0 contributes "
        "zero and may be omitted without changing <i>y</i><sub><i>i</i></sub>; every term with "
        "<i>A</i><sub><i>ij</i></sub> ≠ 0 is stored exactly once, at some position <i>k</i> in row "
        "<i>i</i>'s segment, with <c>col_idx[k]</c> = <i>j</i>. Hence the two sums are identical, and the "
        "number of multiplications falls from <i>MN</i> to NNZ.")
    R.figure(os.path.join(FIG, "ises_fig1.png"), "SpMVM using CSR representation for the 4 × 4 example "
             "(from the iSES paper): <i>A</i>, <i>x</i>, the three CSR arrays and the zero-skipping computation", 3.9)
    R.p("<b>Worked example (Figure 3.2).</b> For the 4 × 4 matrix <i>A</i> with rows (5, 0, 0, 2), "
        "(0, 0, 1, 0), (0, 6, 0, 0), (8, 0, 0, 4) and <i>x</i> = (1, 2, 3, 4)<sup>T</sup>, "
        "NNZ = 6, <c>values</c> = [5, 2, 1, 6, 8, 4], <c>col_idx</c> = [0, 3, 2, 1, 0, 3] and "
        "<c>row_ptr</c> = [0, 2, 3, 4, 6]. Evaluating row by row gives <i>y</i><sub>0</sub> = 5(1) + 2(4) = 13, "
        "<i>y</i><sub>1</sub> = 1(3) = 3, <i>y</i><sub>2</sub> = 6(2) = 12 and <i>y</i><sub>3</sub> = 8(1) + 4(4) = 24, "
        "so <i>y</i> = (13, 3, 12, 24)<sup>T</sup>. Six multiplications replace sixteen; the ten skipped "
        "operations are exactly the multiplications by zero.")
    R.h3("Storage bit-width derivation")
    R.p("Let <i>b</i><sub><i>v</i></sub> be the bit-width of a stored value (8 for INT8), and define the "
        "minimum index widths")
    R.eq("<i>b</i><sub><i>c</i></sub> = ⌈log<sub>2</sub> <i>N</i>⌉,   "
         "<i>b</i><sub><i>r</i></sub> = ⌈log<sub>2</sub> <i>M</i>⌉,   "
         "<i>b</i><sub><i>p</i></sub> = ⌈log<sub>2</sub>(NNZ + 1)⌉")
    R.p("where <i>b</i><sub><i>c</i></sub> addresses a column, <i>b</i><sub><i>r</i></sub> a row and "
        "<i>b</i><sub><i>p</i></sub> a position in the <c>values</c> array (a row pointer must be able to take "
        "any value in 0…NNZ). The storage of the four formats is then")
    R.eq("<i>S</i><sub>Dense</sub> = <i>MN</i> <i>b</i><sub><i>v</i></sub>")
    R.eq("<i>S</i><sub>CSR</sub> = NNZ <i>b</i><sub><i>v</i></sub> + NNZ <i>b</i><sub><i>c</i></sub> + "
         "(<i>M</i> + 1) <i>b</i><sub><i>p</i></sub>")
    R.eq("<i>S</i><sub>COO</sub> = NNZ (<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>r</i></sub> + "
         "<i>b</i><sub><i>c</i></sub>)")
    R.eq("<i>S</i><sub>CSC</sub> = NNZ <i>b</i><sub><i>v</i></sub> + NNZ <i>b</i><sub><i>r</i></sub> + "
         "(<i>N</i> + 1) <i>b</i><sub><i>p</i></sub>")
    d = storage_bits(4, 4, 6)
    R.p(f"For the 4 × 4 example (<i>b</i><sub><i>c</i></sub> = <i>b</i><sub><i>r</i></sub> = 2, "
        f"<i>b</i><sub><i>p</i></sub> = 3) these evaluate to <i>S</i><sub>Dense</sub> = {d['dense']} bits, "
        f"<i>S</i><sub>CSR</sub> = 48 + 12 + 15 = {d['csr']} bits, <i>S</i><sub>COO</sub> = 6(8 + 2 + 2) = "
        f"{d['coo']} bits and <i>S</i><sub>CSC</sub> = 48 + 12 + 15 = {d['csc']} bits. The implemented banks "
        "use byte-wide index words (the BRAM word is 8 bits regardless of the minimum index width), so the "
        "physical CSR footprint of this tiny example is 6·8 + 6·8 + 5·8 = 136 bits; the "
        "saving appears for the larger, sparser tiles for which the core is intended (Section 3.6 and "
        "Chapter 5).")
    R.h3("Index-overhead threshold")
    R.p("CSR is smaller than dense storage when <i>S</i><sub>CSR</sub> < <i>S</i><sub>Dense</sub>. Writing the "
        "density ρ = NNZ/(<i>MN</i>) and neglecting the row-pointer term (which is (<i>M</i> + 1) "
        "<i>b</i><sub><i>p</i></sub>, small compared with NNZ values for tiles that are not hypersparse), the "
        "condition is NNZ (<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>c</i></sub>) < <i>MN</i> "
        "<i>b</i><sub><i>v</i></sub>, that is")
    R.eq("ρ < ρ* ≈ <i>b</i><sub><i>v</i></sub> / (<i>b</i><sub><i>v</i></sub> + "
         "<i>b</i><sub><i>c</i></sub>)")
    R.p("For <i>b</i><sub><i>v</i></sub> = 8 and a 64-column tile (<i>b</i><sub><i>c</i></sub> = 6), "
        "ρ* = 8/14 ≈ 57 %, i.e. CSR wins at sparsity above about 43 %. With byte-wide index words "
        "(<i>b</i><sub><i>c</i></sub> = 8) ρ* = 50 %. The COO break-even is lower, ρ*<sub>COO</sub> "
        "= 8/(8 + 6 + 6) = 40 %, because COO stores a row index for every non-zero instead of a short "
        "row-pointer array. CSR is smaller than COO whenever (<i>M</i> + 1) <i>b</i><sub><i>p</i></sub> < "
        "NNZ <i>b</i><sub><i>r</i></sub>, which holds for every tile with more than a few non-zeros per row; "
        "COO is preferable only for hypersparse matrices with NNZ ≈ <i>M</i> or smaller. CSC mirrors CSR "
        "with the roles of rows and columns exchanged.")
    R.table("Storage formats for an <i>M</i> × <i>N</i> matrix with NNZ non-zeros",
            ["Format", "Arrays stored", "Storage (bits)", "Row-wise SpMVM fit"],
            [["Dense", "all <i>MN</i> elements", "<i>MN</i> <i>b</i><sub><i>v</i></sub>",
              "Trivial, but multiplies every zero"],
             ["CSR", "<c>values</c>, <c>col_idx</c>, <c>row_ptr</c> (<i>M</i> + 1)",
              "NNZ(<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>c</i></sub>) + (<i>M</i> + 1)<i>b</i><sub><i>p</i></sub>",
              "Best: one row yields one <i>y</i><sub><i>i</i></sub> with a local accumulator"],
             ["COO", "<c>values</c>, <c>row_idx</c>, <c>col_idx</c>",
              "NNZ(<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>r</i></sub> + <i>b</i><sub><i>c</i></sub>)",
              "Needs row-change detection; larger index stream"],
             ["CSC", "<c>values</c>, <c>row_idx</c>, <c>col_ptr</c> (<i>N</i> + 1)",
              "NNZ(<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>r</i></sub>) + (<i>N</i> + 1)<i>b</i><sub><i>p</i></sub>",
              "Column-major: scatter-accumulates into <i>y</i> (random writes)"]],
            [0.7, 1.95, 2.1, 1.52], size=9.5)
    R.p("CSR is chosen for this design for a structural reason in addition to the storage comparison of "
        "Table 3.2. The row-wise dataflow produces each <i>y</i><sub><i>i</i></sub> in one contiguous run "
        "of non-zeros, so a single accumulator register suffices and the output is written once per row; "
        "CSC would require a read-modify-write of <i>y</i> for every non-zero. The <c>bank_vector</c> read "
        "indexed by <c>col_idx</c> is then an ordinary BRAM read.")
    R.p("<b>Sparse-data preparation.</b> Preparation is a software step performed offline (or by the host "
        "processor): quantise the pruned weights to INT8, scan <i>A</i> row-major, append each non-zero "
        "to <c>values</c> and its column to <c>col_idx</c>, and record the running count at each row start in "
        "<c>row_ptr</c>. The three arrays and the dense vector are then written into the BRAM banks through "
        "Port B. For the implemented single-row core, a row's arrays occupy addresses 0…NNZ−1 and "
        "<c>nnz_count</c> = NNZ of that row.")

    # ---------------------------------------------------------------- 3.5
    R.h2("3.5 Proposed near-memory accelerator architecture")
    R.h3("In-memory computing versus near-memory computing on FPGAs")
    R.p("<b>What true IMC is.</b> In an analog SRAM in-memory-computing macro [@verma2019], [@jhang2021], the "
        "6T bit-cell array that stores the weights is also the multiplier array. Input activations are "
        "applied as word-line voltages or pulse widths on many rows <i>simultaneously</i>; each bit-cell "
        "conditionally discharges (or sources current onto) its bit-line according to the stored bit; the "
        "bit-line voltage or accumulated charge is therefore the analog sum ∑ <i>w</i><sub><i>i</i></sub> "
        "<i>x</i><sub><i>i</i></sub> of the products along a column, and an ADC at the column periphery "
        "converts it to a digital word. The same mechanism underlies resistive-memory crossbars "
        "[@sebastian2020]. The weights never leave the array, which is the source of the energy advantage.")
    R.p("<b>Why it is native to custom ASIC macros.</b> Doing this requires (i) a custom bit-cell and array "
        "layout in which multiple word-lines can be asserted at once without destroying the stored data, "
        "(ii) analog periphery — word-line DACs or pulse generators, column ADCs, reference generators and "
        "calibration — sized for the precision targeted, and (iii) an analysis of noise, mismatch and "
        "non-linearity over process, voltage and temperature. These are decisions made at the transistor and "
        "layout level of an ASIC.")
    R.p("<b>Why it is impractical on commercial FPGAs.</b> The block RAM of a 7-series FPGA is a hard macro "
        "whose bit-cells, bit-lines and sense amplifiers are enclosed behind a fixed synchronous interface: "
        "an address and enable go in, a registered word comes out one clock later [@ug473]. Only one word "
        "line per port is activated per access, the bit-lines are not accessible, there is no analog "
        "periphery to repurpose, and the programmable logic around it is purely digital and clocked. "
        "Multi-row analog accumulation inside the RAM array is therefore simply not expressible in the "
        "fabric. (Digital variants of IMC, which add logic to the array, are likewise ASIC-level "
        "modifications.)")
    R.p("<b>The practical FPGA equivalent: BRAM-centric near-memory computing.</b> What an FPGA does offer "
        "is the ability to place arbitrary logic <i>immediately adjacent to the memory port</i> and to "
        "connect it with dedicated, short routing. The Sparse-CIM architecture exploits this in three ways:")
    R.bullets([
        "<b>Compute at the read port.</b> The controller drives the BRAM addresses and consumes the "
        "registered BRAM outputs in the very next cycle; the zero-skipping control logic "
        "(<c>sparse_cim_controller</c>) and the signed INT8 arithmetic unit (<c>mac_unit</c>) sit directly "
        "on the <c>douta</c> buses of <c>bank_values</c>, <c>bank_col_idx</c> and <c>bank_vector</c>. No "
        "FIFO, cache or off-chip transfer intervenes.",
        "<b>Dedicated ports.</b> Port A of every bank is reserved for the accelerator and Port B for "
        "preloading, so that once <c>start</c> is asserted the engine has uncontested access to its operands.",
        "<b>Compute proportional to data, not to the dense shape.</b> Because the controller walks the "
        "compressed arrays, every BRAM read and every MAC corresponds to a stored non-zero.",
    ])
    R.p("The result is a design that is <i>near</i> memory rather than <i>in</i> memory: the weight still "
        "traverses a few hundred picoseconds to a nanosecond of programmable routing between the RAM macro "
        "and the multiplier, and costs the read energy of the RAM. In exchange the arithmetic is exact "
        "digital INT8, timing is deterministic, the design is reconfigurable and it is realisable today on a "
        "low-cost commercial device with standard tools. This is the sense in which the design is a “Sparse "
        "Compute-in-Memory” engine on FPGA: it realises the CIM dataflow (static weights resident next "
        "to the compute, no weight traffic from DRAM) with the near-memory mechanism that the platform allows.")
    R.figure(os.path.join(FIG, "ises_fig2.png"), "System-level block diagram of the Sparse-CIM engine (from "
             "the iSES paper): the FSM controller routes addresses to three BRAM banks and operands to the MAC unit", 4.7)
    R.p("Figure 3.3 shows the architecture. The top module <c>sparse_cim_top</c> instantiates five blocks: "
        "one <c>sparse_cim_controller</c>, one <c>mac_unit</c> and three <c>bram_bank</c> instances. It is "
        "listed in full in Listing 3.1 and explained signal by signal below.")
    R.code("sparse_cim_top.sv – top-level module integrating the controller, the MAC unit and the three BRAM banks",
           sv("sparse_cim_top.sv"))
    R.h3("Port-by-port explanation of sparse_cim_top")
    R.defs([
        ("clk", "common clock for the controller, MAC and all three BRAM banks (single synchronous domain)."),
        ("rst_n", "active-low asynchronous reset, forwarded to the controller and to the MAC; the BRAM banks "
         "have no reset (their contents are preloaded)."),
        ("start", "level-sensitive request from the host or testbench; the FSM leaves IDLE only when "
         "<c>start</c> = 1 and <c>nnz_count</c> > 0, and leaves DONE_STATE only after <c>start</c> falls."),
        ("nnz_count [ADDR_WIDTH-1:0]", "number of stored non-zeros to process in this invocation "
         "(at most 63 for the 6-bit instance); it must be stable while the FSM runs."),
        ("final_result [31:0] (signed)", "output of the 32-bit accumulator, valid while <c>done</c> = 1."),
        ("done", "high in DONE_STATE; tells the host that <c>final_result</c> is final."),
        ("web_val, web_col, web_vec", "independent Port B write enables of the value, column-index and "
         "vector banks; they let a different address be written in each bank in the same cycle phase."),
        ("addrb [ADDR_WIDTH-1:0]", "shared Port B write address for the three banks."),
        ("dinb_val, dinb_col, dinb_vec [DATA_WIDTH-1:0]", "Port B write data for the value, column-index "
         "and vector banks respectively."),
    ])
    R.h3("Internal wires")
    R.defs([
        ("val_addr", "Port A read address of <c>bank_values</c> and <c>bank_col_idx</c>; driven by the "
         "controller (equal to its non-zero pointer)."),
        ("vec_addr", "Port A read address of <c>bank_vector</c>; driven by the controller from the column "
         "index (indirect addressing)."),
        ("val_data, col_data, vec_data", "registered Port A outputs (<c>douta</c>) of the three banks."),
        ("mac_en, mac_clr", "enable and synchronous clear of the accumulator, generated by the controller."),
        ("mac_weight, mac_act [7:0] (signed)", "operands passed from the controller to the MAC; both are "
         "declared signed so the multiplication is two's-complement."),
    ])
    R.p("<b>Instance wiring.</b> The controller is instantiated with the same <c>ADDR_WIDTH</c> and "
        "<c>DATA_WIDTH</c> as the banks. The MAC output <c>acc_out</c> is connected directly to the top-level "
        "port <c>final_result</c>. <c>bank_values</c> and <c>bank_col_idx</c> share <c>val_addr</c> on "
        "Port A so that the weight and its column index are read together in one cycle; "
        "<c>bank_vector</c> takes the independent <c>vec_addr</c>. All three banks tie <c>ena</c> and "
        "<c>enb</c> to 1 and differ only in their write enable and data. The comment in the source records "
        "the intended use: in a real SoC the ARM processor, through an AXI BRAM controller, would drive "
        "the Port B signals.")

    # ---------------------------------------------------------------- 3.6
    R.h2("3.6 Sparse computational cost and data movement")
    R.p("Let the matrix be <i>M</i> × <i>N</i> with density ρ and sparsity <i>s</i> = 1 − ρ, "
        "so NNZ = ρ<i>MN</i>. The number of multiply–accumulate operations is")
    R.eq("<i>C</i><sub>dense</sub> = <i>MN</i>,   <i>C</i><sub>CSR</sub> = NNZ = (1 − <i>s</i>) <i>MN</i>")
    R.p("The ratio is exactly 1/(1 − <i>s</i>): at 90 % sparsity the engine performs one tenth of the "
        "operations. Memory traffic follows the same law. A dense engine with the vector held in BRAM reads "
        "<i>MN</i> weights and <i>MN</i> vector elements; the CSR engine reads, per non-zero, one value, one "
        "column index and one vector element, plus <i>M</i> + 1 row pointers per pass:")
    R.eq("<i>R</i><sub>dense</sub> = 2<i>MN</i> words,   <i>R</i><sub>CSR</sub> = 3 NNZ + (<i>M</i> + 1) words")
    R.p("In bits, with <i>b</i><sub><i>x</i></sub> = 8 for the vector and the minimum widths of Section 3.4,")
    R.eq("<i>B</i><sub>CSR</sub> = NNZ (<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>c</i></sub> + "
         "<i>b</i><sub><i>x</i></sub>) + (<i>M</i> + 1) <i>b</i><sub><i>p</i></sub>,   "
         "<i>B</i><sub>dense</sub> = <i>MN</i> (<i>b</i><sub><i>v</i></sub> + <i>b</i><sub><i>x</i></sub>)")
    M = N = 64
    nnz = 410
    sb = storage_bits(M, N, nnz)
    bp = clog2(nnz + 1)
    B_csr = nnz * (8 + 6 + 8) + (M + 1) * bp
    B_den = M * N * 16
    R.p(f"Table 3.3 evaluates these expressions for a 64 × 64 INT8 tile at 90 % sparsity "
        f"(NNZ = {nnz}, <i>b</i><sub><i>c</i></sub> = 6, <i>b</i><sub><i>p</i></sub> = {bp}) and also gives the "
        "cycle counts of the three-cycle PE of this report (Section 5.9). The numerical instance uses "
        "<c>ADDR_WIDTH</c> larger than the 6 bits of the synthesised instance, since the 6-bit-address "
        "instance holds at most 63 non-zeros; the parameterisation is described in Section 3.8.")
    R.table("Computation and data-movement cost, dense versus CSR (64 × 64 INT8 tile, 90 % sparsity)",
            ["Quantity", "Dense", "CSR (this design)", "Ratio"],
            [["MAC operations", f"{M*N:,}", f"{nnz}", f"{M*N/nnz:.1f}× fewer"],
             ["Weight words read", f"{M*N:,}", f"{nnz}", f"{M*N/nnz:.1f}× fewer"],
             ["Index words read (col_idx + row_ptr)", "0", f"{nnz} + {M+1}", "–"],
             ["Vector words read", f"{M*N:,}", f"{nnz}", f"{M*N/nnz:.1f}× fewer"],
             ["Bits read per product", f"{B_den:,}", f"{B_csr:,}", f"{B_den/B_csr:.1f}× fewer"],
             ["Weight storage (bits)", f"{sb['dense']:,}", f"{sb['csr']:,}", f"{sb['dense']/sb['csr']:.1f}× smaller"],
             ["Cycles, 3-cycle PE (<i>T</i>)", f"{3*M*N+2:,} (dense scan)", f"{cycles_for(nnz):,}",
              f"{(3*M*N+2)/cycles_for(nnz):.1f}× faster"]],
            [2.3, 1.35, 1.5, 1.12], size=9.5, aligns=["l", "r", "r", "r"])
    R.p("The table shows the central trade of the architecture: CSR adds an index word per non-zero and a "
        "short pointer array, but at 90 % sparsity this overhead is dwarfed by the order-of-magnitude "
        "reduction in weight words, vector words and MACs. Because all of these reads are served by "
        "on-chip BRAM, the energy of each avoided access is the BRAM read energy rather than a DRAM "
        "access, and the saving is realised without any off-chip bandwidth at all.")

    # ---------------------------------------------------------------- 3.7
    R.h2("3.7 Test-data preparation and expected-result construction")
    R.p("Two data sets are used. The first is the 4 × 4 <b>paper example</b> of Figure 3.2, which "
        "validates the formulation and gives the expected output vector <i>y</i> = (13, 3, 12, 24)<sup>T</sup>. "
        "For the single-row core, each row is one invocation: row 0 is loaded as <c>values</c> = [5, 2], "
        "<c>col_idx</c> = [0, 3] and the vector bank as [1, 2, 3, 4] with <c>nnz_count</c> = 2, and the "
        "expected <c>final_result</c> is 5(1) + 2(4) = 13. Rows 1–3 are loaded in the same way with "
        "<c>nnz_count</c> = 1, 1 and 2, giving 3, 12 and 24. The <c>row_ptr</c> array [0, 2, 3, 4, 6] "
        "supplies the <c>nnz_count</c> of each row as the difference of successive entries and is the "
        "input of the multi-row extension (Section 3.10).")
    R.p("The second data set is the <b>directed test</b> used by <c>tb_sparse_cim_top</c>, chosen to "
        "exercise the two properties that matter most for the datapath: a negative weight and indirect "
        "addressing with a non-trivial column index. Two non-zero elements are stored at pointer addresses 0 "
        "and 1: weight 5 with column 0, and weight −4 with column 2. The dense vector bank holds "
        "<i>x</i>[0] = 3 and <i>x</i>[2] = 2. The expected result is")
    R.eq("5 · <i>x</i>[0] + (−4) · <i>x</i>[2] = 5(3) + (−4)(2) = 15 − 8 = 7")
    R.p("with the accumulator passing through the intermediate value 15 after the first non-zero. Because "
        "the second column index is 2 rather than 1, a design that simply read the vector sequentially would "
        "fetch the wrong element and produce a different result; the test therefore verifies the indirect "
        "<c>vec_addr</c> path. The expected values are constructed by hand (and are reproduced by the "
        "cycle-accurate reference model used in Section 5.1), which is appropriate for a directed test; "
        "Section 3.16 describes the automatic golden-model comparison that extends this to randomised "
        "matrices.")

    # ---------------------------------------------------------------- 3.8
    R.h2("3.8 Parameterization and signed numerical representation")
    R.p("The design is parameterised by three integers, <c>DATA_WIDTH</c> = 8, <c>ADDR_WIDTH</c> = 6 and "
        "<c>DEPTH</c> = 64, with the constraint <c>DEPTH</c> ≤ 2<sup><c>ADDR_WIDTH</c></sup>. "
        "Changing them rescales the banks and the pointer logic without rewriting the control flow. The "
        "arithmetic widths, by contrast, are fixed by the INT8 design point: 8-bit signed operands, a 16-bit "
        "product and a 32-bit accumulator. Table 3.4 collects these quantities and their consequences.")
    R.table("Parameters and signal widths of the Sparse-CIM core",
            ["Quantity", "Value", "Meaning / consequence"],
            [["<c>DATA_WIDTH</c>", "8", "Width of every BRAM word: INT8 weight, column index, vector element"],
             ["<c>ADDR_WIDTH</c>", "6", "Pointer, <c>val_addr</c>, <c>vec_addr</c>, <c>addrb</c>, <c>nnz_count</c> width"],
             ["<c>DEPTH</c>", "64", "Words per bank: 512 bits, one RAMB18E1 each"],
             ["Maximum NNZ per call", "63", "<c>nnz_count</c> is 6 bits wide, so the largest value is 63"],
             ["Maximum vector length", "64", "<c>vec_addr</c> = <c>col_data[5:0]</c> addresses 64 entries"],
             ["<c>mac_weight</c>, <c>mac_act</c>", "signed [7:0]", "Range −128…127, two's complement"],
             ["<c>product</c>", "signed [15:0]", "Exact: |product| ≤ 16,384 < 2<sup>15</sup>"],
             ["<c>acc_out</c> / <c>final_result</c>", "signed [31:0]", "No overflow for fewer than 131,072 products"],
             ["Controller state / pointer", "3 bits / 6 bits", "Together with 32 accumulator bits: 41 FDCE flip-flops"]],
            [1.9, 1.15, 3.22], size=9.5)
    R.p("<b>Two's-complement handling.</b> The ports <c>weight_in</c> and <c>act_in</c> of <c>mac_unit</c> and "
        "the controller outputs <c>mac_weight</c> and <c>mac_act</c> are declared <c>logic signed [7:0]</c>, "
        "and <c>product</c> is <c>logic signed [15:0]</c>. In <c>product = weight_in * act_in</c> both operands "
        "are signed, so the expression is evaluated as a signed multiplication whose width is determined "
        "by the 16-bit target and the result is correct for negative operands. For the directed test the weight "
        "−4 is stored in the BRAM as the byte <c>8'hFC</c> (two's complement of 4); the controller assigns "
        "<c>mac_weight = val_data</c>, reinterpreting the bits as the signed value −4, and the product "
        "with 2 is the 16-bit pattern <c>16'hFFF8</c> = −8.")
    R.p("<b>Sign-preserving widening.</b> The accumulate statement <c>acc_out <= acc_out + 32'(product)</c> "
        "uses the SystemVerilog size cast. A size cast preserves the signedness of its operand, so "
        "<c>32'(product)</c> sign-extends: <c>16'hFFF8</c> becomes <c>32'hFFFFFFF8</c> = −8, and the "
        "32-bit addition 15 + (−8) = 7 is exact. Had the product been zero-extended, the sum would be "
        "15 + 65,528 = 65,543; the explicit cast, noted in the source as “for safety”, removes this "
        "ambiguity.")

    # ---------------------------------------------------------------- 3.9
    R.h2("3.9 BRAM organization and operand storage")
    R.p("Listing 3.2 gives the complete <c>bram_bank</c> module, the parameterised dual-port memory used for "
        "all three operand arrays.")
    R.code("bram_bank.sv – parameterised dual-port block-RAM bank (Port A read, Port B write)", sv("bram_bank.sv"))
    R.h3("Signal-by-signal explanation")
    R.defs([
        ("clk", "single clock for both ports."),
        ("ena, addra, douta (Port A)", "read port: when <c>ena</c> = 1, <c>mem[addra]</c> is loaded into the "
         "output register <c>douta</c> at each rising edge, so <c>douta</c> reflects the address presented in "
         "the <i>previous</i> cycle — a one-cycle synchronous read latency."),
        ("enb, web, addrb, dinb (Port B)", "write port: when both <c>enb</c> and <c>web</c> are 1, "
         "<c>dinb</c> is written to <c>mem[addrb]</c> at the rising edge; <c>web</c> = 0 performs no access."),
    ])
    R.p("<b>Memory inference.</b> The array is declared "
        "<c>(* ram_style = \"block\" *) logic [DATA_WIDTH-1:0] mem [0:DEPTH-1]</c>. The attribute instructs "
        "Vivado synthesis to implement the array in a block RAM rather than in distributed (LUT) RAM or "
        "flip-flops [@ug901]. Together with the registered-read coding style of the Port A "
        "<c>always_ff</c> block (the read value passes through a register, not combinationally to the "
        "output), this maps onto the synchronous read of a RAMB18E1 with its output latch, and the write "
        "<c>always_ff</c> block maps onto the second port [@ug473]. Each bank holds 64 × 8 = 512 bits and "
        "therefore occupies one RAMB18E1; the three banks account exactly for the three RAMB18E1 primitives "
        "reported in Chapter 5.")
    R.p("<b>Port discipline.</b> Port A is read-only and is dedicated to the accelerator (the controller "
        "never writes it); Port B is write-only and is dedicated to the preload path. Two consequences "
        "follow. First, once <c>start</c> is asserted the accelerator is the only reader and no arbitration "
        "logic is needed, which gives the deterministic single-cycle read access the schedule depends on. "
        "Second, because the memory has two independent ports on one clock, a host may in principle write the "
        "next layer's data while the current one is processed, provided the written region is not being read; "
        "the present protocol conservatively preloads before <c>start</c>.")
    R.p("<b>Three instantiated banks.</b> <c>sparse_cim_top</c> instantiates the module three times:")
    R.bullets([
        "<c>bank_values</c> – the CSR non-zero INT8 weights, read at <c>val_addr</c>;",
        "<c>bank_col_idx</c> – the column index of each non-zero, read at the same <c>val_addr</c> so "
        "weight and index arrive together;",
        "<c>bank_vector</c> – the dense input vector, read at <c>vec_addr</c> derived from "
        "<c>col_data</c>.",
    ])
    R.p("The banks have no reset and no initial contents in the RTL; they are filled through Port B before "
        "each run. A read of a never-written location returns an undefined value in simulation, and the "
        "protocol guarantees that only written locations are read (addresses below <c>nnz_count</c> and the "
        "column indices stored by the host).")

    # ---------------------------------------------------------------- 3.10
    R.h2("3.10 Sparsity-aware control-unit FSM")
    R.figure(os.path.join(FIG, "ises_fig3.png"), "State-transition diagram of the sparsity-aware FSM "
             "(from the iSES paper)", 2.55)
    R.p("The controller is a Moore-style five-state FSM whose structure is shown in Figure 3.4. A reset places "
        "it in IDLE. When <c>start</c> is high and <c>nnz_count</c> is non-zero it enters FETCH_PTR, then "
        "unconditionally passes through FETCH_VEC and COMPUTE; at the end of COMPUTE it either returns to "
        "FETCH_PTR for the next non-zero or, when the pointer equals <c>nnz_count</c> − 1, enters "
        "DONE_STATE. DONE_STATE holds until the host lowers <c>start</c>, then returns to IDLE. The complete "
        "source is given in Listing 3.3.")
    R.code("sparse_cim_controller.sv – five-state sparsity-aware controller", sv("sparse_cim_controller.sv"))
    R.h3("Line-by-line explanation")
    R.p("<b>Declarations (lines 3–33).</b> The module is parameterised by <c>ADDR_WIDTH</c> and "
        "<c>DATA_WIDTH</c>. Inputs <c>clk</c>, <c>rst_n</c>, <c>start</c> and <c>nnz_count</c> come from the "
        "host; <c>val_data</c>, <c>col_data</c> and <c>vec_data</c> are the registered BRAM outputs. Outputs "
        "<c>val_addr</c> and <c>vec_addr</c> address the BRAMs; <c>mac_en</c>, <c>mac_clr</c>, "
        "<c>mac_weight</c> and <c>mac_act</c> drive the MAC; <c>done</c> is the status flag.")
    R.p("<b>State type (lines 36–42).</b> <c>typedef enum logic [2:0]</c> declares five states encoded "
        "by default as 3'd0 (IDLE), 3'd1 (FETCH_PTR), 3'd2 (FETCH_VEC), 3'd3 (COMPUTE) and 3'd4 "
        "(DONE_STATE); <c>current_state</c> and <c>next_state</c> are the state register and its next "
        "value, and <c>current_ptr</c> (line 47) is the index of the non-zero being processed.")
    R.p("<b>Sequential block (lines 52–66).</b> On the falling edge of <c>rst_n</c> the state register "
        "returns to IDLE and the pointer to 0 (asynchronous reset). Otherwise at every rising edge "
        "<c>current_state</c> takes <c>next_state</c>; the pointer is incremented in the cycle that ends "
        "COMPUTE (<c>current_state == COMPUTE</c>) and cleared while the FSM is in IDLE. The pointer is "
        "therefore updated only after a MAC has consumed the corresponding operands.")
    R.p("<b>Combinational block (lines 71–129).</b> The default assignments at lines 73–80 "
        "(<c>next_state = current_state</c>, <c>val_addr = current_ptr</c>, all other outputs 0) guarantee "
        "that every output is assigned on every path, which prevents latch inference in synthesis. "
        "Notably <c>val_addr</c> equals <c>current_ptr</c> in <i>every</i> state, so the value and "
        "column-index banks are continuously reading the current non-zero. The state-specific behaviour is:")
    R.bullets([
        "<b>IDLE</b> asserts <c>mac_clr</c> so the accumulator rests at zero, and moves to FETCH_PTR when "
        "<c>start</c> && <c>nnz_count</c> > 0 (lines 83–88).",
        "<b>FETCH_PTR</b> presents <c>val_addr</c> = <c>current_ptr</c> and waits one cycle for the BRAM "
        "latency (lines 90–96).",
        "<b>FETCH_VEC</b> uses the now-valid <c>col_data</c> as the address of <c>bank_vector</c>: "
        "<c>vec_addr = col_data[ADDR_WIDTH-1:0]</c> (lines 98–103).",
        "<b>COMPUTE</b> forwards <c>val_data</c> and <c>vec_data</c> to <c>mac_weight</c> and "
        "<c>mac_act</c>, asserts <c>mac_en</c>, and decides between DONE_STATE (<c>current_ptr == "
        "nnz_count - 1</c>) and FETCH_PTR (lines 105–117).",
        "<b>DONE_STATE</b> asserts <c>done</c> and waits for <c>!start</c> before returning to IDLE "
        "(lines 119–125); the <c>default</c> branch returns to IDLE from any unused encoding.",
    ])
    R.table("States of the five-state sparsity-aware controller",
            ["State", "Encoding", "Outputs asserted", "Next state", "Cycles"],
            [["IDLE", "000", "<c>mac_clr</c> = 1", "FETCH_PTR if <c>start</c> && <c>nnz_count</c> > 0; else IDLE", "1 (while waiting)"],
             ["FETCH_PTR", "001", "<c>val_addr</c> = ptr", "FETCH_VEC", "1"],
             ["FETCH_VEC", "010", "<c>vec_addr</c> = <c>col_data</c>[5:0]", "COMPUTE", "1"],
             ["COMPUTE", "011", "<c>mac_en</c> = 1, <c>mac_weight</c> = <c>val_data</c>, <c>mac_act</c> = <c>vec_data</c>",
              "DONE_STATE if ptr = nnz − 1; else FETCH_PTR", "1"],
             ["DONE_STATE", "100", "<c>done</c> = 1", "IDLE when <c>start</c> = 0; else DONE_STATE", "≥ 1"]],
            [1.0, 0.7, 1.9, 1.9, 0.77], size=9, aligns=["l", "c", "l", "l", "c"])
    R.p("Table 3.5 summarises the five states. Each stored non-zero traverses FETCH_PTR, FETCH_VEC and "
        "COMPUTE once, which is the origin of the three-cycles-per-non-zero rule derived in Section 3.11.")
    R.h3("Multi-row CSR extension: the six-state scaling framework")
    R.p("The implemented core evaluates one compressed row per invocation. Extending it to a full matrix "
        "is a controlled evolution of the same schedule rather than a new design. The scaling framework adds "
        "a <c>row_ptr</c> BRAM bank, a result BRAM bank, a row counter and a six-state FSM:")
    R.numbered([
        "<b>IDLE</b> – wait for <c>start</c>; clear the row counter and accumulator.",
        "<b>FETCH_ROW_PTR</b> – read <c>row_ptr[r + 1]</c> (the start pointer is the previous end); "
        "form the row length; an empty row branches directly to WRITEBACK with a zero result.",
        "<b>STREAM_CSR</b> – the existing FETCH_PTR/FETCH_VEC pair: issue the value/column address, wait "
        "the BRAM latency, issue the vector address.",
        "<b>MAC_ACCUM</b> – the existing COMPUTE state: enable the MAC and increment the pointer; "
        "repeat STREAM_CSR/MAC_ACCUM until the pointer reaches <c>row_ptr[r + 1]</c>.",
        "<b>WRITEBACK</b> – write the accumulator into the result bank at address <i>r</i>, pulse "
        "<c>clr_acc</c> and increment <i>r</i>; continue with FETCH_ROW_PTR or finish when <i>r</i> = "
        "<c>row_count</c>.",
        "<b>DONE</b> – assert <c>done</c> and wait for <c>start</c> to fall, exactly as DONE_STATE does today.",
    ], fmt="{}.")
    R.p("Because STREAM_CSR and MAC_ACCUM are the present FETCH_PTR/FETCH_VEC and COMPUTE states, the "
        "datapath, the BRAM banks and the three-cycle inner schedule are reused unchanged; only the outer "
        "loop is new. Listing 3.4 gives the intended state skeleton.")
    R.code("Conceptual skeleton of the six-state multi-row CSR controller (scaling framework; "
           "not part of the synthesised five-state core)",
           """typedef enum logic [2:0] {
    IDLE, FETCH_ROW_PTR, STREAM_CSR, MAC_ACCUM, WRITEBACK, DONE
} mstate_t;

always_comb begin
    next_state = state;  wr_en = 0;  mac_clr = 0;  mac_en = 0;  done = 0;
    case (state)
        IDLE:          if (start && row_count > 0) next_state = FETCH_ROW_PTR;
        FETCH_ROW_PTR: // row_ptr[r+1] arrives one cycle after the read
                       if (row_end == ptr) next_state = WRITEBACK;   // empty row
                       else                next_state = STREAM_CSR;
        STREAM_CSR:    next_state = MAC_ACCUM;       // value/col read, then vector read
        MAC_ACCUM: begin
            mac_en = 1;
            next_state = (ptr + 1 == row_end) ? WRITEBACK : STREAM_CSR;
        end
        WRITEBACK: begin
            wr_en = 1;  mac_clr = 1;                 // y[r] <= acc; acc <= 0
            next_state = (r + 1 == row_count) ? DONE : FETCH_ROW_PTR;
        end
        DONE:          begin done = 1; if (!start) next_state = IDLE; end
    endcase
end""")

    # ---------------------------------------------------------------- 3.11
    R.h2("3.11 BRAM latency and operand alignment")
    R.p("The schedule of the controller is dictated by two facts: every BRAM read has a latency of one "
        "clock cycle (the data appear on <c>douta</c> after the next rising edge), and the vector address "
        "depends on data read from a BRAM (the column index). Consider one stored non-zero with pointer "
        "<i>p</i>, and let the cycles of its processing be numbered 1, 2, 3.")
    R.bullets([
        "<b>Cycle 1 – FETCH_PTR.</b> <c>val_addr</c> = <i>p</i> is presented to <c>bank_values</c> and "
        "<c>bank_col_idx</c>. The data are not yet available; at the rising edge that ends the cycle both "
        "banks latch <c>mem[p]</c> into their output registers.",
        "<b>Cycle 2 – FETCH_VEC.</b> <c>val_data</c> = weight and <c>col_data</c> = column index are "
        "now valid. The controller forms <c>vec_addr</c> = <c>col_data[5:0]</c> combinationally and "
        "presents it to <c>bank_vector</c>; at the end of the cycle that bank latches "
        "<i>x</i>[<c>col_data</c>] into <c>vec_data</c>. <c>val_data</c> remains stable because "
        "<c>val_addr</c> still equals <i>p</i> and the bank re-reads the same location.",
        "<b>Cycle 3 – COMPUTE.</b> <c>val_data</c> and <c>vec_data</c> are both valid and are "
        "forwarded to the MAC; <c>mac_en</c> = 1 so the product is added into the accumulator at the "
        "edge that ends the cycle, and the pointer increments at the same edge.",
    ])
    R.p("The two reads are <i>serially dependent</i>: <c>vec_addr</c> cannot be generated until "
        "<c>col_data</c> exists, and <c>col_data</c> cannot exist until one edge after <c>val_addr</c> is "
        "applied. Two registered BRAM reads in series therefore need two edges before the operand pair is "
        "complete, and the third cycle performs the arithmetic. The alignment is shown below; the symbol "
        "▲ marks the clock edge that ends each cycle.")
    R.code("Operand alignment for one non-zero (pointer p)",
"""cycle            |   1: FETCH_PTR    |   2: FETCH_VEC       |   3: COMPUTE
-----------------+-------------------+----------------------+------------------------
val_addr         |   p               |   p                  |   p
bank_values/col  |   read p  ... ▲   |   douta = mem[p]     |   douta = mem[p]
col_data         |   (old)           |   = col_idx[p]       |   = col_idx[p]
vec_addr         |   0 (default)     |   col_idx[p][5:0]    |   0 (default)
bank_vector      |   --              |   read x[col] ... ▲  |   douta = x[col]
mac_en / acc     |   0               |   0                  |   1 :  acc += w * x  ▲
current_ptr      |   p               |   p                  |   p  ->  p + 1  ▲""", numbered=False,
           caption=False)
    R.p("<b>Latency formula.</b> With NNZ stored non-zeros, <c>start</c> sampled in IDLE (1 cycle), three "
        "cycles per non-zero and one cycle in DONE_STATE in which <c>done</c> and the final result are "
        "visible, the execution latency in clock cycles is")
    R.eq("<i>T</i><sub>cycles</sub> = 1 + 3 · NNZ + 1 = 3 · NNZ + 2")
    R.p("For NNZ = 2 (the directed test) <i>T</i> = 8 cycles = 80 ns at 100 MHz; for the example of "
        "Section 5.9, NNZ = 410, <i>T</i> = 1,232 cycles. In general the throughput of the inner loop is "
        "one non-zero per three cycles, i.e. <i>f</i>/3 MAC operations per second at clock frequency "
        "<i>f</i>.")
    R.p("<b>Scheduling headroom.</b> The three-cycle schedule is the simplest correct schedule and is the "
        "one implemented and characterised. Because val_addr already advances to the next pointer at the "
        "edge that ends COMPUTE, FETCH_PTR of non-zero <i>k</i> + 1 can be overlapped with COMPUTE of "
        "non-zero <i>k</i> by pre-incrementing the pointer, which reduces the loop to two cycles per "
        "non-zero (<i>T</i> = 2 NNZ + 3, the extra cycle being the initial fetch); and a fully pipelined version, with the address generator, the "
        "vector-address stage and the MAC in three overlapped stages, accepts one non-zero per cycle "
        "(<i>T</i> ≈ NNZ + 4, one fill latency of three cycles plus the done cycle). These are the "
        "natural next steps once the system-level integration is complete.")

    # ---------------------------------------------------------------- 3.12
    R.h2("3.12 INT8 multiply-accumulate datapath")
    R.figure(os.path.join(FIG, "ises_fig4.png"), "Datapath micro-architecture of the MAC unit (from the iSES "
             "paper): 8-bit signed multiplier, 16-bit product, 32-bit accumulator register with feedback", 2.45)
    R.p("Figure 3.5 shows the datapath. Two signed 8-bit operands feed a multiplier that produces a 16-bit "
        "product; the product is sign-extended to 32 bits and added to the 32-bit accumulator register's "
        "feedback value; an FSM-controlled enable and clear determine whether the register loads the sum, "
        "holds, or clears. Listing 3.5 shows the complete module.")
    R.code("mac_unit.sv – combinational signed multiplier with enable-controlled 32-bit accumulator",
           sv("mac_unit.sv"))
    R.h3("Explanation")
    R.defs([
        ("weight_in, act_in [7:0] (signed)", "INT8 operands from the controller."),
        ("clk, rst_n", "clock and active-low asynchronous reset (the accumulator clears to zero when "
         "<c>rst_n</c> falls)."),
        ("clr_acc", "synchronous clear: when 1 at a rising edge the accumulator is set to zero. The "
         "controller asserts it throughout IDLE, so every invocation starts from zero."),
        ("en", "accumulate enable: when 1 (and <c>clr_acc</c> = 0) the product is added at the rising edge; "
         "when 0 the register holds. The controller raises it only in COMPUTE, so cycles with no valid "
         "operand pair cannot alter the result."),
        ("acc_out [31:0] (signed)", "the accumulator, driven straight to <c>final_result</c>."),
        ("product [15:0] (signed)", "internal combinational product."),
    ])
    R.p("<b>Combinational product.</b> The <c>always_comb</c> block computes "
        "<c>product = weight_in * act_in</c>. Because the operands are signed and the destination is 16 "
        "bits, the result is the exact two's-complement product (Section 2.3); there is no register between "
        "the operands and the product, so the multiplier is purely combinational and its delay lies on the "
        "path from the BRAM output registers (through the controller's operand gating) to the accumulator.")
    R.p("<b>Enable-controlled accumulation.</b> The <c>always_ff</c> block has the priority order "
        "<i>reset</i> > <i>clear</i> > <i>enable</i>: on <c>rst_n</c> = 0 or <c>clr_acc</c> = 1 the register "
        "is zeroed, on <c>en</c> = 1 it loads <c>acc_out + 32'(product)</c>, and otherwise it keeps its value. "
        "In the target fabric this is a bank of 32 FDCE flip-flops (D flip-flop with clock enable and "
        "asynchronous clear), the synchronous clear folded into the data path and the clock-enable pin driven by "
        "the OR of <c>en</c> and <c>clr_acc</c>, so that holding the accumulator costs no extra logic and "
        "suppresses switching in the register when no operand is valid. The addition uses the slice carry "
        "chain.")

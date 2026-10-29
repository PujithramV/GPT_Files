"""Cycle-accurate Python reference model of the Sparse-CIM core (sparse_cim_top.sv).

The model mirrors the RTL semantics exactly:
  * BRAM Port A is a registered (1-cycle) read with ena = 1.
  * The controller is the 5-state FSM IDLE/FETCH_PTR/FETCH_VEC/COMPUTE/DONE_STATE.
  * mac_unit accumulates 32'(weight*act) at the clock edge that ends a cycle with en = 1,
    and clears at the edge that ends a cycle with clr_acc = 1.
It is used to generate the cycle-by-cycle trace (Table 5.1) and the analytical tables.
"""
import math


def s8(v):
    v &= 0xFF
    return v - 256 if v & 0x80 else v


def simulate(values, cols, vec, nnz, start_cycles=1, hold_start_cycles=2, max_cycles=200):
    """Return a list of per-cycle dictionaries (one entry per clock cycle).

    values/cols/vec are the preloaded BRAM contents (python lists, depth 64).
    start is asserted during the first `start_cycles` idle cycle(s) and released
    `hold_start_cycles` cycles after done first rises (mirrors the directed testbench).
    """
    depth = 64
    val_mem = list(values) + [0] * (depth - len(values))
    col_mem = list(cols) + [0] * (depth - len(cols))
    vec_mem = list(vec) + [0] * (depth - len(vec))
    state, ptr, acc = "IDLE", 0, 0
    val_q = col_q = vec_q = 0  # BRAM output registers (douta)
    trace = []
    done_seen = None
    for cyc in range(max_cycles):
        start = 1
        if done_seen is not None and cyc - done_seen >= hold_start_cycles - 1:
            start = 0
        # --- combinational outputs of the controller in this cycle
        val_addr = ptr
        vec_addr = 0
        mac_en = mac_clr = 0
        w = a = 0
        done = 0
        nxt = state
        if state == "IDLE":
            mac_clr = 1
            if start and nnz > 0:
                nxt = "FETCH_PTR"
        elif state == "FETCH_PTR":
            nxt = "FETCH_VEC"
        elif state == "FETCH_VEC":
            vec_addr = col_q & 0x3F
            nxt = "COMPUTE"
        elif state == "COMPUTE":
            w, a, mac_en = s8(val_q), s8(vec_q), 1
            nxt = "DONE_STATE" if ptr == nnz - 1 else "FETCH_PTR"
        elif state == "DONE_STATE":
            done = 1
            if not start:
                nxt = "IDLE"
        trace.append(dict(cycle=cyc, state=state, ptr=ptr, start=start, val_addr=val_addr,
                          vec_addr=vec_addr, val_data=s8(val_q), col_data=col_q,
                          vec_data=s8(vec_q), mac_en=mac_en, mac_clr=mac_clr,
                          product=w * a, acc=acc, done=done))
        if done and done_seen is None:
            done_seen = cyc
        if state == "IDLE" and done_seen is not None and nxt == "IDLE" and cyc > done_seen + 4:
            break
        # --- clock edge: update registers
        new_acc = acc
        if mac_clr:
            new_acc = 0
        elif mac_en:
            new_acc = acc + w * a
        new_ptr = ptr
        if state == "COMPUTE":
            new_ptr = ptr + 1
        elif state == "IDLE":
            new_ptr = 0
        # synchronous BRAM reads (Port A, ena=1) use the addresses of the ending cycle
        val_q, col_q, vec_q = val_mem[val_addr], col_mem[val_addr], vec_mem[vec_addr]
        state, ptr, acc = nxt, new_ptr, new_acc
    return trace


def cycles_for(nnz):
    """T_cycles = 1 (IDLE) + 3*NNZ (FETCH_PTR, FETCH_VEC, COMPUTE) + 1 (DONE_STATE)."""
    return 1 + 3 * nnz + 1


def clog2(x):
    return max(1, math.ceil(math.log2(x))) if x > 1 else 1


def storage_bits(M, N, nnz, bv=8, bc=None, br=None, bp=None):
    bc = bc or clog2(N)
    br = br or clog2(M)
    bp = bp or clog2(nnz + 1)
    return dict(dense=M * N * bv,
                csr=nnz * bv + nnz * bc + (M + 1) * bp,
                coo=nnz * (bv + br + bc),
                csc=nnz * bv + nnz * br + (N + 1) * bp)


if __name__ == "__main__":
    tr = simulate([5, -4], [0, 2], [3, 0, 2], 2)
    for t in tr:
        print(t)

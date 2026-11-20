#!/usr/bin/env python3
"""
Parse tsvc.dump and classify functions by whether they contain
RVV (RISC-V Vector) instructions.

Usage: python3 check_vectorization.py tsvc.dump
"""

import sys
import re
from collections import defaultdict, Counter

# All RVV instruction prefixes / patterns
RVV_INSTRUCTIONS = {
    'vsetvli', 'vsetivli', 'vsetvl',
    'vle8', 'vle16', 'vle32', 'vle64',
    'vse8', 'vse16', 'vse32', 'vse64',
    'vlse8', 'vlse16', 'vlse32', 'vlse64',
    'vsse8', 'vsse16', 'vsse32', 'vsse64',
    'vluxei8', 'vluxei16', 'vluxei32', 'vluxei64',
    'vloxei8', 'vloxei16', 'vloxei32', 'vloxei64',
    'vsuxei8', 'vsuxei16', 'vsuxei32', 'vsuxei64',
    'vsoxei8', 'vsoxei16', 'vsoxei32', 'vsoxei64',
    'vl1r', 'vl2r', 'vl4r', 'vl8r',
    'vs1r', 'vs2r', 'vs4r', 'vs8r',
    'vl1re8', 'vl1re16', 'vl1re32', 'vl1re64',
    'vl2re8', 'vl2re16', 'vl2re32', 'vl2re64',
    'vl4re8', 'vl4re16', 'vl4re32', 'vl4re64',
    'vl8re8', 'vl8re16', 'vl8re32', 'vl8re64',
    'vadd', 'vsub', 'vrsub',
    'vmul', 'vmulh', 'vmulhu', 'vmulhsu',
    'vdiv', 'vdivu', 'vrem', 'vremu',
    'vand', 'vor', 'vxor',
    'vsll', 'vsrl', 'vsra',
    'vnsrl', 'vnsra',
    'vmin', 'vminu', 'vmax', 'vmaxu',
    'vfadd', 'vfsub', 'vfmul', 'vfdiv', 'vfrdiv',
    'vfmacc', 'vfnmacc', 'vfmsac', 'vfnmsac',
    'vfmadd', 'vfnmadd', 'vfmsub', 'vfnmsub',
    'vfwmacc', 'vfwnmacc', 'vfwmsac', 'vfwnmsac',
    'vfwadd', 'vfwsub', 'vfwmul',
    'vfsqrt', 'vfmin', 'vfmax',
    'vfcvt', 'vfwcvt', 'vfncvt',
    'vfclass', 'vfsgnj', 'vfsgnjn', 'vfsgnjx',
    'vfmerge', 'vfmv',
    'vmfeq', 'vmfne', 'vmflt', 'vmfle', 'vmfgt', 'vmfge',
    'vredsum', 'vredmax', 'vredmaxu', 'vredmin', 'vredminu',
    'vredand', 'vredor', 'vredxor',
    'vwredsumu', 'vwredsum',
    'vfredusum', 'vfredosum', 'vfredmin', 'vfredmax',
    'vfwredusum', 'vfwredosum',
    'vmand', 'vmnand', 'vmandnot', 'vmxor', 'vmor', 'vmnor', 'vmornot', 'vmxnor',
    'vmsbf', 'vmsof', 'vmsif', 'viota', 'vid',
    'vcpop', 'vfirst',
    'vmseq', 'vmsne', 'vmsltu', 'vmslt', 'vmsleu', 'vmsle', 'vmsgtu', 'vmsgt',
    'vmerge', 'vmv',
    'vslideup', 'vslidedown', 'vslide1up', 'vslide1down',
    'vfslide1up', 'vfslide1down',
    'vrgather', 'vrgatherei16', 'vcompress',
    'vadc', 'vmadc', 'vsbc', 'vmsbc',
    'vsaddu', 'vsadd', 'vssubu', 'vssub',
    'vaadd', 'vaaddu', 'vasub', 'vasubu',
    'vsmul', 'vssra', 'vssrl',
    'vnclip', 'vnclipu',
    'vwaddu', 'vwsubu', 'vwadd', 'vwsub',
    'vwmul', 'vwmulu', 'vwmulsu',
    'vwmacc', 'vwmaccu', 'vwmaccsu', 'vwmaccus',
    'vzext', 'vsext',
}

# AraXL supported instructions (from FUNCTIONALITIES.MD)
# These are the base mnemonics — variants like vle32.v, vfadd.vv etc. match by prefix
ARAXL_SUPPORTED = {
    # Config
    'vsetvli', 'vsetivli', 'vsetvl',
    # Unit-strided loads/stores only (NO strided, NO indexed)
    'vle8', 'vle16', 'vle32', 'vle64',
    'vse8', 'vse16', 'vse32', 'vse64',
    'vl1r', 'vs1r',
    'vl1re8', 'vl1re16', 'vl1re32', 'vl1re64',
    'vl2re8', 'vl2re16', 'vl2re32', 'vl2re64',
    'vl4re8', 'vl4re16', 'vl4re32', 'vl4re64',
    'vl8re8', 'vl8re16', 'vl8re32', 'vl8re64',
    'vs2r', 'vs4r', 'vs8r',
    # Integer arithmetic
    'vadd', 'vsub', 'vrsub',
    'vwaddu', 'vwsubu', 'vwadd', 'vwsub',
    'vzext', 'vsext',
    'vadc', 'vmadc', 'vsbc', 'vmsbc',
    'vand', 'vor', 'vxor',
    'vsll', 'vsrl', 'vsra',
    'vnsrl', 'vnsra',
    'vmseq', 'vmsne', 'vmsltu', 'vmslt', 'vmsleu', 'vmsle', 'vmsgtu', 'vmsgt',
    'vminu', 'vmin', 'vmaxu', 'vmax',
    'vmul', 'vmulh', 'vmulhu', 'vmulhsu',
    'vdivu', 'vdiv', 'vremu', 'vrem',
    'vwmul', 'vwmulu', 'vwmulsu',
    'vmacc', 'vnmsac', 'vmadd', 'vnmsub',
    'vwmaccu', 'vwmacc', 'vwmaccsu', 'vwmaccus',
    'vmerge', 'vmv',
    # Floating-point
    'vfadd', 'vfsub', 'vfrsub',
    'vfwadd', 'vfwsub',
    'vfmul', 'vfdiv', 'vfrdiv',
    'vfwmul',
    'vfmacc', 'vfnmacc', 'vfmsac', 'vfnmsac',
    'vfmadd', 'vfnmadd', 'vfmsub', 'vfnmsub',
    'vfwmacc', 'vfwnmacc', 'vfwmsac', 'vfwnmsac',
    'vfsqrt', 'vfmin', 'vfmax',
    'vfsgnj', 'vfsgnjn', 'vfsgnjx',
    'vfclass',
    'vfmerge', 'vfmv',
    'vmfeq', 'vmfne', 'vmflt', 'vmfle', 'vmfgt', 'vmfge',
    'vfcvt', 'vfwcvt', 'vfncvt',
    'vfrec7', 'vfrsqrt7',
    # Reductions
    'vredsum', 'vredmaxu', 'vredmax', 'vredminu', 'vredmin',
    'vredand', 'vredor', 'vredxor',
    'vwredsumu', 'vwredsum',
    'vfredusum', 'vfredosum', 'vfredmin', 'vfredmax',
    'vfwredusum', 'vfwredosum',
    # Mask instructions
    'vmand', 'vmnand', 'vmandnot', 'vmxor', 'vmor', 'vmnor', 'vmornot', 'vmxnor',
    'vmsbf', 'vmsof', 'vmsif', 'viota', 'vid',
    'vcpop', 'vfirst',
    # Permutation
    'vslideup', 'vslidedown', 'vslide1up', 'vslide1down',
    'vfslide1up', 'vfslide1down',
    # Fixed-point
    'vsaddu', 'vsadd', 'vssubu', 'vssub',
    'vaadd', 'vaaddu', 'vasub', 'vasubu',
    'vsmul', 'vssra', 'vssrl',
    'vnclip', 'vnclipu',
}

def is_araxl_supported(mnemonic):
    """Check if a mnemonic is supported by AraXL hardware."""
    mnemonic = mnemonic.lower().rstrip('.')
    if mnemonic in ARAXL_SUPPORTED:
        return True
    for sup in ARAXL_SUPPORTED:
        if mnemonic.startswith(sup):
            return True
    return False

# TSVC categories: category number -> set of function names
CATEGORIES = {
    1: {
        's000', 's111', 's1111', 's112', 's1112', 's113', 's1113',
        's114', 's115', 's1115', 's116', 's118', 's119', 's1119',
        's121', 's122', 's123', 's124', 's125', 's126', 's127', 's128',
        's131', 's132', 's141', 's151', 's152',
        's161', 's1161', 's162',
        's171', 's172', 's173', 's174', 's175', 's176',
    },
    2: {
        's211', 's212', 's1213',
        's221', 's1221', 's222',
        's231', 's232', 's1232', 's233', 's2233', 's235',
        's241', 's242', 's243', 's244', 's1244', 's2244',
        's251', 's1251', 's2251', 's3251', 's252', 's253', 's254', 's255',
        's256', 's257', 's258',
        's261',
        's271', 's272', 's273', 's274', 's275', 's2275', 's276',
        's277', 's278', 's279', 's1279', 's2710', 's2711', 's2712',
        's281', 's1281', 's291', 's292', 's293',
        's2101', 's2102', 's2111',
    },
    3: {
        's311', 's31111', 's312', 's313', 's314', 's315', 's316', 's317',
        's318', 's319', 's3110', 's13110', 's3111', 's3112', 's3113',
        's321', 's322', 's323',
        's331', 's332',
        's341', 's342', 's343',
        's351', 's1351', 's352', 's353',
    },
    4: {
        's421', 's1421', 's422', 's423', 's424',
        's431', 's441', 's442', 's443',
        's451', 's452', 's453',
        's471', 's481', 's482',
        's491', 's4112', 's4113', 's4114', 's4115', 's4116', 's4117', 's4121',
    },
    5: {
        'va', 'vag', 'vas', 'vif', 'vpv', 'vtv',
        'vpvtv', 'vpvts', 'vpvpv', 'vtvtv',
        'vsumr', 'vdotr', 'vbor',
    },
}

TSVC_FUNCTIONS = set().union(*CATEGORIES.values())

def get_category(func):
    for cat, funcs in CATEGORIES.items():
        if func in funcs:
            return cat
    return 0

def is_rvv_instruction(mnemonic):
    mnemonic = mnemonic.lower().rstrip('.')
    if mnemonic in RVV_INSTRUCTIONS:
        return True
    for rvv in RVV_INSTRUCTIONS:
        if mnemonic.startswith(rvv):
            return True
    return False

def parse_dump(filename):
    functions = {}
    current_func = None
    current_instrs = []
    func_pattern = re.compile(r'^[0-9a-f]+ <([^>]+)>:')
    instr_pattern = re.compile(r'^[0-9a-f]+:\s+[0-9a-f]+\s+\t(\S+)')
    with open(filename, 'r') as f:
        for line in f:
            m = func_pattern.match(line)
            if m:
                if current_func:
                    functions[current_func] = current_instrs
                current_func = m.group(1)
                current_instrs = []
                continue
            if current_func:
                m = instr_pattern.match(line)
                if m:
                    current_instrs.append(m.group(1))
    if current_func:
        functions[current_func] = current_instrs
    return functions

def print_instr_stats(instr_list, label):
    """Print instruction frequency stats for a list of instructions."""
    total = len(instr_list)
    if total == 0:
        print(f"  (no RVV instructions)")
        return
    counts = Counter(instr_list)
    print(f"  {'Instruction':<22} {'Count':>6}  {'%':>6}")
    print(f"  {'-'*38}")
    for instr, count in counts.most_common():
        pct = 100.0 * count / total
        print(f"  {instr:<22} {count:>6}  {pct:>5.1f}%")
    print(f"  {'TOTAL':<22} {total:>6}  100.0%")

def analyse(filename):
    print(f"Parsing {filename}...")
    functions = parse_dump(filename)
    print(f"Found {len(functions)} total functions in dump\n")

    vectorized = []
    not_vectorized = []
    not_found = []
    func_rvv_instrs = {}   # func -> list of all rvv instr occurrences
    func_rvv_unique = {}   # func -> frozenset of unique rvv instrs

    for func in sorted(TSVC_FUNCTIONS):
        matched_key = None
        for key in functions:
            if key == func or key.startswith(func + '_'):
                matched_key = key
                break
        if matched_key is None:
            not_found.append(func)
            continue
        instrs = functions[matched_key]
        rvv = [i for i in instrs if is_rvv_instruction(i)]
        func_rvv_instrs[func] = rvv
        func_rvv_unique[func] = frozenset(set(rvv))
        if rvv:
            vectorized.append(func)
        else:
            not_vectorized.append(func)

    # ----------------------------------------------------------------
    # 1. VECTORIZED — grouped by identical instruction sets
    # ----------------------------------------------------------------
    print("=" * 60)
    print(f"VECTORIZED ({len(vectorized)} loops) — grouped by instruction set")
    print("=" * 60)

    groups = defaultdict(list)
    for f in vectorized:
        groups[func_rvv_unique[f]].append(f)

    for instr_set, funcs in sorted(groups.items(), key=lambda x: sorted(x[1])[0]):
        funcs_sorted = sorted(funcs)
        instr_list = sorted(instr_set)
        print(f"  {', '.join(funcs_sorted)}")
        print(f"    [{', '.join(instr_list)}]")

    # ----------------------------------------------------------------
    # 2. LOOPS WITH UNSUPPORTED ARAXL INSTRUCTIONS
    # ----------------------------------------------------------------
    print()
    print("=" * 60)
    print("VECTORIZED BUT CONTAINS UNSUPPORTED AraXL INSTRUCTIONS")
    print("=" * 60)

    unsupported_loops = []
    for f in vectorized:
        unsup = sorted(set(i for i in func_rvv_instrs[f] if not is_araxl_supported(i)))
        if unsup:
            unsupported_loops.append((f, unsup))

    if unsupported_loops:
        for f, unsup in sorted(unsupported_loops):
            print(f"  {f:<12} unsupported: [{', '.join(unsup)}]")
    else:
        print("  (none — all vectorized loops use only supported instructions)")

    fully_supported = [f for f in vectorized if f not in [x[0] for x in unsupported_loops]]
    print()
    print(f"  Fully supported on AraXL: {len(fully_supported)} / {len(vectorized)} vectorized loops")
    print(f"  Has unsupported instrs:   {len(unsupported_loops)} / {len(vectorized)} vectorized loops")

    # ----------------------------------------------------------------
    # 3. NOT VECTORIZED
    # ----------------------------------------------------------------
    # 3. NOT VECTORIZED
    # ----------------------------------------------------------------
    print()
    print("=" * 60)
    print(f"NOT VECTORIZED ({len(not_vectorized)} loops) — scalar only")
    print("=" * 60)
    for f in not_vectorized:
        print(f"  {f}")

    # ----------------------------------------------------------------
    # 4. NOT FOUND
    # ----------------------------------------------------------------
    if not_found:
        print()
        print("=" * 60)
        print(f"NOT FOUND IN DUMP ({len(not_found)} loops)")
        print("=" * 60)
        for f in not_found:
            print(f"  {f}")

    # ----------------------------------------------------------------
    # 5. INSTRUCTION STATS — overall
    # ----------------------------------------------------------------
    all_rvv = []
    for f in vectorized:
        all_rvv.extend(func_rvv_instrs[f])

    print()
    print("=" * 60)
    print(f"RVV INSTRUCTION FREQUENCY — all vectorized loops (total {len(all_rvv)} occurrences)")
    print("=" * 60)
    print_instr_stats(all_rvv, "all")

    # ----------------------------------------------------------------
    # 6. INSTRUCTION STATS — per category
    # ----------------------------------------------------------------
    for cat in sorted(CATEGORIES.keys()):
        cat_funcs = [f for f in vectorized if get_category(f) == cat]
        cat_rvv = []
        for f in cat_funcs:
            cat_rvv.extend(func_rvv_instrs[f])

        vec_count = len(cat_funcs)
        total_count = len(CATEGORIES[cat])
        print()
        print("=" * 60)
        print(f"RVV INSTRUCTION FREQUENCY — Category {cat}  ({vec_count} vectorized / {total_count} total loops)")
        print("=" * 60)
        print_instr_stats(cat_rvv, f"cat{cat}")

    # ----------------------------------------------------------------
    # 7. SUMMARY
    # ----------------------------------------------------------------
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(vectorized) + len(not_vectorized)
    print(f"  Vectorized:     {len(vectorized):3d} / {total}  ({100*len(vectorized)/total:.1f}%)")
    print(f"  Not vectorized: {len(not_vectorized):3d} / {total}  ({100*len(not_vectorized)/total:.1f}%)")
    print(f"  Not in dump:    {len(not_found):3d}")
    print()
    for cat in sorted(CATEGORIES.keys()):
        cat_vec   = [f for f in vectorized     if get_category(f) == cat]
        cat_novec = [f for f in not_vectorized if get_category(f) == cat]
        tot = len(cat_vec) + len(cat_novec)
        pct = 100*len(cat_vec)/tot if tot else 0
        print(f"  Category {cat}: {len(cat_vec):3d} / {tot} vectorized  ({pct:.1f}%)")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} tsvc.dump")
        sys.exit(1)
    analyse(sys.argv[1])
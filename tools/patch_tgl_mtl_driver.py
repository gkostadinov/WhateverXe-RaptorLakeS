#!/usr/bin/env python3
"""Patch the TGL Metal driver (AppleIntelTGLGraphicsMTLDriver) to skip SIMD8.

CHAL_INTEL::ChalContext::ChalExecuteKernel picks, per dispatch, the smallest
SIMD binary that fits the GPU's thread budget: SIMD8 for dispatches of up to
8x the hardware thread count (fewer than 16 threadgroups of 128 threads on a
UHD 770), then SIMD16, then SIMD32. The 2020 Tiger Lake compiler miscompiles
some SIMD8 kernels; MetalPerformanceShaders' ndArrayConvolution2D loses every
odd filter tap in its SIMD8 build, so small convolutions (and Geekbench's Face
Detection) return wrong results while the SIMD16/SIMD32 builds of the same
kernel are correct.

The SIMD8 candidate test becomes unconditional, so the driver uses SIMD16 when
it fits and the first (default) binary otherwise. Kernels built only for SIMD8
still run: their single binary is the default.

Usage: patch_tgl_mtl_driver.py <AppleIntelTGLGraphicsMTLDriver> [<output>]
       (re-sign ad hoc after: codesign -f -s - <file>)
"""
import hashlib, sys

ORIGINAL_SHA256 = "7816bb18a28efea9"  # prefix of the shipped driver
PATCHES = [
    (0x2C8C2, "781c", "eb1c"),  # js 0x2c8e0 -> jmp 0x2c8e0 (never select SIMD8)
]
# testl %r15d,%r15d; js; movl 0xd4c(%rdi),%eax; shll $3,%eax
CONTEXT = (0x2C8BF, "4585ff781c8b874c0d0000c1e003")


def main() -> int:
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    digest = hashlib.sha256(data).hexdigest()
    off, ctx = CONTEXT
    ctx = bytes.fromhex(ctx)
    cur = bytes(data[off:off + len(ctx)])
    patched_ctx = bytearray(ctx)
    for poff, old, new in PATCHES:
        patched_ctx[poff - off:poff - off + len(bytes.fromhex(new))] = bytes.fromhex(new)
    if cur not in (ctx, bytes(patched_ctx)):
        print("unexpected driver layout", digest)
        return 1
    for poff, old, new in PATCHES:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        now = bytes(data[poff:poff + len(old)])
        if now == new:
            continue
        if now != old:
            print(f"unexpected bytes at {poff:#x}: {now.hex()}")
            return 1
        data[poff:poff + len(new)] = new
    open(dst, "wb").write(data)
    print("patched", digest[:16], "->", hashlib.sha256(data).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())

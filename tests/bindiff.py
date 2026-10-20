#!/usr/bin/env python3
"""bindiff.py a.bin b.bin — mostra bytes diferentes (offset, hex, decimal e int16 LE)"""
import sys
a, b = open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()
for i in range(min(len(a), len(b))):
    if a[i] != b[i]:
        i16 = lambda d: int.from_bytes(d[i & ~1:(i & ~1) + 2], "little", signed=True)
        print(f"{i:4d} (0x{i:03x}): {a[i]:02x} -> {b[i]:02x}   ({a[i]:3d} -> {b[i]:3d})   int16@{i & ~1}: {i16(a)} -> {i16(b)}")

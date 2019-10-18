from project_01 import *

def test_nand():
    assert eval(Nand, a=0, b=0).out == 1
    assert eval(Nand, a=0, b=1).out == 1
    assert eval(Nand, a=1, b=0).out == 1
    assert eval(Nand, a=1, b=1).out == 0

def test_not():
    assert eval(Not, in_=0).out == 1
    assert eval(Not, in_=1).out == 0

def test_or():
    assert eval(Or, a=0, b=0).out == 0
    assert eval(Or, a=0, b=1).out == 1
    assert eval(Or, a=1, b=0).out == 1
    assert eval(Or, a=1, b=1).out == 1

def test_and():
    assert eval(And, a=0, b=0).out == 0
    assert eval(And, a=0, b=1).out == 0
    assert eval(And, a=1, b=0).out == 0
    assert eval(And, a=1, b=1).out == 1

def test_xor():
    assert eval(Xor, a=0, b=0).out == 0
    assert eval(Xor, a=0, b=1).out == 1
    assert eval(Xor, a=1, b=0).out == 1
    assert eval(Xor, a=1, b=1).out == 0

def test_mux():
    assert eval(Mux, a=0, b=0, sel=0).out == 0
    assert eval(Mux, a=0, b=0, sel=1).out == 0
    assert eval(Mux, a=0, b=1, sel=0).out == 0
    assert eval(Mux, a=0, b=1, sel=1).out == 1
    assert eval(Mux, a=1, b=0, sel=0).out == 1
    assert eval(Mux, a=1, b=0, sel=1).out == 0
    assert eval(Mux, a=1, b=1, sel=0).out == 1
    assert eval(Mux, a=1, b=1, sel=1).out == 1

def test_dmux():
    dmux00 = eval(DMux, in_=0, sel=0)
    assert dmux00.a == 0 and dmux00.b == 0

    dmux01 = eval(DMux, in_=0, sel=1)
    assert dmux01.a == 0 and dmux01.b == 0

    dmux10 = eval(DMux, in_=1, sel=0)
    assert dmux10.a == 1 and dmux10.b == 0

    dmux11 = eval(DMux, in_=1, sel=1)
    assert dmux11.a == 0 and dmux11.b == 1

def test_not16():
    assert eval(Not16, in_=0b0000_0000_0000_0000).out == 0b1111_1111_1111_1111
    assert eval(Not16, in_=0b1111_1111_1111_1111).out == 0b0000_0000_0000_0000
    assert eval(Not16, in_=0b1010_1010_1010_1010).out == 0b0101_0101_0101_0101
    assert eval(Not16, in_=0b0011_1100_1100_0011).out == 0b1100_0011_0011_1100
    assert eval(Not16, in_=0b0001_0010_0011_0100).out == 0b1110_1101_1100_1011

# TODO: these require multi-bit inputs/outputs:
# DMux4Way
# DMux8Way
# And16
# Mux16
# Mux4Way16
# Mux8Way16

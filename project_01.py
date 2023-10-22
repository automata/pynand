# Boolean Logic
#
# See https://www.nand2tetris.org/project01

from nand import Nand, chip

# SOLVERS: remove this import to get started
from nand.solutions import solved_01

@chip
def Not(inputs, outputs):
    in_ = inputs.in_
    # n1 = Nand(a=in_, b=1)
    # Or:
    n1 = Nand(a=in_, b=in_)
    outputs.out = n1.out


@chip
def Or(inputs, outputs):
    a = inputs.a
    b = inputs.b
    not_a = Not(in_=a)
    not_b = Not(in_=b)
    nand_a_b = Nand(a=not_a.out, b=not_b.out)
    outputs.out = nand_a_b.out


@chip
def And(inputs, outputs):
    a = inputs.a
    b = inputs.b
    n1 = Nand(a=a, b=b)
    n2 = Nand(a=n1.out, b=1)
    outputs.out = n2.out


@chip
def Xor(inputs, outputs):
    a = inputs.a
    b = inputs.b
    a_and_not_b = And(a=a, b=Not(in_=b).out)
    b_and_not_a = And(a=Not(in_=a).out, b=b)
    or_a_b = Or(a=a_and_not_b.out, b=b_and_not_a.out)
    outputs.out = or_a_b.out


@chip
def Mux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # The idea is to use sel as a switch: if sel is 1, it will allow a to pass,
    # and if sel is 0, it will let b to pass. Note how the (not sel) is used
    # to reverse the value of sel, blocking the other input.
    #
    # a -------,====[)o-.
    # sel -.--'          ;=[)o-- out
    #      `-=[)o-,=[)o-'
    # b ----------'

    sel_a = Nand(a=a, b=Nand(a=sel, b=sel).out)
    sel_b = Nand(a=b, b=sel)
    outputs.out = Nand(a=sel_a.out, b=sel_b.out).out


@chip
def DMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.DMux(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b


@chip
def DMux4Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: use sel[0] and sel[1] to extract each bit
    n1 = solved_01.DMux4Way(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b
    outputs.c = n1.c
    outputs.d = n1.d


@chip
def DMux8Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.DMux8Way(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b
    outputs.c = n1.c
    outputs.d = n1.d
    outputs.e = n1.e
    outputs.f = n1.f
    outputs.g = n1.g
    outputs.h = n1.h


@chip
def Not16(inputs, outputs):
    in_ = inputs.in_
    for i in range(16):
        outputs.out[i] = Not(in_=in_[i]).out


@chip
def And16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    for i in range(16):
        outputs.out[i] = And(a=a[i], b=b[i]).out


@chip
def Mux16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux16(a=a, b=b, sel=sel)

    outputs.out = n1.out


@chip
def Mux4Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux4Way16(a=a, b=b, c=c, d=d, sel=sel)

    outputs.out = n1.out


@chip
def Mux8Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    e = inputs.e
    f = inputs.f
    g = inputs.g
    h = inputs.h
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux8Way16(a=a, b=b, c=c, d=d, e=e, f=f, g=g, h=h, sel=sel)

    outputs.out = n1.out

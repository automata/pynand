# Boolean Logic
#
# See https://www.nand2tetris.org/project01

from nand import Nand, chip

# from nand.solutions import solved_01

@chip
def Not(inputs, outputs):
    in_ = inputs.in_
    
    # No matter what we give to AND, if we fix one input as 1, it
    # will give as output the other input: 0 1 -> 0 and 1 1 -> 1. If
    # we NOT that, we have 0 1 -> 1 and 0 1 -> 0, or 0 -> 1 and 1 -> 0!
    #
    # n1 = Nand(a=in_, b=1)
    #
    # Or, if we git 0 0 to AND, it gives us 0. And if we give 1 1 to AND,
    # it gives us 1. If we NOT that, we get 0 0 -> 1 and 1 1 -> 0. So,
    # we actually have 0 -> 1 and 1 -> 0, a NOT!
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

    # This one is easy, we just have to Not the Nand!

    n1 = Nand(a=a, b=b)
    n2 = Nand(a=n1.out, b=1)
    outputs.out = n2.out


@chip
def Xor(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # This one is exactly the interpretation of what we say as the
    # definition of exclusivity: if a, then not b OR if b, then not a :-)

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
    # a -------;====[)o--;=[)o-- out
    # sel -.---'         |
    #      `-=[)o-;=[)o--'
    # b ----------'

    sel_a = Nand(a=a, b=Nand(a=sel, b=sel).out)
    sel_b = Nand(a=b, b=sel)
    outputs.out = Nand(a=sel_a.out, b=sel_b.out).out


@chip
def DMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # We revert sel in the first AND so when SEL=0, it will actually allow
    # IN to pass to A (because SEL is going to be flipped to 1).
    # For the second AND, there's no need to flip SEL, given that we want
    # to IN to pass to B when SEL=1. So the idea here is to use AND as a switch.
    #
    #   in  -+------;=[)--- a
    #   sel -|-+-[>-'
    #        | `----;=[)--- b
    #        `------'
    #
    # in sel  a b
    # 0  0    0 0
    # 0  1    0 0
    # 1  0    1 0
    # 1  1    0 1

    outputs.a = And(a=in_, b=Not(in_=sel).out).out
    outputs.b = And(a=in_, b=sel).out


@chip
def DMux4Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # This one is actually pretty easy! The trick is to understand the boolean equation
    # that represents this gate:
    #
    # Important: note that the logic table is inverted! b (sel[1]), then a (sel[0]).
    # Not sure why, maybe some requirement later... but I'm representing
    #
    #      F = ~b~aA + ~baB + b~aC + baD
    #
    # The ba AND gate prefixing each output will actually let the output pass or not.
    # It corresponds exactly to the boolean expression of the AND: b=0 a=1 -> B will pass, etc.
    #
    # Solving the equation for b=0 a=1:
    #
    #      F = ~0~1A + ~01B + 0~1C + 01D 
    #      F = 10A + 11B + 00C + 01D
    #      F = 0 + B + 0 + 0
    #      F = B
    #
    # b a  A B C D
    # 0 0  i 0 0 0
    # 0 1  0 i 0 0  
    # 1 0  0 0 i 0
    # 1 1  0 0 0 i

    outputs.a = And(a=And(a=Not(in_=sel[1]).out,
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.b = And(a=And(a=Not(in_=sel[1]).out,
                          b=sel[0]).out,
                    b=in_).out
    outputs.c = And(a=And(a=sel[1],
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.d = And(a=And(a=sel[1],
                          b=sel[0]).out,
                    b=in_).out


@chip
def DMux8Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # The same as the DMux4Way above, but instead of 2 control bits/inputs, we
    # have 3 (because 2^3 = 8). Note that it's again reversed cba instead of abc!
    #
    #      FF = ~c~b~aA + ~c~baB + ~cb~aC + ~cbaD + c~b~aE + c~baF + cb~aG + cbaH
    #
    # c b a ABCDEFGH
    # 0 0 0 i0000000
    # 0 0 1 0i000000
    # 0 1 0 00i00000
    # 0 1 1 000i0000
    # 1 0 0 0000i000
    # 1 0 1 00000i00
    # 1 1 0 000000i0
    # 1 1 1 0000000i

    outputs.a = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                b=Not(in_=sel[1]).out).out,
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.b = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                b=Not(in_=sel[1]).out).out,
                          b=sel[0]).out,
                    b=in_).out
    outputs.c = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                b=sel[1]).out,
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.d = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                b=sel[1]).out,
                          b=sel[0]).out,
                    b=in_).out
    outputs.e = And(a=And(a=And(a=sel[2],
                                b=Not(in_=sel[1]).out).out,
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.f = And(a=And(a=And(a=sel[2],
                                b=Not(in_=sel[1]).out).out,
                          b=sel[0]).out,
                    b=in_).out
    outputs.g = And(a=And(a=And(a=sel[2],
                                b=sel[1]).out,
                          b=Not(in_=sel[0]).out).out,
                    b=in_).out
    outputs.h = And(a=And(a=And(a=sel[2],
                                b=sel[1]).out,
                          b=sel[0]).out,
                    b=in_).out


@chip
def Not16(inputs, outputs):
    in_ = inputs.in_

    # Here we just repeat the unary Not gate to all inputs/outputs

    for i in range(16):
        outputs.out[i] = Not(in_=in_[i]).out


@chip
def And16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # Here we just repeat the binary And gate to all inputs/outputs

    for i in range(16):
        outputs.out[i] = And(a=a[i], b=b[i]).out


@chip
def Mux16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # Same thing, we just repeat the binary Mux to all inputs/outputs.
    # The sel is one bit wide while the inputs and outputs are 16 bit wide.
    
    for i in range(16):
        sel_a = Nand(a=a[i], b=Nand(a=sel, b=sel).out).out
        sel_b = Nand(a=b[i], b=sel).out
        outputs.out[i] = Nand(a=sel_a, b=sel_b).out


@chip
def Mux4Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    sel = inputs.sel

    # We can apply again the same idea we used for DMux before. We can
    # select based on those AND operations, the difference is that we're going
    # pass the respective input (A, B, C, ...) instead of only the same input IN
    # that we used on DMux (because we have here multiple inputs instead of only one).
    #
    # Another difference is that we actually OR all the ANDs, so we literally have
    # the following equation translated to the operation. The parenthesis group
    # the respective binary OR operations we used:
    #
    # F = (~b~aA + (~baB + (b~aC + baD)))
    #
    # Note that we're also using 16 bit wise inputs and outputs.

    for i in range(16):
        sel_a = And(a=And(a=Not(in_=sel[1]).out,
                          b=Not(in_=sel[0]).out).out,
                    b=a[i]).out
        sel_b = And(a=And(a=Not(in_=sel[1]).out,
                          b=sel[0]).out,
                    b=b[i]).out
        sel_c = And(a=And(a=sel[1],
                          b=Not(in_=sel[0]).out).out,
                    b=c[i]).out
        sel_d = And(a=And(a=sel[1],
                          b=sel[0]).out,
                    b=d[i]).out

        outputs.out[i] = Or(a=sel_a,
                            b=Or(a=sel_b,
                                 b=Or(a=sel_c,
                                      b=sel_d).out).out).out


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

    # The same as above, but using 8 inputs! We're implementing the following equation:
    
    # FF = (~c~b~aA + (~c~baB + (~cb~aC + (~cbaD + (c~b~aE + (c~baF + (cb~aG + cbaH)))))))

    for i in range(16):
        sel_a = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                b=Not(in_=sel[1]).out).out,
                          b=Not(in_=sel[0]).out).out,
                    b=a[i]).out
        sel_b = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                    b=Not(in_=sel[1]).out).out,
                            b=sel[0]).out,
                        b=b[i]).out
        sel_c = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                    b=sel[1]).out,
                            b=Not(in_=sel[0]).out).out,
                        b=c[i]).out
        sel_d = And(a=And(a=And(a=Not(in_=sel[2]).out,
                                    b=sel[1]).out,
                            b=sel[0]).out,
                        b=d[i]).out
        sel_e = And(a=And(a=And(a=sel[2],
                                    b=Not(in_=sel[1]).out).out,
                            b=Not(in_=sel[0]).out).out,
                        b=e[i]).out
        sel_f = And(a=And(a=And(a=sel[2],
                                    b=Not(in_=sel[1]).out).out,
                            b=sel[0]).out,
                        b=f[i]).out
        sel_g = And(a=And(a=And(a=sel[2],
                                    b=sel[1]).out,
                            b=Not(in_=sel[0]).out).out,
                        b=g[i]).out
        sel_h = And(a=And(a=And(a=sel[2],
                                    b=sel[1]).out,
                            b=sel[0]).out,
                        b=h[i]).out

        outputs.out[i] = Or(a=sel_a,
                            b=Or(a=sel_b,
                                 b=Or(a=sel_c,
                                      b=Or(a=sel_d,
                                           b=Or(a=sel_e,
                                                b=Or(a=sel_f,
                                                     b=Or(a=sel_g,
                                                          b=sel_h).out).out).out).out).out).out).out


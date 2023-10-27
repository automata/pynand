# Boolean Arithmetic
#
# See https://www.nand2tetris.org/project02

from nand import Nand, chip
from project_01 import And, And16, Or, Mux16, Not, Not16, Xor

# SOLVERS: remove this import to get started
from nand.solutions import solved_02


@chip
def HalfAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # If we check the sum and carry outputs, we'll see that
    # they correspond to the Xor and And truth tables!

    # a b sum carry
    # 0 0 0   0
    # 0 1 1   0
    # 1 0 1   0
    # 1 1 0   1

    # a b And Xor
    # 0 0 0   0
    # 0 1 0   1
    # 1 0 0   1
    # 1 1 1   0

    # So, we can implement a HalfAdder chip with And and Xor!

    outputs.sum = Xor(a=a, b=b).out
    outputs.carry = And(a=a, b=b).out


@chip
def FullAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c

    # a b c   sum car
    # 0 0 0   0   0
    # 0 0 1   1   0
    # 0 1 0   1   0
    # 0 1 1   0   1
    # 1 0 0   1   0
    # 1 0 1   0   1
    # 1 1 0   0   1
    # 1 1 1   1   1

    # A full adder can be built by a 2 half adders in cascade for the sum output
    # and a Nand in the negate of carry of the 2 half adders output

    ab = HalfAdder(a=a, b=b)
    abc = HalfAdder(a=ab.sum, b=c)
    outputs.sum = abc.sum
    outputs.carry = Nand(a=Not(in_=ab.carry).out,
                         b=Not(in_=abc.carry).out).out


@chip
def Inc16(inputs, outputs):
    """Add one to a single 16-bit input, ignoring overflow."""

    # Given that we are incrementing, the LSB will always flip!
    # 00++ -> 01++ -> 10++ -> 11++ -> 00... note the LSB how it
    # always flips! So, for the LSB we don't need a HalfAdder,
    # we can only flip it!
    outputs.out[0] = Not(in_=inputs.in_[0]).out
    # Here we simulate the wiring from the next carry with the
    # result of previous sum (don't think of it as a for, it's
    # just a shortcut so we don't have to repeat those blocks 16 times)
    carry = inputs.in_[0]
    for i in range(1, 16):
        s = HalfAdder(a=carry, b=inputs.in_[i])
        outputs.out[i] = s.sum
        carry = s.carry


@chip
def Add16(inputs, outputs):
    """Add two 16-bit inputs, ignoring overflow."""

    # For the LSB we only need a HalfAdder (because how we add numbers,
    # we don't have any carry on first digit)
    a = HalfAdder(a=inputs.a[0], b=inputs.b[0])
    outputs.out[0] = a.sum
    # After the LSB, we need to add the two bits plus the carry!
    # That's why we need a FullAdder!
    for i in range(1, 16):
        s = FullAdder(a=inputs.a[i], b=inputs.b[i], c=a.carry)
        outputs.out[i] = s.sum
        a = s


@chip
def Zero16(inputs, outputs):
    """Test whether a single 16-bit input has the value 0."""

    in_ = inputs.in_

    # We have to negate all bits, so we make the zero turn into a "signal" as 1,
    # flagging where the zeros were. Then we can AND everything. We will only
    # get a 1 as output if all bits are equal 1 (but because we inverted),
    # we'll get a 1 only when all bits are equal 0.

    # 0010 -> 1101 -> 10 -> 0
    # 1101 -> 0010 -> 00 -> 0
    # 1111 -> 0000 -> 00 -> 0
    # 0000 -> 1111 -> 11 -> 1

    # And to AND everything, we create this beautiful tree of ANDs :-)

    # 00 00 00 00 00 00 00 00
    #   00   00     00   00
    #      00         00 
    #           00

    outputs.out = And(a=And(a=And(a=And(a=Not(in_=in_[0 ]).out,
                                        b=Not(in_=in_[1 ]).out).out,
                                  b=And(a=Not(in_=in_[2 ]).out,
                                        b=Not(in_=in_[3 ]).out).out).out,
                            b=And(a=And(a=Not(in_=in_[4 ]).out,
                                        b=Not(in_=in_[5 ]).out).out,
                                  b=And(a=Not(in_=in_[6 ]).out,
                                        b=Not(in_=in_[7 ]).out).out).out).out,
                      b=And(a=And(a=And(a=Not(in_=in_[8 ]).out,
                                        b=Not(in_=in_[9 ]).out).out,
                                  b=And(a=Not(in_=in_[10]).out,
                                        b=Not(in_=in_[11]).out).out).out,
                            b=And(a=And(a=Not(in_=in_[12]).out,
                                        b=Not(in_=in_[13]).out).out,
                                  b=And(a=Not(in_=in_[14]).out,
                                        b=Not(in_=in_[15]).out).out).out).out).out


@chip
def Neg16(inputs, outputs):
    """Test whether a single 16-bit input is negative."""

    # Wow super easy! Because we're representing signed numbers as
    # 2-complement, the negative numbers will always have the MSB == 1,
    # so we just have to return it :-)

    outputs.out = inputs.in_[15]


@chip
def ALU(inputs, outputs):
    """Combine two 16-bit inputs according to six control bits, producing a 16-bit result and two
    condition codes.
    """

    x = inputs.x
    y = inputs.y

    zx = inputs.zx  # if zx == 1, replace x by 0
    nx = inputs.nx  # if nx == 1, negate/flip x
    zy = inputs.zy  # if zy == 1, replace y by 0
    ny = inputs.ny  # if ny == 1, negate/flip y
    f  = inputs.f   # if f == 1, ADD x y, otherwise, AND x y
    no = inputs.no  # if no == 1, negate/flip the output

    # The ALU looks difficult to implement but actually that's the easiest
    # chip, now that we have built all the required gates!
    #
    # The core trick is to use Mux as an IF!
    #
    # if selection: then else     is converted to    Mux16(then, else, selection)
    #
    # Let's see how to apply for all control bits!

    # If zx == 1, b is selected, so x is replaced by 0. Same for y.
    # Otherwise, x (or y) stay the same (going for the next operation in the chain!)
    x = Mux16(a=x, b=0, sel=zx).out
    y = Mux16(a=y, b=0, sel=zy).out

    # If nx == 1, b is selected, so x is replaced by ~x. Same for y
    # Otherwise, x (or y) stay the same
    x = Mux16(a=x, b=Not16(in_=x).out, sel=nx).out
    y = Mux16(a=y, b=Not16(in_=y).out, sel=ny).out

    # If f == 1, ADD x and y, otherwise AND x and y
    res = Mux16(a=And16(a=x, b=y).out, b=Add16(a=x, b=y).out, sel=f).out
    
    # If no == 1, ~res
    out = Mux16(a=res, b=Not16(in_=res).out, sel=no).out
    outputs.out = out

    # This is super simple! We just use the gates we created above straight!
    outputs.zr = Zero16(in_=out).out
    outputs.ng = Neg16(in_=out).out

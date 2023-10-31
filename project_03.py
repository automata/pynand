# Sequential Logic
#
# See https://www.nand2tetris.org/project03

from nand import chip, clock, lazy, DFF

from project_01 import *
from project_02 import *

# SOLVERS: remove this import to get started
from nand.solutions import solved_03


@chip
def MyDFF(inputs, outputs):
    #         load
    #           |
    #  in ----|\__,__ out
    #      .--|/  |
    #      `------'

    @chip
    def Latch(inputs, outputs):
        mux = lazy()
        mux.set(Mux(a=mux.out, b=inputs.in_, sel=inputs.enable))
        outputs.out = mux.out

    l1 = Latch(in_=inputs.in_, enable=clock)
    l2 = Latch(in_=l1.out, enable=Not(in_=clock).out)

    outputs.out = l2.out


@chip
def Bit(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load

    #         load
    #          |
    #  in ----|M\   
    #      .--|u )--[DFF^]-.--- out
    #      |  |x/          |
    #      '---------------'

    dff = lazy() # so we can use this as input before even defining it!
    mux = Mux(a=dff.out, b=in_, sel=load)
    dff.set(DFF(in_=mux.out))

    outputs.out = dff.out


@chip
def Register(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load

    # A register is basically a multibit Bit

    for i in range(16):
        outputs.out[i] = Bit(in_=in_[i], load=load).out


@chip
def RAM8(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # Built by an array of 8 registers.

    # With a DMux, we can say: when address 00000001, load input at register 0
    # when address 00000010, load input at register 1, etc
    
    #        address     
    #           | /|---.
    #            / |---|----.
    #           /D |---|----|----.
    #  load ---/ M |---|----|----|----.
    #          \ U |---|----|----|----|----.
    #           \X |---|----|----|----|----|----.
    #            \ |---|----|----|----|----|----|----.
    #             \|---|----|----|----|----|----|----|----.     address
    #                  |    |    |    |    |    |    |    |       |
    #           in--+-[R0]--|----|----|----|----|----|----|----|\ |
    #               +------[R1]--|----|----|----|----|----|----| \|
    #               +-----------[R2]--|----|----|----|----|----| M\
    #               +----------------[R3]--|----|----|----|----| U \____ out
    #               +---------------------[R4]--|----|----|----| X /
    #               +--------------------------[R5]--|----|----|  /
    #               +-------------------------------[R6]--|----| /
    #               +------------------------------------[R7]--|/

    # 1. Dmux will rout load to the register defined by address.
    # 2. If load=0, the register will output value stored in internal mux of register to Mux (read)
    #    If load=1, the register will store in to internal mux of register and send to Mux on next clock cycle (write)
    # 3. The address will select which of the registers to output in Mux with read or write operation results 

    sel = DMux8Way(in_=load, sel=address)
    r0 = Register(in_=in_, load=sel.a)
    r1 = Register(in_=in_, load=sel.b)
    r2 = Register(in_=in_, load=sel.c)
    r3 = Register(in_=in_, load=sel.d)
    r4 = Register(in_=in_, load=sel.e)
    r5 = Register(in_=in_, load=sel.f)
    r6 = Register(in_=in_, load=sel.g)
    r7 = Register(in_=in_, load=sel.h)

    outputs.out = Mux8Way16(a=r0.out, b=r1.out, c=r2.out, d=r3.out,
                            e=r4.out, f=r5.out, g=r6.out, h=r7.out, sel=address).out


@chip
def RAM64(inputs, outputs):

    # Built by an array of RAM8 blocks.

    # We'll have 2^6 = 64 words, so we need 6 bits to address all of them (xxxyyy)
    # The 3 MSB (xxx) will address the 2^3 = 8 RAM8 memory banks
    # The 3 LSB (yyy) will address the 2^3 = 8 registers inside each RAM8 cell

    # So, we use a shift operation to move the LSB to MSB, and with that we'll
    # be able to use a DMux with 8 outputs to select which memory bank.
    # Then we can pass the address straight to the memory bank to select the register within.
    # And in the end, we use a Mux to output the value on address.

    # 000001 - shift 3 -> 001000

    @chip
    def RShift3(inputs, outputs):
        outputs.out[0] = inputs.in_[3]
        outputs.out[1] = inputs.in_[4]
        outputs.out[2] = inputs.in_[5]

    shifted = RShift3(in_=inputs.address)
    load = DMux8Way(in_=inputs.load, sel=shifted.out)
    ram0 = RAM8(in_=inputs.in_, load=load.a, address=inputs.address)
    ram1 = RAM8(in_=inputs.in_, load=load.b, address=inputs.address)
    ram2 = RAM8(in_=inputs.in_, load=load.c, address=inputs.address)
    ram3 = RAM8(in_=inputs.in_, load=load.d, address=inputs.address)
    ram4 = RAM8(in_=inputs.in_, load=load.e, address=inputs.address)
    ram5 = RAM8(in_=inputs.in_, load=load.f, address=inputs.address)
    ram6 = RAM8(in_=inputs.in_, load=load.g, address=inputs.address)
    ram7 = RAM8(in_=inputs.in_, load=load.h, address=inputs.address)
    outputs.out = Mux8Way16(a=ram0.out, b=ram1.out, c=ram2.out, d=ram3.out,
                            e=ram4.out, f=ram5.out, g=ram6.out, h=ram7.out,
                            sel=shifted.out).out


@chip
def RAM512(inputs, outputs):

    # Built by an array of RAM64 blocks.

    # To address which 2^6 = 64 register we need 6 bits, so we shift
    # LSB to MSB in 6 bits. The rest is the same (using RAM64 now).

    @chip
    def RShift6(inputs, outputs):
        outputs.out[0] = inputs.in_[6]
        outputs.out[1] = inputs.in_[7]
        outputs.out[2] = inputs.in_[8]

    shifted = RShift6(in_=inputs.address)
    load = DMux8Way(in_=inputs.load, sel=shifted.out)
    ram0 = RAM64(in_=inputs.in_, load=load.a, address=inputs.address)
    ram1 = RAM64(in_=inputs.in_, load=load.b, address=inputs.address)
    ram2 = RAM64(in_=inputs.in_, load=load.c, address=inputs.address)
    ram3 = RAM64(in_=inputs.in_, load=load.d, address=inputs.address)
    ram4 = RAM64(in_=inputs.in_, load=load.e, address=inputs.address)
    ram5 = RAM64(in_=inputs.in_, load=load.f, address=inputs.address)
    ram6 = RAM64(in_=inputs.in_, load=load.g, address=inputs.address)
    ram7 = RAM64(in_=inputs.in_, load=load.h, address=inputs.address)
    outputs.out = Mux8Way16(a=ram0.out, b=ram1.out, c=ram2.out, d=ram3.out,
                            e=ram4.out, f=ram5.out, g=ram6.out, h=ram7.out,
                            sel=shifted.out).out


# SOLVERS: This has gotten repetitive by now, so just use the provided RAM4K and RAM16K
RAM4K = solved_03.RAM4K
RAM16K = solved_03.RAM16K


@chip
def PC(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    inc = inputs.inc
    reset = inputs.reset

    # ???

    reseted = lazy()
    pc = Register(in_=reseted.out, load=1)

    nxt = Inc16(in_=pc.out).out
    inced = Mux16(a=pc.out, b=nxt, sel=inc)
    loaded = Mux16(a=inced.out, b=in_, sel=load)
    reseted.set(Mux16(a=loaded.out, b=0, sel=reset))

    outputs.out = pc.out

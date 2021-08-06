#! /usr/bin/env python3

"""An alternative CPU which is backward compatible with the Nand to Tetris design, adding a handful of
new instructions which reduce most interactions with the stack to a single instructions/cycle.

The cost is adding a fourth register to hold SP, and a fair amount of additional logic to decode 2 more 
instruction formats (give or take), and to wrangle two more possible sources for the address to memory.

The VM translator is specialized to use the new instructions for push and pop operations, and to take
advantage of them not overwriting the A register.

The result is significant, but not quite mind-blowing:
- gates: about 1,800 (+40% from 1,262), but could probably be improved
- instruction count for Pong: 15.7k (-47% from 29.5k)
- cycles in Sys.init: 2.61m (-34% from 3.97m)

It's also a bit slower per cycle in simulation, resulting in approx. the same net performance 
(10s to init.)

Caveat: this design is probably not realistic in that the CPU may supply any of three addresses to 
the RAM (A, SP, or SP-1), based on instruction decoding, and then the RAM is read in the same cycle. 
In the real world, you would probably need to have the address available at the start of the cycle in
order for the RAM to be read in time. The original design does have that property, because the address
is _always_ A (from the previous cycle). That could be put right by pipelining the processor so that
instruction decoding is one cycle ahead of execution. Of course, there would be more registers (or at 
least more state to save,) and probably a one-cycle penalty on taken branches.

There is a temptation to add a few more instruction types, which would further complicate decoding but 
not require any new state:
- immediate loads and stores (e.g. A=@LCL, @LCL=A), for frame save/restore and access to temps
- load constant to D, to save an instruction and also avoid clobbering A in some cases.
See notes in Translator below on some places these would help.
"""

import re

from nand import *
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Xor, Not, Not16, Mux16
from nand.solutions.solved_02 import Inc16, Zero16, ALU
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC
from nand.solutions import solved_06
from nand.solutions import solved_07


def mkDec16(inputs, outputs):
    def mkHalfSub(inputs, outputs):
        """This is the same trick as HalfAdder, with the second input and the output inverted.
        """
        
        a = inputs.a
        neg_b = inputs.neg_b
        
        nand = Nand(a=a, b=neg_b).out
        not_a_or_not_b = Nand(a=a, b=nand).out
        a_or_b = Nand(a=nand, b=neg_b).out
        
        outputs.sum = Nand(a=not_a_or_not_b, b=a_or_b).out
        outputs.neg_carry = Not(in_=a_or_b).out

    HalfSub = build(mkHalfSub)
    
    neg_carry = outputs.out[0] = Not(in_=inputs.in_[0]).out
    for i in range(1, 16):
        sub = HalfSub(a=inputs.in_[i], neg_b=neg_carry)
        outputs.out[i] = sub.sum
        neg_carry = sub.neg_carry
    
Dec16 = build(mkDec16)


def mkSPCPU(inputs, outputs):
    """Implements the Hack architecture, plus two extra instructions:

    Pop to register:
      [AD]=--SP
      0b100_1_110000_AD0_000
      Bits A and/or D give the destination(s). Note: cannot pop to M, since the single-ported RAM 
      is busy reading the popped value. Also: for now, the ALU control bits must be set to the "M"
      pattern, to load the value from memory; any other pattern may or may not do anything useful.
    
    Push from ALU:
      SP++=<expr>
      bit pattern 0b100_0_XXXXXX_000_000
      Note: cannot refer to M, since the single-ported RAM is busy writing the pushed value.
    
    It is assumed that bits 13 and 14 of the instruction are always set for all other non-@ instructions.

    Note: the bit pattern corresponding to SP++=<expr>;<jmp> should be considered unsupported (and isn't 
    currently generated by parse_op).
    
    Location 0 in the RAM is never written or read; SP is stored in a register. Ordinary reads and 
    writes to location 0 are intercepted for backward compatibility with Hack programs (as long as they 
    set bits 13 and 14 as expected).
    """
    
    inM = inputs.inM                 # Value from the memory (M or top of stack)
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, x1, x0, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    is_sp = And(a=i, b=And(a=Not(in_=x1).out, b=Not(in_=x0).out).out).out
    push_bits = And(a=Not(in_=da).out, b=Not(in_=dd).out).out
    is_push = And(a=is_sp, b=push_bits).out
    is_pop = And(a=is_sp, b=Not(in_=push_bits).out).out

    is_write = And(a=dm, b=i).out  # The instruction writes to M

    a_reg = lazy()
    sp_reg = lazy()
    next_sp = Inc16(in_=sp_reg.out).out
    prev_sp = Dec16(in_=sp_reg.out).out  # TODO: would it be more efficient to re-use the same Inc16, by switching the input/output?
    
    a_zero = Zero16(in_=a_reg.out).out  # Meaning that M refers to SP
    
    is_sp_write = And(a=is_write, b=a_zero).out

    alu = lazy()
    
    a_reg.set(Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out))
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    sp_reg.set(Register(in_=Mux16(
                            a=alu.out,
                            b=Mux16(a=prev_sp, b=next_sp, sel=is_push).out,
                            sel=is_sp).out, 
                        load=Or(a=is_sp, b=is_sp_write).out))
    
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    
    # The Y input to the ALU:
    # is SP if expr refers to M and A is 0,
    # is from the RAM if the expr is --SP or refers to M,
    # otherwise it is A.
    alu_y = Mux16(
        a=Mux16(
            a=a_reg.out, 
            b=Mux16(
                a=inM, 
                b=sp_reg.out, 
                sel=a_zero).out, 
            sel=a).out,
        b=inM,
        sel=is_pop).out
    alu.set(ALU(x=d_reg.out, y=alu_y, zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))

    # output value to memory (to M or top of stack)
    outputs.outM = alu.out
    
    # write to memory?
    outputs.writeM = Or(a=And(a=is_write, b=Not(in_=a_zero).out).out, b=is_push).out
    
    # Address in data memory (of M or top of stack) (latched)
    outputs.addressM = Mux16(a=Mux16(a=a_reg.out, b=prev_sp, sel=is_pop).out, b=sp_reg.out, sel=is_push).out
    
    # address of next instruction (latched)
    outputs.pc = pc.out

    # expose SP for debugging purposes (since it's no longer found in the RAM)
    outputs.sp = sp_reg.out

SPCPU = build(mkSPCPU)


def mkSPComputer(inputs, outputs):
    """This is the same as regular Computer, except using SPCPU, and exposing `sp` as an output so that
    it can be inspected for tests and debugging.
    """
    
    reset = inputs.reset
    
    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(SPCPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc
    outputs.sp = cpu.sp
    outputs.tty_ready = mem.tty_ready

SPComputer = build(mkSPComputer)


def parse_op(string, symbols={}):
    m = re.match(r"([ADM]+)=--SP", string)
    if m:
        dest_a = 'A' in m.group(1)
        dest_d = 'D' in m.group(1)
        if 'M' in m.group(1):
            raise SyntaxError(f"M not allowed as a destination for pop: {string}")
        return (1 << 15) | (0b1_110000 << 6) | (dest_a << 5) | (dest_d << 4)
    
    m = re.match(r"SP\+\+=([^;]+)", string)
    if m:
        alu = solved_06.ALU_CONTROL.get(m.group(1))
        if alu is not None:
            return (1 << 15) | (alu << 6)
    
    return solved_06.parse_op(string, symbols)


def assemble(lines):
    return solved_06.assemble(lines, parse_op)


class Translator(solved_07.Translator):
    """Re-use most of the solution's translations, but strategically override most of the 
    access to SP.
    """
    
    def __init__(self):
        self.asm = AssemblySource()
        solved_07.Translator.__init__(self, self.asm)

    def push_constant(self, value):
        self.asm.start(f"push constant {value}")
        if value <= 1:
            self.asm.instr(f"SP++={value}")
        else:
            self.asm.instr(f"@{value}")
            self.asm.instr(f"SP++=A")

    def _pop_segment(self, segment_name, segment_ptr, index):
        self.asm.start(f"pop {segment_name} {index}")
        # Since pop doesn't overwrite A, a much simpler sequence works:
        if index == 0:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M")
        elif index == 1:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M+1")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr("D=A")
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=D+M")
        self.asm.instr("D=--SP")
        self.asm.instr("M=D")

    def _push_d(self):
        # TODO: no need for this as soon as everything's switched to use SP++ directly
        self.asm.instr("SP++=D")

    def _pop_d(self):
        # TODO: no need for this as soon as everything's switched to use SP++ directly?
        self.asm.instr("D=--SP")

    def _binary(self, opcode, op):
        self.asm.start(opcode)
        self.asm.instr("D=--SP")
        self.asm.instr("A=--SP")
        self.asm.instr(f"SP++={op.replace('M', 'A')}")

    def _unary(self, opcode, op):
        self.asm.start(opcode)
        self.asm.instr("D=--SP")
        self.asm.instr(f"SP++={op.replace('M', 'D')}")

    def function(self, class_name, function_name, num_vars):
        """Pushing zeros is a lot simpler now, saving a few instructions."""
        
        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{function_name}"

        self.asm.start(f"function {class_name}.{function_name} {num_vars}")
        self.asm.label(f"{self.function_namespace}")

        if num_vars == 0:
            # Tricky: this instruction has no effect; it's just here to take up space in the ROM and ensure that the
            # "function" op has a unique address assigned to it, so that it can appear in tracing and profiling. Yes, 
            # that is dumb.
            self.asm.instr("0")
        else:
            for _ in range(num_vars):
                self.asm.instr("SP++=0")

    def _compare(self, op):
        # Saves about 4 instuctions each time, or a few % at runtime.
        
        label = self.asm.next_label(f"{op.lower()}_common")
        end_label = self.asm.next_label(f"{op.lower()}_common$end")
        self.asm.start(f"{op.lower()}_common")
        self.asm.label(label)
        self.asm.instr("@R15")    # R15 = D (the return address)
        self.asm.instr("M=D")
        
        # D = top, M = second from top
        self.asm.instr("D=--SP")
        self.asm.instr("A=--SP")

        # Compare
        self.asm.instr("D=A-D")
        
        # Set result True, optimistically
        self.asm.instr("SP++=-1")
        
        self.asm.instr(f"@{end_label}")
        self.asm.instr(f"D;J{op}")
        
        # Set result False
        self.asm.instr("D=--SP")  # Drop speculative result
        self.asm.instr("SP++=0")

        self.asm.label(end_label)
        self.asm.instr("@R15")   # JMP to R15
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")
        return label

    def _call(self):
        """Common sequence for all calls.
        
        D = num_args
        R14 = callee address
        stack: return address already pushed
        
        Note: this is about 16 instructions better in all, by reducing each push to a single instruction
        and keeping the new ARG address in D while the segment pointers are pushed. The total is now 24,
        not to mention the 10 or so at each point of use that then jumps here. That's still frustratingly
        many.
        
        Possible improvements:
        - pass the callee address on the stack, now that it's cheaper?
        - with an immediate load instruction (e.g. A=@LCL), save 5 cycles
        - with an immediate store (e.g. @LCL=A), save another 3
        
        Possibly bigger return from a smarter compiler that avoids saving a full frame when calling 
        functions that won't use/clobber everything. This is the familiar "leaf function" optimization.
        """
        
        label = self.asm.next_label("call_common")

        self.asm.start(f"call_common")
        self.asm.label(label)

        # D = SP - (D + 1) (which will be the new ARG)
        self.asm.instr("@SP")
        self.asm.instr("D=M-D")
        self.asm.instr("D=D-1")

        # push four segment pointers:
        self.asm.instr("@LCL")
        self.asm.instr("A=M")
        self.asm.instr("SP++=A")
        self.asm.instr("@ARG")
        self.asm.instr("A=M")
        self.asm.instr("SP++=A")
        self.asm.instr("@THIS")
        self.asm.instr("A=M")
        self.asm.instr("SP++=A")
        self.asm.instr("@THAT")
        self.asm.instr("A=M")
        self.asm.instr("SP++=A")

        # ARG = D
        self.asm.instr("@ARG")
        self.asm.instr("M=D")

        # LCL = SP
        # Note: setting LCL here (as opposed to in "function") feels wrong, but it makes the 
        # state of the segment pointers consistent after each opcode, so it's easier to debug.
        self.asm.instr("@SP")
        self.asm.instr("D=M")
        self.asm.instr("@LCL")
        self.asm.instr("M=D")

        # JMP to R14 (the callee)
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")
        return label


    # TODO: improve the common sequence for `return`.


    def finish(self):
        pass


if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    SP_PLATFORM = computer.Platform(
        chip=SPComputer,
        assemble=assemble,
        parse_line=solved_07.parse_line,
        translator=Translator)

    computer.main(SP_PLATFORM)

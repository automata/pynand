from nand.solutions import solved_05, solved_06
from nand import run


ASM = """

// Initialize R2 to 0
@R2
M=0

(loop)
     @2        // store R2 in A
     D=M       // D = M[R2]
     @0
     D=D+M
     @2
     M=D       // store result in M[R2]
     @1
     D=M
     @1
     D=D-A
     @1
     M=D       // decrement R1
     @end
     D;JEQ     // finish if counter reached 0
     @loop
     0;JMP     // otherwise, loop it again
(end)
    @end
    0;JMP

""".split("\n")

ASM2 = """

  // Initialize R2 to 0
  @R2
  M=0
  
  // Test for R1 == 0 and exit early
  @R1
  D=M
  @halt
  D;JLE
  
(loop)
  @R0
  D=M
  @halt
  D;JLE

  // Add R1 to R2:
  @1
  D=M
  @R2
  M=D+M
  
  // Subtract 1 from R0 (in place)
  @R0
  M=M-1
  
  @loop
  0;JMP

(halt)

""".split("\n")

if __name__ == '__main__':
    Computer = solved_05.Computer
    assemble = solved_06.assemble
    computer = run(Computer)

    pgm, _, _ = assemble(ASM)
    computer.init_rom(pgm)
    computer.poke(0, 3)
    computer.poke(1, 1)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(120):
        computer.ticktock()
        print(computer, 'R0', computer.peek(0), 'R1', computer.peek(1), 'R2', computer.peek(2))
    assert computer.peek(2) == 3
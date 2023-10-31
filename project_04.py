# Machine Language
#
# See https://www.nand2tetris.org/project04

# SOLVERS: remove this import to get started
from nand.solutions import solved_04


# SOLVERS: MULT_ASM and FILL_ASM should be a lists of strings, each one an assembly instruction.
#

# Multiplies R0 and R1 and stores the result in R2.
# (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

# MULT_ASM = """
# // Here's where the magic happens:
# (top)
#   @0
# ...
# """.split('\n') 

# MULT_ASM = solved_04.MULT_ASM

MULT_ASM = """

// R2 = R0 * R1
//      R0 + R0 + R0 + R0 ... + R0 (R1 times)
//      sum_0^{R1} R0_i
// counter, from R1 to 0, do R2 = R2 + R2

@R2      // M[R2] = 0
M=0

(loop) 
    @2       // store R2 in A
    D=M      // D = M[R2]
    @R2
    D=D+M    // do the multiplication step: D = M[R2] + R2
    @R2
    M=D      // store the current multiplication step in M[R2] (update M[R2])
    @R1      // counter, from R1 to 0
    D=M      // put the counter in register: D = M[R1]
    @1       // load a constant (step)
    D=D-A    // decrement 1 from D (which is actually R1)
    @R1
    M=D      // store the counter in M[R1]: M[R1] = M[R1] - 1
@end
    D;JEQ    // if counter is equal to zero, jump to end
    @loop
    0;JMP    // otherwise, do one more step    
    (end)
@end
    0;JMP

""".split("\n")



# Runs an infinite loop that listens to the keyboard input.
# When a key is pressed (any key), the program blackens the screen,
# i.e. writes "black" in every pixel;
# the screen should remain fully black as long as the key is pressed.
# When no key is pressed, the program clears the screen, i.e. writes
# "white" in every pixel;
# the screen should remain fully clear as long as no key is pressed.

# FILL_ASM = """
# // Here's where the magic happens:
# (top)
#   @0
# ...
# """.split('\n')

FILL_ASM = solved_04.FILL_ASM
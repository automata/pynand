# Machine Language
#
# See https://www.nand2tetris.org/project04

# SOLVERS: remove this import to get started
from nand.solutions import solved_04

# Multiplies R0 and R1 and stores the result in R2.

MULT_ASM = """

// Initialize R2 to 0
@2
M=0

// If R1 == 0, exit early
@1
D=M
@end
D;JLE

(loop)
     @2        // or @R2... store R2 in A
     D=M       // D = M[R2]
     @0
     D=D+M
     @2
     M=D       // store result in M[R2]
     @1
     D=M
     @1
     M=D-1
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
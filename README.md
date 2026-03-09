#README
RISC-V Assembler Project

About this project:
In this project, we have built a simple assembler using Python. An assembler is a program that converts assembly language instructions into machine code (binary numbers). Computers cannot understand assembly language directly, so an assembler does that work by translating each instruction into a 32-bit binary format that the processor can execute. Our program reads an input file that contains RISC-V assembly instructions and produces an output file with the binary instructions, also checking for program errors, such as invalid registers, wrong instructions, or incorrect labels. If there is an error in the code, the assembler prints the line number where the problem occurred, making it easier to find and fix.

What we learned from doing this project:
We understood how the assembly instructions are converted into machine code, also learning. how different instruction types in RISC-V work, such as R-type, I-type, S-type, B-type, U-type, and J-type instructions. Each instruction type has its own format, and the assembler places the correct bits in the correct positions to build the final binary instruction.
We also learned how labels work in assembly programs. Labels act like markers in the code, due to which branch and jump instructions know where to go. Our assemblers first scan the entire program to collect all labels and their addresses, and then it uses those addresses when generating the final machine code.
Another important thing we learned is how to detect errors in a program(debugging). The assembler checks for problems like duplicate labels, invalid instructions, wrong registers,  jump overflow and so on. This helped us understand how real programming tools check programs before running them.

Overall, this project helped us understand how assembly instructions are translated into binary format that the CPU executes.

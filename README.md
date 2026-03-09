#README
RISC-V Assembler Project

About the Project

In this project, we built a simple assembler using Python. An assembler is a program that converts assembly language instructions into machine code (binary format). Since computers cannot directly understand assembly language, the assembler acts as a translator that converts each instruction into a 32-bit binary instruction that the processor can execute.
Our program reads an input file containing RISC-V assembly instructions and generates an output file with the corresponding binary instructions. While doing this, the assembler also checks the program for errors such as invalid registers, unsupported instructions, incorrect labels, or syntax issues. If an error is detected, the program reports the line number where the problem occurred, making it easier to locate and fix the issue.

What We Learned

Through this project, we gained a deeper understanding of how assembly instructions are converted into machine code. We also learned about the different instruction formats used in the RISC-V architecture, including R-type, I-type, S-type, B-type, U-type, and J-type instructions. Each of these instruction types follows a specific format, and the assembler places the required bits in the correct positions to generate the final binary instruction.
Another key concept we explored was the use of labels in assembly programs. Labels act as markers in the code and are mainly used by branch and jump instructions to determine where execution should move next. To handle this, our assembler first scans the entire program to identify all labels and their corresponding addresses. These addresses are then used when generating the final machine code.
We also learned how important error detection and debugging are in programming tools. The assembler checks for issues such as duplicate labels, invalid instructions, incorrect register names, and jump overflow errors. Implementing these checks helped us understand how real compilers and assemblers validate code before execution.

Conclusion
Overall, this project gave us practical insight into how low-level assembly instructions are translated into binary machine code that the CPU can understand and execute.

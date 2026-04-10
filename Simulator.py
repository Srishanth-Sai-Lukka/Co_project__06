import sys

DATA_MEM_BASE = 0x00010000
DATA_MEM_SIZE = 32          
STACK_BASE    = 0x00000100
STACK_SIZE    = 32          
SP_INIT       = 0x0000017C
HALT_ENCODING = 0x00000063  

class Memory:
    """Flat word-addressed memory covering data segment and stack."""

    def __init__(self):
        self._words = [0] * (DATA_MEM_SIZE + STACK_SIZE)

    def _resolve(self, byte_address):
        addr = byte_address & 0xFFFFFFFF
        if DATA_MEM_BASE <= addr < DATA_MEM_BASE + DATA_MEM_SIZE * 4:
            return (addr - DATA_MEM_BASE) // 4
        elif STACK_BASE <= addr < STACK_BASE + STACK_SIZE * 4:
            return DATA_MEM_SIZE + (addr - STACK_BASE) // 4
        else:
            print(f"Memory error: address 0x{addr:08X} out of range")
            sys.exit(1)

    def load(self, byte_address):
        return self._words[self._resolve(byte_address)]

    def store(self, byte_address, value):
        self._words[self._resolve(byte_address)] = value & 0xFFFFFFFF

    def dump(self):
        """Return list of (address, value) for the data segment only."""
        return [
            (DATA_MEM_BASE + i * 4, self._words[i])
            for i in range(DATA_MEM_SIZE)
        ]

class RegisterFile:
    """32 RISC-V integer registers; x0 is always zero."""

    def __init__(self):
        self._r = [0] * 32
        self._r[2] = SP_INIT   

    def read(self, index):
        return self._r[index]

    def write(self, index, value):
        if index != 0:                      
            self._r[index] = value & 0xFFFFFFFF

    def all_values(self):
        return list(self._r)
        
def bits(word, hi, lo):
    """Extract bits [hi:lo] inclusive from a 32-bit integer."""
    mask = (1 << (hi - lo + 1)) - 1
    return (word >> lo) & mask


def sign_extend(value, width):
    """Sign-extend 'value' from 'width' bits to a full Python int."""
    if value & (1 << (width - 1)):
        value -= (1 << width)
    return value


def as_signed(val):
    val = val & 0xFFFFFFFF
    return val - 0x100000000 if val >= 0x80000000 else val


def as_unsigned(val):
    return val & 0xFFFFFFFF

def extract_fields(word):
    opcode = bits(word, 6,  0)
    rd     = bits(word, 11, 7)
    funct3 = bits(word, 14, 12)
    rs1    = bits(word, 19, 15)
    rs2    = bits(word, 24, 20)
    funct7 = bits(word, 31, 25)

    # I-type immediate
    imm_i = sign_extend(bits(word, 31, 20), 12)

    # S-type immediate
    imm_s = sign_extend((bits(word, 31, 25) << 5) | bits(word, 11, 7), 12)

    # B-type immediate
    imm_b = sign_extend(
        (bits(word, 31, 31) << 12) |
        (bits(word, 7,  7)  << 11) |
        (bits(word, 30, 25) << 5)  |
        (bits(word, 11, 8)  << 1),
        13
    )

    # U-type immediate
    imm_u = sign_extend(bits(word, 31, 12) << 12, 32)

    # J-type immediate
    imm_j = sign_extend(
        (bits(word, 31, 31) << 20) |
        (bits(word, 19, 12) << 12) |
        (bits(word, 20, 20) << 11) |
        (bits(word, 30, 21) << 1),
        21
    )

    return {
        "opcode": opcode, "rd": rd, "funct3": funct3,
        "rs1": rs1, "rs2": rs2, "funct7": funct7,
        "imm_i": imm_i, "imm_s": imm_s, "imm_b": imm_b,
        "imm_u": imm_u, "imm_j": imm_j,
    }

class CPU:

    def __init__(self):
        self.regs = RegisterFile()
        self.mem  = Memory()
        self.pc   = 0x00000000
        self._build_dispatch()

    def _build_dispatch(self):
        """Map (opcode, funct3, funct7) tuples to handler methods."""
        R = lambda f3, f7, fn: ((0b0110011, f3, f7), fn)
        I = lambda op, f3, fn: ((op,        f3, -1), fn)
        S = lambda f3, fn:     ((0b0100011, f3, -1), fn)
        B = lambda f3, fn:     ((0b1100011, f3, -1), fn)

        self._table = dict([
            # R-type
            R(0b000, 0b0000000, self._add),
            R(0b000, 0b0100000, self._sub),
            R(0b001, 0b0000000, self._sll),
            R(0b010, 0b0000000, self._slt),
            R(0b011, 0b0000000, self._sltu),
            R(0b100, 0b0000000, self._xor),
            R(0b101, 0b0000000, self._srl),
            R(0b101, 0b0100000, self._sra),
            R(0b110, 0b0000000, self._or),
            R(0b111, 0b0000000, self._and),
            # I-type arithmetic
            I(0b0010011, 0b000, self._addi),
            I(0b0010011, 0b011, self._sltiu),
            # Loads
            I(0b0000011, 0b010, self._lw),
            # JALR
            I(0b1100111, 0b000, self._jalr),
            # S-type
            S(0b010, self._sw),
            # B-type
            B(0b000, self._beq),
            B(0b001, self._bne),
            B(0b100, self._blt),
            B(0b101, self._bge),
            B(0b110, self._bltu),
            B(0b111, self._bgeu),
        ])
        
        self._use_funct7 = {0b0110011}
        self._special = {
            0b0110111: self._lui,
            0b0010111: self._auipc,
            0b1101111: self._jal,
        }

    def _add(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) + self.regs.read(f["rs2"])))
        return pc + 4

    def _sub(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) - self.regs.read(f["rs2"])))
        return pc + 4

    def _sll(self, f, pc):
        shamt = self.regs.read(f["rs2"]) & 0x1F
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) << shamt))
        return pc + 4

    def _slt(self, f, pc):
        result = 1 if as_signed(self.regs.read(f["rs1"])) < as_signed(self.regs.read(f["rs2"])) else 0
        self.regs.write(f["rd"], result)
        return pc + 4

    def _sltu(self, f, pc):
        result = 1 if as_unsigned(self.regs.read(f["rs1"])) < as_unsigned(self.regs.read(f["rs2"])) else 0
        self.regs.write(f["rd"], result)
        return pc + 4

    def _xor(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) ^ self.regs.read(f["rs2"])))
        return pc + 4

    def _srl(self, f, pc):
        shamt = self.regs.read(f["rs2"]) & 0x1F
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"])) >> shamt)
        return pc + 4

    def _sra(self, f, pc):
        shamt = self.regs.read(f["rs2"]) & 0x1F
        self.regs.write(f["rd"], as_unsigned(as_signed(self.regs.read(f["rs1"])) >> shamt))
        return pc + 4

    def _or(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) | self.regs.read(f["rs2"])))
        return pc + 4

    def _and(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) & self.regs.read(f["rs2"])))
        return pc + 4

    def _addi(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(self.regs.read(f["rs1"]) + f["imm_i"]))
        return pc + 4

    def _sltiu(self, f, pc):
        imm_u = as_unsigned(f["imm_i"])
        result = 1 if as_unsigned(self.regs.read(f["rs1"])) < imm_u else 0
        self.regs.write(f["rd"], result)
        return pc + 4

    def _lw(self, f, pc):
        addr = as_unsigned(self.regs.read(f["rs1"]) + f["imm_i"])
        self.regs.write(f["rd"], self.mem.load(addr))
        return pc + 4

    def _jalr(self, f, pc):
        ret = as_unsigned(pc + 4)
        target = as_unsigned(self.regs.read(f["rs1"]) + f["imm_i"]) & 0xFFFFFFFE
        self.regs.write(f["rd"], ret)
        return target

    def _sw(self, f, pc):
        addr = as_unsigned(self.regs.read(f["rs1"]) + f["imm_s"])
        self.mem.store(addr, self.regs.read(f["rs2"]))
        return pc + 4

    def _beq(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_signed(self.regs.read(f["rs1"])) == as_signed(self.regs.read(f["rs2"])) else pc + 4

    def _bne(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_signed(self.regs.read(f["rs1"])) != as_signed(self.regs.read(f["rs2"])) else pc + 4

    def _blt(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_signed(self.regs.read(f["rs1"])) < as_signed(self.regs.read(f["rs2"])) else pc + 4

    def _bge(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_signed(self.regs.read(f["rs1"])) >= as_signed(self.regs.read(f["rs2"])) else pc + 4

    def _bltu(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_unsigned(self.regs.read(f["rs1"])) < as_unsigned(self.regs.read(f["rs2"])) else pc + 4

    def _bgeu(self, f, pc):
        return as_unsigned(pc + f["imm_b"]) if as_unsigned(self.regs.read(f["rs1"])) >= as_unsigned(self.regs.read(f["rs2"])) else pc + 4

    def _lui(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(f["imm_u"]))
        return pc + 4

    def _auipc(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(pc + f["imm_u"]))
        return pc + 4

    def _jal(self, f, pc):
        self.regs.write(f["rd"], as_unsigned(pc + 4))
        return as_unsigned(pc + f["imm_j"]) & 0xFFFFFFFE

    def step(self, word):
        f = extract_fields(word)
        opcode = f["opcode"]
        funct3 = f["funct3"]
        funct7 = f["funct7"] if opcode in self._use_funct7 else -1

        if opcode in self._special:
            return self._special[opcode](f, self.pc)

        handler = self._table.get((opcode, funct3, funct7))
        if handler is None:
            print(f"Error: unrecognised instruction (opcode=0b{opcode:07b} funct3={funct3:03b})")
            sys.exit(1)

        return handler(f, self.pc)

    def format_state(self, pc_to_print):
        pc_str  = "0b" + format(pc_to_print & 0xFFFFFFFF, "032b")
        reg_str = " ".join("0b" + format(v & 0xFFFFFFFF, "032b") for v in self.regs.all_values())
        return pc_str + " " + reg_str

    def format_memory_dump(self):
        lines = []
        for addr, val in self.mem.dump():
            lines.append(f"0x{addr:08X}:0b{val & 0xFFFFFFFF:032b}")
        return lines

HALT_WORD = 0x00000063   


def load_program(path):
    program = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                program.append(int(line, 2))   
    return program


def main():
    if len(sys.argv) < 3:
        print("Usage: python simulator_alternate.py <input_file> <output_file>")
        sys.exit(1)

    program     = load_program(sys.argv[1])
    output_path = sys.argv[2]
    cpu         = CPU()
    trace_lines = []

    while True:
        idx = cpu.pc // 4

        if idx < 0 or idx >= len(program):
            print(f"Error: PC 0x{cpu.pc:08X} out of bounds")
            sys.exit(1)

        word = program[idx]

        if word == HALT_WORD:
            trace_lines.append(cpu.format_state(cpu.pc))
            break

        next_pc  = cpu.step(word)
        cpu.pc   = next_pc
        trace_lines.append(cpu.format_state(cpu.pc))

    with open(output_path, "w") as out:
        for line in trace_lines:
            out.write(line + "\n")
        for line in cpu.format_memory_dump():
            out.write(line + "\n")

if __name__ == "__main__":
    main()

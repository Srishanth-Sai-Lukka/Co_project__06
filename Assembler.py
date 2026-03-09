import sys
# Registers 
REG = {
"zero":"00000","ra":"00001","sp":"00010","gp":"00011","tp":"00100",
"t0":"00101","t1":"00110","t2":"00111",
"s0":"01000","s1":"01001",
"a0":"01010","a1":"01011","a2":"01100","a3":"01101","a4":"01110","a5":"01111","a6":"10000","a7":"10001",
"s2":"10010","s3":"10011","s4":"10100","s5":"10101","s6":"10110","s7":"10111",
"s8":"11000","s9":"11001","s10":"11010","s11":"11011",
"t3":"11100","t4":"11101","t5":"11110","t6":"11111"
}

# Instruction Tables
R = {
"add":("0000000","000","0110011"),
"sub":("0100000","000","0110011"),
"sll":("0000000","001","0110011"),
"slt":("0000000","010","0110011"),
"sltu":("0000000","011","0110011"),
"xor":("0000000","100","0110011"),
"srl":("0000000","101","0110011"),
"or":("0000000","110","0110011"),
"and":("0000000","111","0110011")
}
I = {
"addi":("000","0010011"),
"sltiu":("011","0010011"),
"lw":("010","0000011"),
"jalr":("000","1100111")
}
S = {"sw":("010","0100011")}
B = {
"beq":("000","1100011"),
"bne":("001","1100011"),
"blt":("100","1100011"),
"bge":("101","1100011"),
"bltu":("110","1100011"),
"bgeu":("111","1100011")
}
U = {"lui":"0110111","auipc":"0010111"}
J = {"jal":"1101111"}

# Helper Functions
def binN(val,bits):
  if val<0:
    val=(1<<bits) + val
  return bin(val)[2:].zfill(bits)

def parse_int(x):
  try:
    return int(x,0)
  except:
    return None
    
#helper for removing label
def remove_label(line):
  if ':' in line:
    return line.split(':',1)[1].strip()
  return line

# Error Handling
def check_imm(val,bits,ln):
  if val is None:
    print("Error at line", ln,": Invalid immediate")
    return False
  low = -(1<<(bits-1))
  high = (1<<(bits-1)) - 1
  if val < low or val > high:
    print("Error at line", ln,": Immediate out of range")
    return False
  return True

def check_reg(r,ln):
  if r not in REG:
    print("Error at line",ln,": Unknown register",r)
    return False
  return True

def check_ops(p,count,ln):
  if len(p) != count:
    print("Error at line",ln,": Wrong operand count")
    return False
  return True

# Helper Functions
def clean(line):
  if '#' in line:
    line=line[:line.index("#")]
  if '//' in line:
    line=line[:line.index('//')]
  return line.strip()

def tokens(line):
  line=line.replace(","," ").replace("("," ").replace(")"," ")
  return line.split()

def collect_labels(lines):
  labels={}
  pc=0
  for line in lines:
    line=clean(line)
    if not line:
      continue
    if ':' in line:
      label,rest=line.split(":",1)
      label=label.strip()
      if label in labels:
        print("Error: Duplicate Label",label)
        return None
      labels[label]=pc
      if rest.strip():
        pc+=4
    else:
      pc+=4
  return labels

# Virtual Halt Check
def check_halt(lines):
  last=None

  for line in lines:
    line=clean(line)
    if not line:
      continue
    line=remove_label(line)
    if not line:
      continue
    last = tokens(line)
    
    if not last:
      print("Error:program empty")
      return False

  if not (len(last) == 4 and last[0] == "beq" and last[1] == "zero" and last[2] == "zero"):
    print("Error: Missing virtual halt")
    return False

  return True

# Main Assembler
def assemble(inp,outp):
  try:
    with open(inp) as f:
      lines = f.readlines()
  except FileNotFoundError:
    print("Error: Input file not found")
    return

  if not check_halt(lines):
    return

  labels = collect_labels(lines)

  if labels is None:
    return

  pc = 0
  out = []

  for ln,line in enumerate(lines,1):
    line = clean(line)

    if not line:
      continue
    line=remove_label(line)
  
    if not line:
      continue

    p = tokens(line)
    op = p[0]

    try:
      # R type:
      if op in R:
        if not check_ops(p,4,ln):
          return
        rd, rs1, rs2 = p[1], p[2], p[3]
        if not(check_reg(rd,ln) and check_reg(rs1,ln) and check_reg(rs2,ln)):
          return
        f7, f3, opc = R[op]
        code = f7 + REG[rs2] + REG[rs1] + f3 + REG[rd] + opc
        
      # I type:
      elif op in I and op != "lw":
        if not check_ops(p,4,ln):
          return
        rd, rs1, imm = p[1], p[2], parse_int(p[3])
        if not(check_reg(rd,ln) and check_reg(rs1,ln)):
          return
        f3, opc = I[op]
        code = binN(imm,12) + REG[rs1] + f3 + REG[rd] + opc
        
      elif op == "lw":
        if not check_ops(p,4,ln):
          return
        rd, imm, rs1 = p[1], parse_int(p[2]),p[3]
        if not(check_reg(rd,ln) and check_reg(rs1,ln)):
          return
        if not check_imm(imm,12,ln):
          return
        f3, opc = I["lw"]
        code = binN(imm,12) + REG[rs1] + f3 + REG[rd] + opc
    
      # S type:
      elif op in S:
        rs2, imm, rs1 = p[1], parse_int(p[2]),p[3]
        f3, opc = S[op]
        imm = binN(imm,12)
        code = imm[:7] + REG[rs2] + REG[rs1] + f3 + imm[7:] + opc

      # B type:
      elif op in B:
        rs1, rs2, target = p[1], p[2], p[3]
        
        if target in labels:
          off = labels[target] - pc
        else:
          off = parse_int(target)
          if off is None:
            print("Error at line",ln,": Undefined label",target)
            return

          if off % 2 != 0:
            print("Error at line",ln,": Misaligned branch offset")
            return

          if not check_imm(off,13,ln): 
            return
            
        imm = binN(off,13)
        f3, opc = B[op]
        code = imm[0] + imm[2:8] + REG[rs2] + REG[rs1] + f3 + imm[8:12] + imm[1] + opc
        
      # U type:
      elif op in U:
        rd, imm = p[1], parse_int(p[2])
        opc = U[op]
        code = binN(imm,20) + REG[rd] + opc
        
      # J type:
      elif op in J:
        rd, target = p[1], p[2]
        
        if target in labels:
          off = labels[target] - pc
        else:
          off = parse_int(target)
          if off is None:
            print("Error at line",ln,": Undefined label",target)
            return

          if off % 2 != 0:
            print("Error at line",ln,": Misaligned jump offset")
            return

          if not check_imm(off,21,ln): 
            return
            
        imm = binN(off,21)
        opc = J[op]
        code = imm[0] + imm[10:20] + imm[9] + imm[1:9] + REG[rd] + opc

      else: 
        print("Error at line", ln, ": Invalid instruction")
        return
        
    except:
      print("Error at line",ln)
      return
      
    out.append(code)
    pc+=4
    
  with open(outp,"w") as f:
    for x in out:
      f.write(x + "\n")

# Calling Function 
if __name__ == "__main__":
  
  if len(sys.argv) != 3:
    print("Usage: python3 assmbler.py input.asm output.bin")
  else:
    assemble(sys.argv[1],sys.argv[2])

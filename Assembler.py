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

# Utlity 
def binN(val,bits):
  if val<0:
    val=(1<<bits) + val
  return bin(val)[2:].zfill(bits)

def parse_int(x):
  try:
    return int(x,0)
  except:
    return None

def clean(line):
  if '#' in line:
    line=line[:line.index("#")]
  if '//' in line:
    line=line[:line.index('//')]
  return line.strip()

def tokens(line):
  line=line.replace(","," ").replace("("," ").replace(")"," ")
  return line.split()

# 1st pass (collect labels)
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
  last = None

  for line in lines:
    line = clean(line)
    if not line:
      continue
    if ":" in line:
      line = line.split(":",1)[1].strip()
    if not line:
      continue
    last = tokens(line)

  if last!=["beq","zero","zero","0"]:
    print("Error: Missing virtual halt")
    return False

  return True

# Main Assembler
def assemble(inp,outp):
  with open(inp) as f:
    lines = f.readlines()

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
    if ":" in line:
      line = line.split(":",1)[1].strip()
    if not line:
      continue

    p = tokens(line)
    op = p[0]

    try:
      # R type:
      if op in R:
        rd, rs1, rs2 = p[1], p[2], p[3]
        f7, f3, opc = R[op]
        code = f7 + REG[rs2] + REG[rs1] + f3 + REG[rd] + opc
        
    except:
      print("Error at line", ln)
      return
      

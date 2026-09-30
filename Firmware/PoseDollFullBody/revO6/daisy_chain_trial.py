"""DC1 digital feasibility only. Not connected to G0/UE and never capture eligible."""
from dataclasses import dataclass
REGISTERS=(0x3FFD,0x3FFE,0x3FFF,0x0016,0x0017)
MAX_CHAIN=9
PARITY=1
SENSOR=2
MAGNET=4
OTP=8
def command(address):
 if not 0<=address<=0x3FFF:raise ValueError('address')
 v=0x4000|address
 return v|((v.bit_count()&1)<<15)
def requests(count):
 if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=MAX_CHAIN:raise ValueError('chain length')
 return [[command(a)]*count for a in REGISTERS]+[[0]*count]
@dataclass(frozen=True)
class TrialScan:
 angles:tuple
 faults:tuple
 mathematically_valid:bool
 capture_eligible:bool=False
 def __post_init__(self):
  if self.capture_eligible:raise ValueError('DC1 has no qualified physical binding or capture path')
def decode_pipeline(rx,count):
 requests(count)
 if len(rx)!=6 or any(len(row)!=count for row in rx):raise ValueError('incomplete pipeline')
 if any(not isinstance(v,int) or isinstance(v,bool) or not 0<=v<=0xFFFF for row in rx for v in row):raise ValueError('word')
 angles=[];faults=[]
 for physical_port in range(count): # declared order: nearest device = port 0
  wire_index=count-1-physical_port
  words=[rx[k][wire_index] for k in range(1,6)] # burst 0 is previous/undefined data
  fault=0
  for w in words:
   if w.bit_count()&1:fault|=PARITY
   if w&0x4000:fault|=SENSOR
  diag,mag,angle,hi,lo=[w&0x3FFF for w in words]
  if not diag&0x100 or diag&0xE00:fault|=MAGNET
  if ((hi&255)<<6)|(lo&63):fault|=OTP
  angles.append(angle);faults.append(fault)
 return TrialScan(tuple(angles),tuple(faults),not any(faults))


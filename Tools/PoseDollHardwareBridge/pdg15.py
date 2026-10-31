"""PDG15/1 raw46 transport candidate. Distinct from immutable PDG5/PD41.
CRC detects transmission errors, not malicious forgery. Declared chain lengths
are configuration, not proof that 46 physical sensors exist.
"""
import struct,zlib
MAGIC=b'P15R';VERSION=1;BYTES=192
PROBE,HELLO,REQUEST,ACCEPTED,SCAN,CANCEL,STOP,ERROR,READ,BODY_SCAN=range(10)
COUNTS=(6,4,10,10,8,8);MASK=(1<<46)-1
# 88-byte header, 8-byte validity mask, 92-byte words, 4-byte CRC.
HEADER=struct.Struct('<4sBBHQQQ16sIIQQQ6B2x')
assert HEADER.size==88
FAULT=0x8000


def integer(v,bits):
 if type(v) is not int or not 0<=v<1<<bits:raise ValueError('integer width/type')
 return v


def encode(m):
 typ=integer(m.get('type',PROBE),8)
 if typ>BODY_SCAN:raise ValueError('type')
 counts=tuple(m.get('counts',COUNTS));words=list(m.get('words',[FAULT]*46));capture=m.get('capture',bytes(16));mask=integer(m.get('valid_mask',0),64)
 if counts!=COUNTS or len(words)!=46 or not isinstance(capture,bytes) or len(capture)!=16 or mask&~MASK:raise ValueError('layout')
 for w in words:integer(w,16)
 values=[integer(m.get(k,0),64) for k in ('device','gateway_boot','body_boot')]
 clocks=[integer(m.get(k,0),64) for k in ('request_us','start_us','end_us')]
 raw=HEADER.pack(MAGIC,VERSION,typ,0,*values,capture,integer(m.get('scan',0),32),integer(m.get('token',0),32),*clocks,*counts)+struct.pack('<Q46H',mask,*words)
 assert len(raw)==188
 wire=raw+struct.pack('<I',zlib.crc32(raw)&0xffffffff)
 decode(wire)
 return wire


def decode(raw):
 if len(raw)!=BYTES or raw[:4]!=MAGIC or zlib.crc32(raw[:-4])&0xffffffff!=struct.unpack_from('<I',raw,188)[0]:raise ValueError('framing/CRC')
 v=HEADER.unpack_from(raw)
 if v[1]!=VERSION or v[2]>BODY_SCAN or v[3]!=0 or raw[86:88]!=b'\0\0' or tuple(v[13:19])!=COUNTS:raise ValueError('version/layout/reserved')
 mask,*words=struct.unpack_from('<Q46H',raw,88)
 if mask&~MASK:raise ValueError('mask')
 m=dict(zip(('device','gateway_boot','body_boot'),v[4:7]));m.update(type=v[2],capture=v[7],scan=v[8],token=v[9],request_us=v[10],start_us=v[11],end_us=v[12],counts=tuple(v[13:19]),valid_mask=mask,words=words)
 if m['type'] in (SCAN,BODY_SCAN):
  if not m['scan'] or not m['token'] or not m['start_us']<m['end_us']:raise ValueError('scan clock/identity')
  if m['type']==SCAN and m['start_us']<m['request_us']:raise ValueError('scan request clock')
  if any(bool(mask&(1<<i))!=(w<0x4000) for i,w in enumerate(words)):raise ValueError('word validity disagreement')
 return m


class Stream:
 def __init__(self):self.buffer=bytearray()
 def feed(self,data):
  if len(self.buffer)+len(data)>BYTES*64:raise ValueError('stream bound')
  self.buffer.extend(data);out=[]
  while len(self.buffer)>=BYTES:
   if self.buffer[:4]!=MAGIC:raise ValueError('serial lost framing; reconnect')
   raw=bytes(self.buffer[:BYTES]);del self.buffer[:BYTES];out.append(decode(raw))
  return out

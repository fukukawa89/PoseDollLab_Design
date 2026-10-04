"""Strict PDG5/1 USB codec. No PD41 cache or timestamp reinterpretation."""
import struct,zlib
SIZE=220
PROBE,HELLO,REQUEST,ACCEPTED,SCAN,CANCEL,ERROR,STOP=range(1,9)
FULL_MASK=((1<<44)-1)&~7

def encode(m):
    b=bytearray(SIZE);struct.pack_into('<4sBBHQQ16sQQQQ',b,0,b'PDG5',1,m['type'],SIZE,m.get('device',0),m.get('boot',0),m.get('capture',bytes(16)),m.get('scan',0),m.get('request_us',0),m.get('start_us',0),m.get('end_us',0))
    struct.pack_into('<6Q',b,72,*m.get('source_boot',[0]*6));struct.pack_into('<44H',b,120,*m.get('words',[0]*44));struct.pack_into('<Q',b,208,m.get('physical_mask',0));struct.pack_into('<I',b,216,zlib.crc32(b[:216]));return bytes(b)

def decode(b):
    if len(b)!=SIZE or b[:4]!=b'PDG5' or b[4]!=1 or not 1<=b[5]<=8 or struct.unpack_from('<H',b,6)[0]!=SIZE or struct.unpack_from('<I',b,216)[0]!=zlib.crc32(b[:216]):raise ValueError('PDG5 CRC/version/length')
    device,boot,capture,scan,req,start,end=struct.unpack_from('<QQ16sQQQQ',b,8)
    mask=struct.unpack_from('<Q',b,208)[0]
    if mask&~FULL_MASK:raise ValueError('PDG5 invalid physical mask')
    return dict(type=b[5],device=device,boot=boot,capture=capture,scan=scan,request_us=req,start_us=start,end_us=end,source_boot=list(struct.unpack_from('<6Q',b,72)),words=list(struct.unpack_from('<44H',b,120)),physical_mask=mask)

class Stream:
    def __init__(self):self.buffer=bytearray();self.since=None
    def feed(self,data,now):
        if self.buffer and now-self.since>.5:raise ValueError('PDG5 partial frame timeout')
        if len(self.buffer)+len(data)>SIZE*32:raise ValueError('PDG5 receive budget')
        if not self.buffer:self.since=now
        self.buffer.extend(data);out=[]
        while len(self.buffer)>=SIZE:
            out.append(decode(self.buffer[:SIZE]));del self.buffer[:SIZE]
            self.since=now
        if self.buffer and self.buffer[:min(4,len(self.buffer))]!=b'PDG5'[:min(4,len(self.buffer))]:raise ValueError('PDG5 frame sync')
        return out

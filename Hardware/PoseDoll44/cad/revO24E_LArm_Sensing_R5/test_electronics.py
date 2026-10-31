from common import *
import arm_reader as r
import struct,zlib,random

def tm(data):
    w=(data&65535)<<8;return w|r.crc4(w)

def run():
    checks=[]
    assert r.crc4(0x0f000400)==7;checks.append('TI published CRC4 command vector 0F000407')
    for _ in range(1000):
        d=random.randrange(1<<18);w=(d<<6)|r.crc6(d)
        assert r.crc6(w>>6)==w&63
        for bit in range(24):assert r.crc6((w^(1<<bit))>>6)!=((w^(1<<bit))&63)
    checks.append('MT CRC6 rejects all single-bit errors in 1000 24-bit frames')
    t=[tm(1000),tm(-2000),tm(3000),tm(0x2710),tm(0x2710),tm(0),tm(0x300),tm(0x3130)]
    assert r.tm_valid(t)
    for j in range(8):
        for b in range(32):
            bad=t.copy();bad[j]^=1<<b;assert not r.tm_valid(bad)
    for pos,val in [(4,0x2720),(3,0x0710),(5,0x8000),(5,0x100),(6,0x1000),(7,0),(0,32760)]:
        bad=t.copy();bad[pos]=tm(val);assert not r.tm_valid(bad)
    checks.append('TMAG CRC, reset, stale/mixed conversions, configuration and saturation rejection')
    b=bytearray(r.command(r.SCAN));struct.pack_into('<II',b,48,1,2);struct.pack_into('<QQQ',b,56,10,20,10000);struct.pack_into('<Q',b,88,r.REQUIRED);struct.pack_into('<Q',b,236,r.REQUIRED)
    for i in range(46):b[96+3*i:99+3*i]=(0xffffff).to_bytes(3,'little')
    for i in r.CHANNELS.values():
        x=1234<<4;w=(x<<6)|r.crc6(x);b[96+3*i:99+3*i]=w.to_bytes(3,'little')
    struct.pack_into('<8I',b,244,*t);struct.pack_into('<I',b,276,zlib.crc32(b[:276]));f=r.decode(b);assert all(x['valid'] for x in f['channels'].values());assert f['channels']['WD']['field_mT'][1]<0
    for bit in range(len(b)*8):
        bb=bytearray(b);bb[bit//8]^=1<<(bit%8)
        try:r.decode(bb)
        except ValueError:pass
        else:raise AssertionError(bit)
    checks.append('280-byte R5AR packet: every single-bit corruption rejected; signed fields correct')
    cal=dict(direction_verified=True,range_verified=True,coupled_wrist_verified=True,forward_reverse_verified=True,max_residual_mT=.2,lut=[[q,20,q*.8,q*.15] for q in range(-20,31,5)])
    assert abs(r.vector_angle([20,7*.8,7*.15],cal)-7)<1e-9
    try:r.vector_angle([100,0,0],cal)
    except ValueError:pass
    else:raise AssertionError('off-curve accepted')
    cal['coupled_wrist_verified']=False
    try:r.vector_angle([20,0,0],cal)
    except ValueError:pass
    else:raise AssertionError('unmeasured calibration accepted')
    checks.append('Vector LUT interpolation, off-curve rejection and missing physical calibration gate')
    cal['coupled_wrist_verified']=True
    mc=dict(reference_raw_deg=30,reference_joint_deg=-45,sign=1,limits_deg=[-45,165],direction_verified=True,range_verified=True,correction_lut=[[-45,0],[168,-3]])
    calibration=dict(channels={k:dict(mc) for k in r.CHANNELS});calibration['channels']['WD']=cal
    ff=dict(channels={k:dict(valid=True,raw_deg=243) for k in r.CHANNELS});ff['channels']['WD']=dict(valid=True,field_mT=[20,0,0])
    assert all(abs(v-165)<1e-9 for k,v in r.angles(ff,calibration).items() if k!='WD')
    checks.append('MT >180-degree range unwrap and distorted endpoint correction use raw LUT bounds')
    put(OUT/'verification/electronics_tests.json',dict(passed=True,checks=checks,hardware_connected=False,hardware_waveforms_verified=False));print('ELECTRONICS TESTS PASS',len(checks),flush=True)

if __name__=='__main__':run()

"""Write O21 SSI/USB reference implementation; old P17 firmware is not reused at run time."""
from build_revo21 import *
def text(path,s):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(s.strip()+'\n',encoding='utf-8')
def main():
    F=B/'firmware_source'
    for f in ['session.c','session.h','test_session.c','CMakeLists.txt','main/main.c','main/CMakeLists.txt','sdkconfig.defaults','build.ps1']:
        s=(OLD/'firmware_source'/f).read_text(encoding='utf-8-sig').replace('p17','p21').replace('P17','P21').replace('O17','O21').replace('o17','o21')
        if f=='main/main.c':
            s=s[s.index('#include'):];s='/* O21 prototype only. New SSI carrier required; never flash onto O20 wiring. */\n'+s
        if f=='session.c':s=s.replace('s->current.valid_mask=0;','s->current.valid_mask=0;s->current.idle_high_mask=0;')
        if f=='test_session.c':
            s=s.replace('out.valid_mask=P21_MASK;', 'out.valid_mask=P21_MASK;out.idle_high_mask=P21_MASK;')
            s=s.replace('out.words[i]=(uint16_t)i;', 'out.words[i]=(i<<10)|p21_crc6(i<<4);')
            s=s.replace('out.words[i]=2;', 'out.words[i]=(2u<<10)|p21_crc6(2u<<4);')
        text(F/f,s)
    text(F/'raw46.h',r'''
#ifndef P21_RAW46_H
#define P21_RAW46_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
enum { P21_BYTES=248, P21_AXES=46,
 P21_PROBE=0,P21_HELLO,P21_REQUEST,P21_ACCEPTED,P21_SCAN,P21_CANCEL,P21_STOP,P21_ERROR };
#define P21_MASK ((UINT64_C(1)<<46)-1)
#define P21_FAULT UINT32_C(0xffffff)
typedef struct {
 uint8_t type,capture[16];
 uint64_t device,transport_boot,body_boot,request_us,start_us,end_us,valid_mask,idle_high_mask;
 uint32_t scan,token,words[46];
} p21_message;
uint8_t p21_crc6(uint32_t data18);
bool p21_sensor_valid(uint32_t word,bool idle_high);
uint32_t p21_crc(const uint8_t*p,size_t n);
bool p21_encode(const p21_message*m,uint8_t out[P21_BYTES]);
bool p21_decode(const uint8_t*p,size_t n,p21_message*out);
#endif
''')
    text(F/'raw46.c',r'''
#include "raw46.h"
#include <string.h>
static const uint8_t layout[6]={14,16,16,0,0,0};
static uint64_t get(const uint8_t*p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
static void put(uint8_t*p,uint64_t v,unsigned n){for(unsigned i=0;i<n;i++)p[i]=(uint8_t)(v>>(8*i));}
uint8_t p21_crc6(uint32_t d){
 uint8_t c=0;
 for(int i=17;i>=0;i--){unsigned fb=((unsigned)c>>5)^((d>>(unsigned)i)&1u);c=(uint8_t)((c<<1)&63u);if(fb)c^=3u;}
 return c;
}
bool p21_sensor_valid(uint32_t w,bool idle){
 return idle&&w<=0xffffffu&&((w>>6)&15u)==0&&p21_crc6(w>>6)==(w&63u);
}
uint32_t p21_crc(const uint8_t*p,size_t n){uint32_t c=UINT32_MAX;for(size_t i=0;i<n;i++){c^=p[i];for(unsigned j=0;j<8;j++)c=(c>>1)^((0u-(c&1u))&UINT32_C(0xedb88320));}return ~c;}
static bool valid(const p21_message*m){
 if(m->type>P21_ERROR||((m->valid_mask|m->idle_high_mask)&~P21_MASK))return false;
 for(unsigned i=0;i<46;i++)if(m->words[i]>0xffffffu)return false;
 if(m->type==P21_SCAN){
  if(!m->scan||!m->token||m->start_us<m->request_us||m->end_us<=m->start_us||m->end_us-m->start_us>60000)return false;
  for(unsigned i=0;i<46;i++)if(((m->valid_mask>>i)&1u)!=(unsigned)p21_sensor_valid(m->words[i],((m->idle_high_mask>>i)&1u)!=0))return false;
 }
 return true;
}
bool p21_encode(const p21_message*m,uint8_t out[P21_BYTES]){
 if(!m||!out||!valid(m))return false;
 memset(out,0,P21_BYTES);memcpy(out,"P21R",4);out[4]=1;out[5]=m->type;
 put(out+8,m->device,8);put(out+16,m->transport_boot,8);put(out+24,m->body_boot,8);memcpy(out+32,m->capture,16);
 put(out+48,m->scan,4);put(out+52,m->token,4);put(out+56,m->request_us,8);put(out+64,m->start_us,8);put(out+72,m->end_us,8);
 memcpy(out+80,layout,6);put(out+88,m->valid_mask,8);
 for(unsigned i=0;i<46;i++)put(out+96+3*i,m->words[i],3);
 put(out+236,m->idle_high_mask,8);put(out+244,p21_crc(out,244),4);return true;
}
bool p21_decode(const uint8_t*p,size_t n,p21_message*out){
 if(!p||!out||n!=P21_BYTES||memcmp(p,"P21R",4)||p[4]!=1||p[5]>P21_ERROR||p[6]||p[7]||p[86]||p[87]||p[234]||p[235]||memcmp(p+80,layout,6)||get(p+244,4)!=p21_crc(p,244))return false;
 p21_message m={0};m.type=p[5];m.device=get(p+8,8);m.transport_boot=get(p+16,8);m.body_boot=get(p+24,8);memcpy(m.capture,p+32,16);
 m.scan=(uint32_t)get(p+48,4);m.token=(uint32_t)get(p+52,4);m.request_us=get(p+56,8);m.start_us=get(p+64,8);m.end_us=get(p+72,8);m.valid_mask=get(p+88,8);m.idle_high_mask=get(p+236,8);
 for(unsigned i=0;i<46;i++)m.words[i]=(uint32_t)get(p+96+3*i,3);
 if(!valid(&m))return false;
 *out=m;return true;
}
''')
    wiring=read(B/'profiles/wiring.json')
    maps=[[n['raw_index'] for n in g['nodes']]+[-1]*(16-g['count']) for g in wiring['banks']]
    mapc=',\n'.join('{'+','.join(map(str,a))+'}' for a in maps)
    text(F/'main/scanner.inc',r'''
/* SSI candidate: Mode-1 style bit sampling, validated in software only.
 * Mainboard buffers CLK/CSN separately per bank. DO pins never connect together.
 * All sensors in a bank receive CSN/CLK; mux selects only which DO we observe.
 * The CTS timing/CRC and idle-high behavior need a real waveform qualification.
 */
static const int addr[4]={2,4,5,6},din[3]={8,9,44};
static const int clk=7,csn=43,en=1;
static const int raw_index[3][16]={
'''+mapc+r'''
};
static void sensor_setup(void){
 uint64_t mask=(UINT64_C(1)<<en)|(UINT64_C(1)<<clk)|(UINT64_C(1)<<csn);
 for(unsigned i=0;i<4;i++)mask|=UINT64_C(1)<<addr[i];
 gpio_config_t c={.pin_bit_mask=mask,.mode=GPIO_MODE_OUTPUT};ESP_ERROR_CHECK(gpio_config(&c));
 gpio_set_level(en,0);gpio_set_level(csn,1);gpio_set_level(clk,0);
 for(unsigned i=0;i<4;i++)gpio_set_level(addr[i],0);
 c.pin_bit_mask=(UINT64_C(1)<<8)|(UINT64_C(1)<<9)|(UINT64_C(1)<<44);c.mode=GPIO_MODE_INPUT;c.pull_up_en=GPIO_PULLUP_DISABLE;c.pull_down_en=GPIO_PULLDOWN_DISABLE;
 ESP_ERROR_CHECK(gpio_config(&c));
 vTaskDelay(pdMS_TO_TICKS(100));gpio_set_level(en,1);
}
static void fresh_scan(p21_message*m){
 m->valid_mask=0;m->idle_high_mask=0;
 for(unsigned i=0;i<46;i++)m->words[i]=P21_FAULT;
 for(unsigned slot=0;slot<16;slot++){
  gpio_set_level(csn,1);gpio_set_level(clk,0);
  for(unsigned a=0;a<4;a++)gpio_set_level(addr[a],(int)((slot>>a)&1u));
  esp_rom_delay_us(20);
  bool idle[3];for(unsigned b=0;b<3;b++)idle[b]=gpio_get_level(din[b])!=0;
  uint32_t w[3]={0,0,0};gpio_set_level(csn,0);esp_rom_delay_us(20);
  for(unsigned bit=0;bit<24;bit++){
   gpio_set_level(clk,1);esp_rom_delay_us(20);
   for(unsigned b=0;b<3;b++)w[b]=(w[b]<<1)|(uint32_t)gpio_get_level(din[b]);
   gpio_set_level(clk,0);esp_rom_delay_us(20);
  }
  gpio_set_level(csn,1);esp_rom_delay_us(20);
  for(unsigned b=0;b<3;b++){
   int i=raw_index[b][slot];if(i<0)continue;
   m->words[i]=w[b];
   if(idle[b])m->idle_high_mask|=UINT64_C(1)<<i;
   if(p21_sensor_valid(w[b],idle[b]))m->valid_mask|=UINT64_C(1)<<i;
  }
 }
}
''')
    text(F/'test_raw46.c',r'''
#include "raw46.h"
#include <assert.h>
#include <stdio.h>
/* Independent polynomial long division, not the streaming implementation. */
static uint8_t reference(uint32_t d){uint32_t x=d<<6;for(int i=23;i>=6;i--)if(x&(1u<<i))x^=0x43u<<(i-6);return (uint8_t)(x&63u);}
int main(void){
 for(uint32_t d=0;d<(1u<<18);d++)assert(p21_crc6(d)==reference(d));
 for(uint32_t a=0;a<16384;a++){
  uint32_t w=(a<<10)|reference(a<<4);
  assert(p21_sensor_valid(w,true));assert(!p21_sensor_valid(w,false));
  for(unsigned bit=0;bit<24;bit++)assert(!p21_sensor_valid(w^(1u<<bit),true));
  for(unsigned status=1;status<16;status++){uint32_t d=(a<<4)|status;assert(!p21_sensor_valid((d<<6)|reference(d),true));}
 }
 p21_message m={.type=P21_SCAN,.device=123,.transport_boot=456,.body_boot=456,.request_us=100,.start_us=101,.end_us=16000,.scan=1,.token=1,.valid_mask=P21_MASK,.idle_high_mask=P21_MASK},out;
 m.capture[0]=1;
 for(unsigned i=0;i<46;i++)m.words[i]=((i*307u)<<10)|reference(i*307u<<4);
 uint8_t bytes[P21_BYTES];assert(p21_encode(&m,bytes));assert(p21_decode(bytes,sizeof bytes,&out));assert(out.words[45]==m.words[45]);
 for(unsigned bit=0;bit<P21_BYTES*8;bit++){bytes[bit/8]^=(uint8_t)(1u<<(bit%8));assert(!p21_decode(bytes,sizeof bytes,&out));bytes[bit/8]^=(uint8_t)(1u<<(bit%8));}
 for(unsigned n=0;n<P21_BYTES;n++)assert(!p21_decode(bytes,n,&out));
 FILE*f=NULL;if(fopen_s(&f,"codec_fixture.bin","wb"))return 2;assert(fwrite(bytes,1,sizeof bytes,f)==sizeof bytes);fclose(f);
 m.valid_mask^=1;assert(!p21_encode(&m,bytes));
 m.valid_mask=P21_MASK;m.words[0]=0x1000000;assert(!p21_encode(&m,bytes));
 puts("P21 PASS: 262144 independent CRC comparisons; all 16384 angles, 393216 single-bit SSI corruptions, all 15 status codes, 1984 USB bit flips, truncations, masks.");
 return 0;
}
''')
    text(B/'source/mt6701.py',r'''
"""MT6701 24-bit SSI codec; mathematical tests do not certify physical wiring."""
def crc6(data):
    if type(data) is not int or not 0<=data<(1<<18):raise ValueError('18-bit payload')
    c=0
    for bit in range(17,-1,-1):
        feedback=(c>>5)^((data>>bit)&1);c=(c<<1)&63
        if feedback:c^=3
    return c
def decode_word(word,idle_high):
    if type(word) is not int or not 0<=word<=0xffffff:raise ValueError('SSI width')
    status=(word>>6)&15
    good=idle_high is True and status==0 and crc6(word>>6)==(word&63)
    return {'word':word,'counts':word>>10,'status':status,'crc_ok':crc6(word>>6)==(word&63),'idle_high':idle_high,'valid':good}
''')
    usb=(OLD/'source/usb_capture.py').read_text(encoding='utf-8-sig')
    usb=usb.replace('P17R','P21R').replace('POSEDOLL-O17','POSEDOLL-O21').replace('SIZE=192;COUNTS=bytes([6,4,10,10,8,8])','SIZE=248;COUNTS=bytes([14,16,16,0,0,0])')
    usb=usb.replace('from device import capture_window','from measurement import capture_window\nfrom mt6701 import decode_word')
    usb=usb.replace('(6,7,86,87)','(6,7,86,87,234,235)').replace('data[:188]','data[:244]').replace('data,188','data,244').replace('d[:188]','d[:244]').replace('d,188','d,244')
    usb=usb.replace("words=list(struct.unpack_from('<46H',data,96))","words=[int.from_bytes(data[96+3*i:99+3*i],'little') for i in range(46)];idle=struct.unpack_from('<Q',data,236)[0]")
    usb=usb.replace("if mask&~MASK:", "if (mask|idle)&~MASK:")
    usb=usb.replace("bool(mask&(1<<i))!=(v<0x4000)","bool(mask&(1<<i))!=decode_word(v,bool(idle&(1<<i)))['valid']")
    usb=usb.replace("valid_mask=mask,words=words)","valid_mask=mask,idle_high_mask=idle,words=words)")
    usb=usb.replace("'sensor_deg':v*360/16384","'sensor_deg':(v>>10)*360/16384")
    text(B/'source/usb_capture.py',usb)
    p=read(B/'profiles/device_profile.json')
    for name in ['mt6701_ssi_waveform','mt6701_crc_known_angle','mt6701_magnetic_gap','mt6701_accuracy_full_range','new_harness_adjacent_clearance']:
        if name not in p['required_physical_measurement_tests']:p['required_physical_measurement_tests'].append(name)
    put(B/'profiles/device_profile.json',p)
    text(R/'scripts/Run-RevO21-CodecTests.cmd',r'''
@echo off
setlocal
set "PD_O21_OUT=%~1"
if not defined PD_O21_OUT exit /b 2
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%~dp0.."
if not exist "%PD_O21_OUT%" mkdir "%PD_O21_OUT%"
set "PD_O21_SRC=Hardware\PoseDoll44\bench\revO21\firmware_source"
cl /nologo /std:c11 /W4 /WX /O2 /I "%PD_O21_SRC%" "%PD_O21_SRC%\raw46.c" "%PD_O21_SRC%\test_raw46.c" /Fo:"%PD_O21_OUT%\\" /Fe:"%PD_O21_OUT%\codec_test.exe"
if errorlevel 1 exit /b 1
pushd "%PD_O21_OUT%"
codec_test.exe
if errorlevel 1 exit /b 1
popd
cl /nologo /std:c11 /W4 /WX /O2 /I "%PD_O21_SRC%" "%PD_O21_SRC%\raw46.c" "%PD_O21_SRC%\session.c" "%PD_O21_SRC%\test_session.c" /Fo:"%PD_O21_OUT%\\" /Fe:"%PD_O21_OUT%\session_test.exe"
if errorlevel 1 exit /b 1
"%PD_O21_OUT%\session_test.exe"
exit /b %errorlevel%
''')
    print('O21 firmware and host source written')
if __name__=='__main__':main()

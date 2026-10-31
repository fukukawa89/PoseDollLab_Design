/* Raw46 candidate codec. No OTP writes. Declared length is not physical identity. */
#include "raw46.h"
#include <string.h>
const uint8_t p15_counts[6]={6,4,10,10,8,8};
const uint16_t p15_registers[5]={0x3ffd,0x3ffe,0x3fff,0x0016,0x0017};
static uint64_t get(const uint8_t*p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
static void put(uint8_t*p,uint64_t v,unsigned n){for(unsigned i=0;i<n;i++)p[i]=(uint8_t)(v>>(8*i));}
uint32_t p15_crc(const uint8_t*p,size_t n){uint32_t c=UINT32_MAX;for(size_t i=0;i<n;i++){c^=p[i];for(unsigned j=0;j<8;j++)c=(c>>1)^((0u-(c&1u))&UINT32_C(0xedb88320));}return ~c;}
static bool valid(const p15_message*m){
 if(m->type>P15_BODY_SCAN||(m->valid_mask&~P15_MASK))return false;
 if(m->type==P15_SCAN||m->type==P15_BODY_SCAN){
  if(!m->scan||!m->token||m->end_us<=m->start_us)return false;
  if(m->type==P15_SCAN&&m->start_us<m->request_us)return false;
  for(unsigned i=0;i<46;i++)if(((m->valid_mask>>i)&1u)!=(unsigned)(m->words[i]<0x4000))return false;
 }
 return true;
}
bool p15_encode(const p15_message*m,uint8_t out[192]){
 if(!m||!out||!valid(m))return false;
 memset(out,0,192);memcpy(out,"P15R",4);out[4]=1;out[5]=m->type;
 put(out+8,m->device,8);put(out+16,m->gateway_boot,8);put(out+24,m->body_boot,8);memcpy(out+32,m->capture,16);
 put(out+48,m->scan,4);put(out+52,m->token,4);put(out+56,m->request_us,8);put(out+64,m->start_us,8);put(out+72,m->end_us,8);memcpy(out+80,p15_counts,6);put(out+88,m->valid_mask,8);
 for(unsigned i=0;i<46;i++)put(out+96+2*i,m->words[i],2);
 put(out+188,p15_crc(out,188),4);return true;
}
bool p15_decode(const uint8_t*p,size_t n,p15_message*out){
 if(!p||!out||n!=192||memcmp(p,"P15R",4)||p[4]!=1||p[5]>P15_BODY_SCAN||p[6]||p[7]||p[86]||p[87]||memcmp(p+80,p15_counts,6)||get(p+188,4)!=p15_crc(p,188))return false;
 p15_message m={0};m.type=p[5];m.device=get(p+8,8);m.gateway_boot=get(p+16,8);m.body_boot=get(p+24,8);memcpy(m.capture,p+32,16);
 m.scan=(uint32_t)get(p+48,4);m.token=(uint32_t)get(p+52,4);m.request_us=get(p+56,8);m.start_us=get(p+64,8);m.end_us=get(p+72,8);m.valid_mask=get(p+88,8);
 for(unsigned i=0;i<46;i++)m.words[i]=(uint16_t)get(p+96+2*i,2);
 if(!valid(&m))return false;
 *out=m;return true;
}
static bool even(uint16_t v){unsigned p=0;for(unsigned i=0;i<16;i++)p^=(v>>i)&1u;return !p;}
uint16_t p15_command(uint16_t address){uint16_t v=(uint16_t)(0x4000u|(address&0x3fffu));return (uint16_t)(v|(even(v)?0:0x8000));}
bool p15_decode_chain(const uint16_t rx[6][10],unsigned count,uint16_t*out){
 if(!rx||!out||count<1||count>10)return false;
 bool ok=true;
 for(unsigned i=0;i<count;i++){
  unsigned wire=count-1-i;uint16_t w[5],flags=0;
  for(unsigned j=0;j<5;j++){uint16_t v=rx[j+1][wire];if(!even(v))flags|=1;if(v&0x4000)flags|=2;w[j]=v&0x3fff;}
  if(!(w[0]&0x100)||(w[0]&0xe00))flags|=4;
  if(((w[3]&255)<<6)|(w[4]&63))flags|=8;
  out[i]=flags?(uint16_t)(P15_FAULT|flags):w[2];if(flags)ok=false;
 }
 return ok;
}

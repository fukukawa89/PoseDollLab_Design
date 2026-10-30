#include "raw46.h"
#include <string.h>
static const uint8_t layout[6]={6,3,1,0,0,0};
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
 memset(out,0,P21_BYTES);memcpy(out,"R5AR",4);out[4]=1;out[5]=m->type;
 put(out+8,m->device,8);put(out+16,m->transport_boot,8);put(out+24,m->body_boot,8);memcpy(out+32,m->capture,16);
 put(out+48,m->scan,4);put(out+52,m->token,4);put(out+56,m->request_us,8);put(out+64,m->start_us,8);put(out+72,m->end_us,8);
 memcpy(out+80,layout,6);put(out+88,m->valid_mask,8);
 for(unsigned i=0;i<46;i++)put(out+96+3*i,m->words[i],3);
 put(out+236,m->idle_high_mask,8);for(unsigned j=0;j<8;j++)put(out+244+4*j,m->tm[j],4);put(out+276,p21_crc(out,276),4);return true;
}
bool p21_decode(const uint8_t*p,size_t n,p21_message*out){
 if(!p||!out||n!=P21_BYTES||memcmp(p,"R5AR",4)||p[4]!=1||p[5]>P21_ERROR||p[6]||p[7]||p[86]||p[87]||p[234]||p[235]||memcmp(p+80,layout,6)||get(p+276,4)!=p21_crc(p,276))return false;
 p21_message m={0};m.type=p[5];m.device=get(p+8,8);m.transport_boot=get(p+16,8);m.body_boot=get(p+24,8);memcpy(m.capture,p+32,16);
 m.scan=(uint32_t)get(p+48,4);m.token=(uint32_t)get(p+52,4);m.request_us=get(p+56,8);m.start_us=get(p+64,8);m.end_us=get(p+72,8);m.valid_mask=get(p+88,8);m.idle_high_mask=get(p+236,8);
 for(unsigned i=0;i<46;i++)m.words[i]=(uint32_t)get(p+96+3*i,3);
 for(unsigned j=0;j<8;j++)m.tm[j]=(uint32_t)get(p+244+4*j,4);
 if(!valid(&m))return false;
 *out=m;return true;
}

uint8_t r5_crc4(uint32_t w){
 uint8_t c=15;w&=0xfffffff0u;
 for(int b=31;b>=0;b--){unsigned f=((c>>3)^((w>>b)&1u))&1u;c=(c<<1)&15u;if(f)c^=3u;}
 return c;
}
bool r5_tm_crc_ok(uint32_t w){return w!=0&&w!=UINT32_MAX&&r5_crc4(w)==(w&15u);}
uint16_t r5_tm_data(uint32_t w){return (uint16_t)(w>>8);}
bool r5_tm_valid(const uint32_t *t){
 for(unsigned j=0;j<8;j++)if(!r5_tm_crc_ok(t[j])||(t[j]&0xc0000080u))return false;
 uint16_t pre=r5_tm_data(t[3]),post=r5_tm_data(t[4]);
 if((pre&0x2700)!=0x2700||(post&0x2700)!=0x2700||((pre^post)&0x70))return false;
 if(r5_tm_data(t[5])&0x9f03)return false;
 if(r5_tm_data(t[6])&0x783f)return false;
 if(r5_tm_data(t[7])!=0x3130)return false;
 for(unsigned j=0;j<3;j++){int v=(int16_t)r5_tm_data(t[j]);if(v>31129||v< -31129)return false;}
 return true;
}

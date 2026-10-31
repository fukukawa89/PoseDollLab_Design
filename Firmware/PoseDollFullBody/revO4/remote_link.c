#include "remote_link.h"
#include <string.h>
static void put(uint8_t*p,uint64_t v,unsigned n){for(unsigned i=0;i<n;i++){p[i]=(uint8_t)v;v>>=8;}}
static uint64_t get(const uint8_t*p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
static uint32_t crc(const uint8_t*p,size_t n){uint32_t v=0xffffffffu;for(size_t i=0;i<n;i++){v^=p[i];for(unsigned j=0;j<8;j++)v=(v>>1)^(0xedb88320u&((uint32_t)0-(v&1)));}return ~v;}
static int nonzero(const uint8_t*p){uint8_t v=0;for(unsigned i=0;i<16;i++)v|=p[i];return v!=0;}
size_t pdr4_encode(const pdr4_message*m,uint8_t*out,size_t cap){
 if(!m||!out||(m->type!=PDR4_REQUEST&&m->type!=PDR4_RESPONSE)||!m->scan||!m->generation||!m->capture_counter||!nonzero(m->link_nonce)||!nonzero(m->capture))return 0;
 const size_t n=m->type==PDR4_REQUEST?PDR4_REQUEST_BYTES:PDR4_RESPONSE_BYTES;if(cap<n)return 0;
 memset(out,0,n);memcpy(out,"PDR4",4);out[4]=1;out[5]=m->type;put(out+6,n-PDR4_HEADER-4,2);memcpy(out+8,m->link_nonce,16);memcpy(out+24,m->capture,16);put(out+40,m->scan,8);put(out+48,m->generation,8);put(out+56,m->capture_counter,8);
 if(m->type==PDR4_RESPONSE){if(!m->duration_us)return 0;put(out+64,m->duration_us,4);for(unsigned i=0;i<4;i++)put(out+68+2*i,m->words[i],2);}
 put(out+n-4,crc(out,n-4),4);return n;
}
int pdr4_decode(const uint8_t*in,size_t n,pdr4_message*out){
 if(!in||!out||(n!=PDR4_REQUEST_BYTES&&n!=PDR4_RESPONSE_BYTES)||memcmp(in,"PDR4",4)||in[4]!=1||get(in+6,2)!=n-PDR4_HEADER-4||get(in+n-4,4)!=crc(in,n-4))return 0;
 if((in[5]==PDR4_REQUEST&&n!=PDR4_REQUEST_BYTES)||(in[5]==PDR4_RESPONSE&&n!=PDR4_RESPONSE_BYTES)||(in[5]!=PDR4_REQUEST&&in[5]!=PDR4_RESPONSE))return 0;
 pdr4_message m;memset(&m,0,sizeof m);m.type=in[5];memcpy(m.link_nonce,in+8,16);memcpy(m.capture,in+24,16);m.scan=get(in+40,8);m.generation=get(in+48,8);m.capture_counter=get(in+56,8);
 if(!m.scan||!m.generation||!m.capture_counter||!nonzero(m.link_nonce)||!nonzero(m.capture))return 0;
 if(m.type==PDR4_RESPONSE){m.duration_us=(uint32_t)get(in+64,4);if(!m.duration_us)return 0;for(unsigned i=0;i<4;i++)m.words[i]=(uint16_t)get(in+68+2*i,2);}
 *out=m;return 1;
}
void pdr4_reset(pdr4_session*s){memset(s,0,sizeof *s);}
int pdr4_bind(pdr4_session*s,const uint8_t nonce[16],uint64_t generation){if(!s||!nonce||!generation||!nonzero(nonce))return 0;pdr4_reset(s);s->joined=1;s->generation=generation;memcpy(s->link_nonce,nonce,16);return 1;}
int pdr4_accept_request(pdr4_session*s,const pdr4_message*m){
 if(!s||!m||!s->joined||m->type!=PDR4_REQUEST||!m->scan||m->generation!=s->generation||memcmp(m->link_nonce,s->link_nonce,16))return 0;
 if(m->capture_counter>s->capture_counter){if(m->scan!=1)return 0;memcpy(s->capture,m->capture,16);s->capture_counter=m->capture_counter;s->last_scan=0;}
 else if(m->capture_counter!=s->capture_counter||memcmp(m->capture,s->capture,16))return 0;
 if(m->scan!=s->last_scan+1)return 0;s->last_scan=m->scan;return 1;
}

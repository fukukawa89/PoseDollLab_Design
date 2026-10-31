#include "static_gateway.h"
#include <string.h>
static const unsigned counts[6]={3,6,9,9,7,7};
static const unsigned starts[6]={3,6,12,28,21,37};
static void put(uint8_t* p,uint64_t x,unsigned n){for(unsigned i=0;i<n;i++){p[i]=(uint8_t)x;x>>=8;}}
static uint64_t get(const uint8_t* p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
uint32_t pd5_crc(const uint8_t* p,size_t n){uint32_t v=0xffffffffu;for(size_t i=0;i<n;i++){v^=p[i];for(unsigned j=0;j<8;j++)v=(v>>1)^(0xedb88320u&((uint32_t)0-(v&1)));}return ~v;}
int pd5_encode_usb(const pd5_usb* m,uint8_t out[220])
{
    if(!m||!out||m->type<1||m->type>8)return 0;
    memset(out,0,220);memcpy(out,"PDG5",4);out[4]=1;out[5]=m->type;put(out+6,220,2);
    put(out+8,m->device,8);put(out+16,m->boot,8);memcpy(out+24,m->capture,16);put(out+40,m->scan,8);
    put(out+48,m->request_us,8);put(out+56,m->start_us,8);put(out+64,m->end_us,8);
    for(unsigned i=0;i<6;i++)put(out+72+8*i,m->source_boot[i],8);
    for(unsigned i=0;i<44;i++)put(out+120+2*i,m->words[i],2);
    put(out+208,m->physical_mask,8);put(out+216,pd5_crc(out,216),4);return 1;
}
int pd5_decode_usb(const uint8_t* p,size_t n,pd5_usb* m)
{
    if(!p||!m||n!=220||memcmp(p,"PDG5",4)||p[4]!=1||p[5]<1||p[5]>8||get(p+6,2)!=220||get(p+216,4)!=pd5_crc(p,216))return 0;
    memset(m,0,sizeof(*m));m->type=p[5];m->device=get(p+8,8);m->boot=get(p+16,8);memcpy(m->capture,p+24,16);m->scan=get(p+40,8);
    m->request_us=get(p+48,8);m->start_us=get(p+56,8);m->end_us=get(p+64,8);
    for(unsigned i=0;i<6;i++)m->source_boot[i]=get(p+72+8*i,8);
    for(unsigned i=0;i<44;i++)m->words[i]=(uint16_t)get(p+120+2*i,2);
    m->physical_mask=get(p+208,8);return 1;
}
int pd5_encode_request(const pd5_region_request* r,uint8_t out[28])
{
    if(!r||!out||r->node<1||r->node>6||!r->gateway_boot||!r->token||(r->operation!=PD5_PROBE&&r->operation!=PD5_REQUEST)||(r->operation==PD5_REQUEST&&!r->expected_boot))return 0;
    memset(out,0,28);out[0]=1;out[1]=r->operation;out[2]=r->node;
    put(out+4,r->gateway_boot,8);put(out+12,r->token,4);put(out+16,r->expected_boot,8);put(out+24,pd5_crc(out,24),4);return 1;
}
int pd5_decode_request(const uint8_t* p,size_t n,pd5_region_request* r)
{
    uint8_t canonical[28];if(!p||!r||n!=28||p[0]!=1||p[3]||get(p+24,4)!=pd5_crc(p,24))return 0;
    r->operation=p[1];r->node=p[2];r->gateway_boot=get(p+4,8);r->token=(uint32_t)get(p+12,4);r->expected_boot=get(p+16,8);
    return pd5_encode_request(r,canonical)&&!memcmp(canonical,p,28);
}
int pd5_encode_result(const pd5_region_result* r,uint8_t out[52])
{
    if(!r||!out||r->node<1||r->node>6||r->count!=counts[r->node-1]||!r->gateway_boot||!r->boot||!r->token||r->mask>=((unsigned)1<<r->count))return 0;
    memset(out,0,52);out[0]=1;out[1]=PD5_SCAN;out[2]=r->node;out[3]=r->count;
    put(out+4,r->gateway_boot,8);put(out+12,r->token,4);put(out+16,r->boot,8);put(out+24,r->duration_us,4);
    for(unsigned i=0;i<9;i++)put(out+28+2*i,r->words[i],2);
    put(out+46,r->mask,2);put(out+48,pd5_crc(out,48),4);return 1;
}
int pd5_decode_result(const uint8_t* p,size_t n,pd5_region_result* r)
{
    uint8_t canonical[52];if(!p||!r||n!=52||p[0]!=1||p[1]!=PD5_SCAN||get(p+48,4)!=pd5_crc(p,48))return 0;
    memset(r,0,sizeof(*r));r->node=p[2];r->count=p[3];r->gateway_boot=get(p+4,8);r->token=(uint32_t)get(p+12,4);r->boot=get(p+16,8);r->duration_us=(uint32_t)get(p+24,4);
    for(unsigned i=0;i<9;i++)r->words[i]=(uint16_t)get(p+28+2*i,2);
    r->mask=(uint16_t)get(p+46,2);return pd5_encode_result(r,canonical)&&!memcmp(canonical,p,52);
}
void pd5_blank_scan(pd5_usb* out)
{
    out->physical_mask=0;out->end_us=0;
    memset(out->source_boot,0,sizeof(out->source_boot));
    for(unsigned i=0;i<44;i++)out->words[i]=i<3?PD5_FIXED:PD5_MISSING;
}
void pd5_acquire_ports(pd5_region_result* out,unsigned ports,pd5_read_axis read,void* context)
{
    out->mask=0;for(unsigned i=0;i<9;i++)out->words[i]=PD5_MISSING;
    if(!read||ports>out->count)return;
    for(unsigned i=0;i<ports;i++){out->words[i]=read(context,i);out->mask|=(uint16_t)(1u<<i);}
}
int pd5_merge_region(pd5_usb* out,const pd5_region_result* r,const pd5_region_request* issued,uint64_t now)
{
    if(!out||!r||!issued||r->node!=issued->node||r->node<1||r->node>6||r->count!=counts[r->node-1]||r->gateway_boot!=out->boot||r->gateway_boot!=issued->gateway_boot||r->token!=issued->token||r->boot!=issued->expected_boot||!r->duration_us||r->duration_us>100000||now<=out->start_us||now-out->start_us>100000||r->duration_us>now-out->start_us||out->source_boot[r->node-1])return 0;
    if(r->mask>=((unsigned)1<<r->count))return 0;
    for(unsigned i=0;i<r->count;i++)if(!(r->mask&(1u<<i))&&r->words[i]!=PD5_MISSING)return 0;
    out->source_boot[r->node-1]=r->boot;
    for(unsigned i=0;i<r->count;i++){
        const unsigned axis=starts[r->node-1]+i;
        if(r->mask&(1u<<i)){out->words[axis]=r->words[i];out->physical_mask|=UINT64_C(1)<<axis;}

    }
    out->end_us=now;return 1;
}
void pd5_make_fragment(const uint8_t* raw,size_t total,unsigned index,uint8_t out[8])
{
    memset(out,0,8);out[0]=(uint8_t)index;for(unsigned i=0;i<7;i++){size_t at=(size_t)index*7+i;if(at<total)out[i+1]=raw[at];}
}
int pd5_fragment(pd5_fragments* s,const uint8_t p[8],size_t total,uint64_t now)
{
    if(!s||!p||!total||total>52)return -1;
    if(p[0]==0){s->next=0;s->started_us=now;memset(s->data,0,sizeof(s->data));}
    if(p[0]!=s->next||now<s->started_us||now-s->started_us>100000||(size_t)s->next*7>=total){s->next=0;return -1;}
    for(unsigned i=0;i<7;i++){size_t at=(size_t)s->next*7+i;if(at<total)s->data[at]=p[i+1];else if(p[i+1]){s->next=0;return -1;}}
    ++s->next;return (size_t)s->next*7>=total?1:0;
}

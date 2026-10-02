#include "remote_runtime.h"
#include <string.h>
void pdr5_reset(pdr5_runtime* r){if(r)memset(r,0,sizeof(*r));}
int pdr5_bind(pdr5_runtime* r,const uint8_t nonce[16],uint64_t generation,uint64_t boot)
{
    if(!r||!boot)return 0;
    pdr5_reset(r);
    if(!pdr4_bind(&r->session,nonce,generation))return 0;
    r->satellite_boot=boot;return 1;
}
static int fresh(pdr5_runtime* r,uint64_t now)
{
    if(now<r->dispatched_us||now-r->dispatched_us>100000){r->phase=PDR5_FAULT;return 0;}
    return 1;
}
int pdr5_request(pdr5_runtime* r,const uint8_t* frame,size_t bytes,uint64_t now)
{
    pdr4_message m;
    if(!r||!r->satellite_boot||bytes!=PDR4_REQUEST_BYTES||!pdr4_decode(frame,bytes,&m)||m.type!=PDR4_REQUEST)return PDR5_REJECT;
    if(m.generation!=r->session.generation||memcmp(m.link_nonce,r->session.link_nonce,16))return PDR5_REJECT;
    if(r->phase!=PDR5_IDLE){
        if(now<r->dispatched_us)r->phase=PDR5_FAULT;
        if(!memcmp(frame,r->request,PDR4_REQUEST_BYTES)){
            (void)fresh(r,now); /* Deadline applies to replaying this scan, not the next 10 Hz scan. */
            if(r->phase==PDR5_ACQUIRING)return PDR5_WAIT;
            if(r->phase==PDR5_READY)return PDR5_REPLAY;
            return PDR5_REJECT;
        }
        if(r->phase==PDR5_ACQUIRING){
            if(fresh(r,now))return PDR5_REJECT;
        }
        if(r->phase==PDR5_FAULT&&m.capture_counter<=r->session.capture_counter)return PDR5_REJECT;
    }
    if(!pdr4_accept_request(&r->session,&m))return PDR5_REJECT;
    memcpy(r->request,frame,bytes);memset(r->response,0,sizeof(r->response));
    r->dispatched_us=now;r->measured_start_us=r->measured_end_us=0;r->phase=PDR5_ACQUIRING;
    return PDR5_START;
}
int pdr5_complete(pdr5_runtime* r,const uint16_t words[4],uint64_t start,uint64_t end)
{
    pdr4_message m;
    if(!r||!words||r->phase!=PDR5_ACQUIRING||start<r->dispatched_us||end<=start||!fresh(r,end))return 0;
    if(!pdr4_decode(r->request,sizeof(r->request),&m))return 0;
    m.type=PDR4_RESPONSE;m.duration_us=(uint32_t)(end-start);memcpy(m.words,words,sizeof(m.words));
    if(pdr4_encode(&m,r->response,sizeof(r->response))!=PDR4_RESPONSE_BYTES)return 0;
    r->measured_start_us=start;r->measured_end_us=end;r->phase=PDR5_READY;return 1;
}
const uint8_t* pdr5_reply(pdr5_runtime* r,uint64_t now)
{
    if(!r||r->phase!=PDR5_READY||!fresh(r,now)||now<r->measured_end_us)return NULL;
    return r->response;
}

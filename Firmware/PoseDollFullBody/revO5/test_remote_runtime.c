#include "remote_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
    pdr5_runtime r;uint8_t req[68],other[68],reply[80];uint16_t words[4]={1,2,0x8004,16383};
    pdr4_message m={0},decoded={0};m.type=PDR4_REQUEST;m.link_nonce[0]=1;m.capture[0]=2;m.generation=1;m.capture_counter=1;m.scan=1;
    assert(pdr4_encode(&m,req,sizeof req)==68);pdr5_reset(&r);
    assert(pdr5_request(&r,req,68,1000)==PDR5_REJECT);
    assert(pdr5_bind(&r,m.link_nonce,1,77));
    /* A lost request executes only when the first complete retry arrives. */
    assert(pdr5_request(&r,req,67,1000)==PDR5_REJECT);
    assert(pdr5_request(&r,req,68,2000)==PDR5_START);
    assert(pdr5_request(&r,req,68,3000)==PDR5_WAIT);
    assert(pdr5_complete(&r,words,2100,4000));
    memcpy(reply,pdr5_reply(&r,4100),80);
    assert(pdr5_request(&r,req,68,5000)==PDR5_REPLAY);
    assert(pdr5_request(&r,req,68,6000)==PDR5_REPLAY);
    assert(!memcmp(reply,pdr5_reply(&r,6000),80));
    assert(r.measured_start_us==2100&&r.measured_end_us==4000);
    assert(pdr4_decode(reply,80,&decoded)&&decoded.duration_us==1900&&decoded.words[2]==0x8004);
    m.capture[1]=3;assert(pdr4_encode(&m,other,68)==68);
    assert(pdr5_request(&r,other,68,7000)==PDR5_REJECT); /* same counter/scan, different content */
    m.capture[1]=0;
    assert(pdr5_request(&r,req,68,102001)==PDR5_REJECT);assert(!pdr5_reply(&r,102001));
    m.scan=2;pdr4_encode(&m,other,68);assert(pdr5_request(&r,other,68,102002)==PDR5_REJECT);
    m.capture_counter=2;m.capture[0]=4;m.scan=1;pdr4_encode(&m,other,68);
    assert(pdr5_request(&r,other,68,103000)==PDR5_START);
    pdr5_reset(&r);assert(!pdr5_complete(&r,words,103010,104000));
    assert(pdr5_request(&r,other,68,104000)==PDR5_REJECT);
    m.link_nonce[0]=5;m.generation=2;assert(pdr5_bind(&r,m.link_nonce,2,78));
    assert(pdr5_request(&r,other,68,105000)==PDR5_REJECT);
    pdr4_encode(&m,other,68);assert(pdr5_request(&r,other,68,106000)==PDR5_START);
    assert(!pdr5_complete(&r,words,106010,206001));
    for(unsigned i=0;i<68;i++){uint8_t bad[68];memcpy(bad,other,68);bad[i]^=1;assert(pdr5_request(&r,bad,68,206002)==PDR5_REJECT);}
    /* At 10 Hz a new scan commonly arrives just after the previous replay TTL.
       It must start a new measurement, while an expired retry still aborts. */
    pdr5_reset(&r);assert(pdr5_bind(&r,m.link_nonce,m.generation,79));
    m.capture_counter=10;m.scan=1;pdr4_encode(&m,req,68);
    assert(pdr5_request(&r,req,68,300000)==PDR5_START);
    assert(pdr5_complete(&r,words,300100,301000));
    m.scan=2;pdr4_encode(&m,other,68);
    assert(pdr5_request(&r,other,68,400001)==PDR5_START);
    assert(r.dispatched_us==400001&&r.measured_end_us==0);
    assert(pdr5_complete(&r,words,400100,401000));
    assert(pdr5_request(&r,req,68,401100)==PDR5_REJECT);
    assert(pdr5_request(&r,other,68,401100)==PDR5_REPLAY);
    assert(r.measured_end_us==401000);
    puts("PASS PDR4/1 O5 runtime: lost request/reply, wait, identical replay, age, conflict, reset, generation, expiry, fresh consecutive 10Hz scans, CRC");
    return 0;
}

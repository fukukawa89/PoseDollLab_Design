#include "pd41_gateway.h"
#include <stdio.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static void control(pd_cohort_t *c,unsigned node,uint64_t boot){
    uint8_t b[8];pd_put64(b,boot);(void)pd_o_dispatch(c,0x100+node,b,10);
    pd_put64(b,c->epoch);(void)pd_o_dispatch(c,0x120+node,b,11);
}
static bool fill(pd_cohort_t *c,unsigned node,uint32_t seq,uint16_t value){
    uint8_t b[8];pd_put32(b,seq);
    for(unsigned g=0;g<(pd_port_count[node-1]+1u)/2;g++){
        pd_put16(b+4,value);pd_put16(b+6,g*2+1<pd_port_count[node-1]?value:PD_FIXED);
        if(!pd_o_dispatch(c,0x200+node*16+g,b,2000))return false;
    }
    pd_put16(b+4,100);pd_put16(b+6,900);return pd_o_dispatch(c,0x180+node,b,3000);
}
static void ready(pd_cohort_t *c){
    pd_init(c,123);for(unsigned n=1;n<=6;n++)control(c,n,100+n);(void)pd_begin(c,1,1000);
}
int main(int argc,char **argv){
    pd_cohort_t c;pd_sample_t s;uint8_t b[8]={0};ready(&c);
    for(unsigned n=1;n<=6;n++)CHECK(fill(&c,n,1,555));
    CHECK(pd_finish(&c,4000,&s));CHECK(s.presence==63);
    for(unsigned i=0;i<44;i++)CHECK(s.words[i]==(i<3?PD_FIXED:555));
    uint8_t wire[PD_WIRE_MAX];size_t len=pd_encode(&s,0x123456789abc,789,1,wire,sizeof wire);CHECK(len);
    if(argc>1){FILE *f=NULL;CHECK(!fopen_s(&f,argv[1],"wb") && f);CHECK(fwrite(wire,1,len,f)==len);CHECK(!fclose(f));}
    /* N1 dropout after a complete frame cannot preserve the preceding waist. */
    CHECK(pd_begin(&c,2,1000));for(unsigned n=2;n<=6;n++)CHECK(fill(&c,n,2,700));
    CHECK(pd_finish(&c,15000,&s));CHECK(s.presence==62);
    for(unsigned i=3;i<6;i++)CHECK(s.words[i]==PD_MISSING);
    for(unsigned i=0;i<3;i++)CHECK(s.words[i]==PD_FIXED);
    /* G0 reset requires six fresh BOOT/ACKs; no automatic local N1 online. */
    pd_init(&c,456);CHECK(pd_begin(&c,1,1000));CHECK(!fill(&c,1,1,20));CHECK(pd_finish(&c,15000,&s));CHECK(!s.presence);
    /* N1 reboot mid-cohort invalidates the current waist even after new ACK. */
    ready(&c);CHECK(fill(&c,1,1,20));control(&c,1,999);CHECK(pd_finish(&c,15000,&s));CHECK(!(s.presence&1));
    CHECK(pd_begin(&c,2,1000));CHECK(fill(&c,1,2,21));CHECK(pd_finish(&c,15000,&s));CHECK(s.presence==1);
    /* Sensor fault differs from a missing node and from valid zero. */
    ready(&c);CHECK(fill(&c,1,1,PD_FAULT|8));CHECK(fill(&c,2,1,0));CHECK(pd_finish(&c,15000,&s));
    CHECK(s.presence==3 && s.words[3]==(PD_FAULT|8) && s.words[6]==0 && s.words[12]==PD_MISSING);
    ready(&c);CHECK(!fill(&c,1,0,5));CHECK(fill(&c,1,1,5));CHECK(!fill(&c,1,1,5));CHECK(pd_finish(&c,15000,&s));CHECK(!s.presence);
    ready(&c);CHECK(!pd_o_dispatch(&c,0x200,b,2000));CHECK(!pd_o_dispatch(&c,0x270,b,2000));CHECK(!pd_o_dispatch(&c,0x107,b,2000));
    pd_put32(b,1);pd_put16(b+4,1);pd_put16(b+6,1);CHECK(!pd_o_dispatch(&c,0x210,b,15000));
    ready(&c);pd_put64(b,122);CHECK(!pd_o_dispatch(&c,0x121,b,2000));
    ready(&c);pd_put32(b,1);pd_put16(b+4,1);pd_put16(b+6,PD_FIXED);CHECK(!pd_o_dispatch(&c,0x210,b,2000));
    puts("PASS: G0 dispatch, all 41 axes, absent N1, restart, stale/duplicate/late frames, fault/fixed/zero and legacy wire identity");
    return 0;
}

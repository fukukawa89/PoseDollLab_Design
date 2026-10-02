#include "session.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static p21_session s;
static p21_message m,out;
static void probe(void){m=(p21_message){.type=P21_PROBE};assert(p21_session_command(&s,&m,100,&out));assert(out.type==P21_HELLO);m=out;m.type=P21_REQUEST;m.capture[0]=1;}
int main(void){
 p21_session_init(&s,123,456);
 m=(p21_message){.type=P21_REQUEST,.device=123,.transport_boot=456,.body_boot=456};m.capture[0]=1;
 assert(p21_session_command(&s,&m,10,&out)&&out.type==P21_ERROR&&!s.active);
 probe();assert(p21_session_command(&s,&m,1000,&out)&&out.type==P21_ACCEPTED&&s.active);
 assert(p21_session_begin(&s,1001,&out)&&out.type==P21_SCAN&&out.scan==1&&out.token==1);
 for(unsigned i=0;i<46;i++)assert(out.words[i]==P21_FAULT);
 out.valid_mask=P21_MASK;out.idle_high_mask=P21_MASK;for(unsigned i=0;i<46;i++)out.words[i]=(i<<10)|p21_crc6(i<<4);
 p21_session_complete(&s,&out,45001);assert(out.type==P21_SCAN&&s.active&&!s.in_flight);
 assert(!p21_session_begin(&s,100100,&out));
 assert(p21_session_command(&s,&m,100200,&out)&&out.type==P21_ACCEPTED&&out.request_us==1000&&out.scan==0);
 assert(p21_session_begin(&s,101001,&out)&&out.scan==2&&out.token==2);
 out.valid_mask=P21_MASK;out.idle_high_mask=P21_MASK;for(unsigned i=0;i<46;i++)out.words[i]=(2u<<10)|p21_crc6(2u<<4);
 out.words[3]=P21_FAULT;out.valid_mask&=~(UINT64_C(1)<<3);
 p21_session_complete(&s,&out,146001);assert(out.type==P21_SCAN&&!s.active);
 assert(p21_session_command(&s,&m,200000,&out)&&out.type==P21_ERROR); // retired request
 m.capture[0]=2;assert(p21_session_command(&s,&m,200000,&out)&&out.type==P21_ACCEPTED);
 p21_message wrong=m;wrong.body_boot++;assert(p21_session_command(&s,&wrong,200001,&out)&&out.type==P21_ERROR&&!s.active);
 m.capture[0]=3;assert(p21_session_command(&s,&m,300000,&out)&&out.type==P21_ACCEPTED);
 wrong=m;wrong.type=P21_CANCEL;wrong.capture[0]=4;assert(!p21_session_command(&s,&wrong,300001,&out)&&s.active);
 wrong.capture[0]=3;assert(!p21_session_command(&s,&wrong,300002,&out)&&!s.active);
 m.capture[0]=4;assert(p21_session_command(&s,&m,400000,&out)&&out.type==P21_ACCEPTED);
 assert(p21_session_begin(&s,399999,&out)&&out.type==P21_ERROR); // backwards clock
 m.capture[0]=5;assert(p21_session_command(&s,&m,500000,&out)&&out.type==P21_ACCEPTED);
 assert(p21_session_begin(&s,3500001,&out)&&out.type==P21_ERROR); // expired request
 m.capture[0]=6;assert(p21_session_command(&s,&m,600000,&out)&&out.type==P21_ACCEPTED);
 assert(p21_session_begin(&s,600000,&out));p21_session_complete(&s,&out,660001);assert(out.type==P21_ERROR&&!s.active);
 m.capture[0]=7;assert(p21_session_command(&s,&m,700000,&out)&&out.type==P21_ACCEPTED);
 s.token=UINT32_MAX;assert(p21_session_begin(&s,700000,&out)&&out.type==P21_ERROR);
 s.token=7;m.capture[0]=8;assert(p21_session_command(&s,&m,800000,&out)&&out.type==P21_ACCEPTED);
 assert(p21_session_begin(&s,800000,&out));out.token++;p21_session_complete(&s,&out,840000);assert(out.type==P21_ERROR);
 m.capture[0]=9;s.retired_count=P21_RETIRED_LIMIT;assert(p21_session_command(&s,&m,900000,&out)&&out.type==P21_ERROR);
 p21_session_init(&s,123,457);probe();wrong=m;wrong.transport_boot=456;assert(p21_session_command(&s,&wrong,1,&out)&&out.type==P21_ERROR);
 puts("P21 session PASS: handshake, identity/reboot, fresh scans, duplicate ACK, replay, cancel, faulty axis, clock rollback, timeout, token overflow, forged completion, capture capacity");return 0;
}

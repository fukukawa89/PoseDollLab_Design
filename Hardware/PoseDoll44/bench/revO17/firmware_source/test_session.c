#include "session.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static p17_session s;
static p17_message m,out;
static void probe(void){m=(p17_message){.type=P17_PROBE};assert(p17_session_command(&s,&m,100,&out));assert(out.type==P17_HELLO);m=out;m.type=P17_REQUEST;m.capture[0]=1;}
int main(void){
 p17_session_init(&s,123,456);
 m=(p17_message){.type=P17_REQUEST,.device=123,.transport_boot=456,.body_boot=456};m.capture[0]=1;
 assert(p17_session_command(&s,&m,10,&out)&&out.type==P17_ERROR&&!s.active);
 probe();assert(p17_session_command(&s,&m,1000,&out)&&out.type==P17_ACCEPTED&&s.active);
 assert(p17_session_begin(&s,1001,&out)&&out.type==P17_SCAN&&out.scan==1&&out.token==1);
 for(unsigned i=0;i<46;i++)assert(out.words[i]==P17_FAULT);
 out.valid_mask=P17_MASK;for(unsigned i=0;i<46;i++)out.words[i]=(uint16_t)i;
 p17_session_complete(&s,&out,45001);assert(out.type==P17_SCAN&&s.active&&!s.in_flight);
 assert(!p17_session_begin(&s,100100,&out));
 assert(p17_session_command(&s,&m,100200,&out)&&out.type==P17_ACCEPTED&&out.request_us==1000&&out.scan==0);
 assert(p17_session_begin(&s,101001,&out)&&out.scan==2&&out.token==2);
 out.valid_mask=P17_MASK;for(unsigned i=0;i<46;i++)out.words[i]=2;
 out.words[3]=P17_FAULT;out.valid_mask&=~(UINT64_C(1)<<3);
 p17_session_complete(&s,&out,146001);assert(out.type==P17_SCAN&&!s.active);
 assert(p17_session_command(&s,&m,200000,&out)&&out.type==P17_ERROR); // retired request
 m.capture[0]=2;assert(p17_session_command(&s,&m,200000,&out)&&out.type==P17_ACCEPTED);
 p17_message wrong=m;wrong.body_boot++;assert(p17_session_command(&s,&wrong,200001,&out)&&out.type==P17_ERROR&&!s.active);
 m.capture[0]=3;assert(p17_session_command(&s,&m,300000,&out)&&out.type==P17_ACCEPTED);
 wrong=m;wrong.type=P17_CANCEL;wrong.capture[0]=4;assert(!p17_session_command(&s,&wrong,300001,&out)&&s.active);
 wrong.capture[0]=3;assert(!p17_session_command(&s,&wrong,300002,&out)&&!s.active);
 m.capture[0]=4;assert(p17_session_command(&s,&m,400000,&out)&&out.type==P17_ACCEPTED);
 assert(p17_session_begin(&s,399999,&out)&&out.type==P17_ERROR); // backwards clock
 m.capture[0]=5;assert(p17_session_command(&s,&m,500000,&out)&&out.type==P17_ACCEPTED);
 assert(p17_session_begin(&s,3500001,&out)&&out.type==P17_ERROR); // expired request
 m.capture[0]=6;assert(p17_session_command(&s,&m,600000,&out)&&out.type==P17_ACCEPTED);
 assert(p17_session_begin(&s,600000,&out));p17_session_complete(&s,&out,660001);assert(out.type==P17_ERROR&&!s.active);
 m.capture[0]=7;assert(p17_session_command(&s,&m,700000,&out)&&out.type==P17_ACCEPTED);
 s.token=UINT32_MAX;assert(p17_session_begin(&s,700000,&out)&&out.type==P17_ERROR);
 s.token=7;m.capture[0]=8;assert(p17_session_command(&s,&m,800000,&out)&&out.type==P17_ACCEPTED);
 assert(p17_session_begin(&s,800000,&out));out.token++;p17_session_complete(&s,&out,840000);assert(out.type==P17_ERROR);
 m.capture[0]=9;s.retired_count=P17_RETIRED_LIMIT;assert(p17_session_command(&s,&m,900000,&out)&&out.type==P17_ERROR);
 p17_session_init(&s,123,457);probe();wrong=m;wrong.transport_boot=456;assert(p17_session_command(&s,&wrong,1,&out)&&out.type==P17_ERROR);
 puts("P17 session PASS: handshake, identity/reboot, fresh scans, duplicate ACK, replay, cancel, faulty axis, clock rollback, timeout, token overflow, forged completion, capture capacity");return 0;
}

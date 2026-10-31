#include "session.h"
#include <string.h>
void p17_session_init(p17_session*s,uint64_t device,uint64_t boot){
 memset(s,0,sizeof(*s));s->identity=(p17_message){.type=P17_HELLO,.device=device,.transport_boot=boot,.body_boot=boot};s->current=s->identity;
}
void p17_session_fail(p17_session*s,p17_message*out){s->active=false;s->in_flight=false;*out=s->current;out->type=P17_ERROR;}
bool p17_session_command(p17_session*s,const p17_message*m,uint64_t now,p17_message*out){
 if(m->type==P17_PROBE){s->active=false;s->in_flight=false;s->discovered=true;s->current=s->identity;*out=s->identity;return true;}
 if(!s->discovered||m->device!=s->identity.device||m->transport_boot!=s->identity.transport_boot||m->body_boot!=s->identity.body_boot){p17_session_fail(s,out);return true;}
 if(m->type==P17_CANCEL||m->type==P17_STOP){if(!memcmp(m->capture,s->current.capture,16)){s->active=false;s->in_flight=false;}return false;}
 if(m->type!=P17_REQUEST){p17_session_fail(s,out);return true;}
 unsigned nonzero=0;for(unsigned i=0;i<16;i++)nonzero|=m->capture[i];
 if(!nonzero){p17_session_fail(s,out);return true;}
 if(s->active&&!memcmp(m->capture,s->current.capture,16)){
  *out=s->identity;out->type=P17_ACCEPTED;out->request_us=s->current.request_us;memcpy(out->capture,m->capture,16);return true;
 }
 for(unsigned i=0;i<s->retired_count;i++)if(!memcmp(s->retired[i],m->capture,16)){p17_session_fail(s,out);return true;}
 if(s->retired_count==P17_RETIRED_LIMIT){p17_session_fail(s,out);return true;}
 memcpy(s->retired[s->retired_count++],m->capture,16);
 s->current=s->identity;s->current.type=P17_ACCEPTED;s->current.request_us=now;memcpy(s->current.capture,m->capture,16);
 s->active=true;s->in_flight=false;s->next_scan=now;*out=s->current;return true;
}
bool p17_session_begin(p17_session*s,uint64_t now,p17_message*out){
 if(!s->active)return false;
 if(now<s->current.request_us||now-s->current.request_us>3000000||s->token==UINT32_MAX||s->in_flight){p17_session_fail(s,out);return true;}
 if(now<s->next_scan)return false;
 s->current.token=++s->token;s->current.scan++;s->current.start_us=now;s->current.end_us=0;s->current.valid_mask=0;s->current.type=P17_SCAN;
 for(unsigned i=0;i<P17_AXES;i++)s->current.words[i]=P17_FAULT;
 s->in_flight=true;*out=s->current;return true;
}
void p17_session_complete(p17_session*s,p17_message*scan,uint64_t end){
 if(!s->in_flight||scan->scan!=s->current.scan||scan->token!=s->current.token||memcmp(scan->capture,s->current.capture,16)||end<=scan->start_us||end-scan->start_us>60000){p17_session_fail(s,scan);return;}
 scan->end_us=end;s->current=*scan;s->next_scan=scan->start_us+100000;s->in_flight=false;
 if(scan->valid_mask!=P17_MASK)s->active=false;
}

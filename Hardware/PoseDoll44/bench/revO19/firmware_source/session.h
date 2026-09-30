#ifndef P17_SESSION_H
#define P17_SESSION_H
#include "raw46.h"
enum { P17_RETIRED_LIMIT=4096 };
typedef struct {
 p17_message identity,current;
 bool discovered,active,in_flight;
 uint32_t token;
 uint64_t next_scan;
 uint8_t retired[P17_RETIRED_LIMIT][16];
 unsigned retired_count;
} p17_session;
void p17_session_init(p17_session*s,uint64_t device,uint64_t boot);
void p17_session_fail(p17_session*s,p17_message*out);
bool p17_session_command(p17_session*s,const p17_message*m,uint64_t now,p17_message*out);
bool p17_session_begin(p17_session*s,uint64_t now,p17_message*out);
void p17_session_complete(p17_session*s,p17_message*scan,uint64_t end);
#endif

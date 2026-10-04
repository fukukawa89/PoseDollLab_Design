#ifndef P21_SESSION_H
#define P21_SESSION_H
#include "raw46.h"
enum { P21_RETIRED_LIMIT=4096 };
typedef struct {
 p21_message identity,current;
 bool discovered,active,in_flight;
 uint32_t token;
 uint64_t next_scan;
 uint8_t retired[P21_RETIRED_LIMIT][16];
 unsigned retired_count;
} p21_session;
void p21_session_init(p21_session*s,uint64_t device,uint64_t boot);
void p21_session_fail(p21_session*s,p21_message*out);
bool p21_session_command(p21_session*s,const p21_message*m,uint64_t now,p21_message*out);
bool p21_session_begin(p21_session*s,uint64_t now,p21_message*out);
void p21_session_complete(p21_session*s,p21_message*scan,uint64_t end);
#endif

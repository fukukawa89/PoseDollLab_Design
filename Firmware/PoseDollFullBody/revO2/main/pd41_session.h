#pragma once
#include "pd41_core.h"
enum { O2_EPOCH=0x080,O2_SYNC=0x081,O2_POLL=0x090,O2_BOOT=0x100,O2_JOIN_ACK=0x130,O2_JOIN_OK=0x150 };
typedef enum { O2_NO_ACTION,O2_RESET_EPOCH,O2_REPLY_JOIN,O2_READY } o2_action_t;
typedef struct { uint64_t epoch,challenge;uint32_t last_seq;bool ready; } o2_regional_t;
typedef struct { uint64_t challenge,observed_boot;unsigned node;bool boot_seen; } o2_join_t;
void o2_regional_reset(o2_regional_t *s);
o2_action_t o2_regional_control(o2_regional_t *s,unsigned node,uint32_t id,uint64_t value);
bool o2_regional_sync(o2_regional_t *s,uint32_t seq);
bool o2_join_begin(o2_join_t *j,pd_cohort_t *c,unsigned node,uint64_t challenge);
bool o2_join_receive(o2_join_t *j,pd_cohort_t *c,uint32_t id,uint64_t value,bool *confirm);
bool o2_all_angles_normal(const pd_sample_t *s);

unsigned o2_select_maintenance(const pd_cohort_t *c,const bool missing[6],unsigned *cursor,uint64_t now,uint64_t last);

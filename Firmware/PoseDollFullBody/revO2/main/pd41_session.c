/* Maintenance uses a dedicated no-SYNC cohort, one addressed node and a fresh
 * challenge. Stable repeated EPOCH has zero TX; no periodic BOOT/ACK storms.
 * CAN control extensions require Rev O2 on all roles; USB PD41 v1 is unchanged. */
#include "pd41_session.h"
#include <string.h>
void o2_regional_reset(o2_regional_t *s){memset(s,0,sizeof(*s));}
o2_action_t o2_regional_control(o2_regional_t *s,unsigned node,uint32_t id,uint64_t v){
    if(node<1 || node>6 || !v)return O2_NO_ACTION;
    if(id==O2_EPOCH){
        if(v==s->epoch)return O2_NO_ACTION;
        o2_regional_reset(s);s->epoch=v;return O2_RESET_EPOCH;
    }
    if(id==O2_POLL+node && s->epoch){s->challenge=v;s->ready=false;return O2_REPLY_JOIN;}
    if(id==O2_JOIN_OK+node && s->epoch && s->challenge==v){s->challenge=0;s->ready=true;return O2_READY;}
    return O2_NO_ACTION;
}
bool o2_regional_sync(o2_regional_t *s,uint32_t seq){
    if(!s->epoch || !s->ready || !seq || seq<=s->last_seq)return false;
    s->last_seq=seq;return true;
}
bool o2_join_begin(o2_join_t *j,pd_cohort_t *c,unsigned node,uint64_t challenge){
    if(!c->epoch || c->active || node<1 || node>6 || !challenge)return false;
    *j=(o2_join_t){.challenge=challenge,.node=node};c->node[node-1].blocked=true;return true;
}
bool o2_join_receive(o2_join_t *j,pd_cohort_t *c,uint32_t id,uint64_t value,bool *confirm){
    *confirm=false;
    if(c->active || !j->node || !j->challenge)return false;
    if(id==O2_BOOT+j->node && value){
        (void)pd_boot(c,j->node,value);j->observed_boot=value;j->boot_seen=true;return true;
    }
    if(id==O2_JOIN_ACK+j->node && value==(j->challenge ^ j->observed_boot) && j->boot_seen && c->node[j->node-1].boot==j->observed_boot){
        *confirm=pd_ack(c,j->node,c->epoch,j->observed_boot);if(*confirm)j->challenge=0;return *confirm;
    }
    return false;
}
bool o2_all_angles_normal(const pd_sample_t *s){
    if(s->presence!=63)return false;
    for(unsigned i=0;i<3;i++)if(s->words[i]!=PD_FIXED)return false;
    for(unsigned i=3;i<44;i++)if(s->words[i]>=PD_FIXED)return false;
    return true;
}

unsigned o2_select_maintenance(const pd_cohort_t *c,const bool missing[6],unsigned *cursor,uint64_t now,uint64_t last){
    if(last && now-last<100000)return 0;
    for(unsigned i=0;i<6;i++){unsigned n=(*cursor+i)%6;if(missing[n] || c->node[n].blocked){*cursor=(n+1)%6;return n+1;}}
    return 0;
}

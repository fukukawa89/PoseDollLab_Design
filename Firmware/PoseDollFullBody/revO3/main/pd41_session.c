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

void o3_recovery_reset(o3_recovery_t *r){memset(r,0,sizeof(*r));}
unsigned o3_select_maintenance(o3_recovery_t *r,const pd_cohort_t *c,const bool missing[6],uint64_t now){
    if(r->attempted && now-r->last_attempt_us<100000)return 0;
    for(unsigned i=0;i<6;i++){
        unsigned n=(r->cursor+i)%6;
        if((missing[n] || c->node[n].blocked) && now>=r->due_us[n]){
            uint64_t interval=100000;
            if(r->consecutive_attempts[n]<UINT16_MAX)r->consecutive_attempts[n]++;
            unsigned k=r->consecutive_attempts[n];
            if(k>2){unsigned shift=k-2;interval=shift>=6?5000000:100000ULL<<shift;}
            if(interval>5000000)interval=5000000;
            r->due_us[n]=now+interval;r->last_attempt_us=now;r->attempted=true;
            r->cursor=(n+1)%6;r->attempts[n]++;r->maintenance_cohorts++;
            return n+1;
        }
    }
    return 0;
}
void o3_observe_sample(o3_recovery_t *r,const pd_sample_t *s){
    for(unsigned i=0;i<6;i++)if(s->presence&(1u<<i)){
        r->consecutive_attempts[i]=0;r->due_us[i]=0;
    }
}
void o3_join_end(o2_join_t *j,pd_cohort_t *c,bool admitted){
    if(j->node && !admitted)c->node[j->node-1].blocked=true;
    memset(j,0,sizeof(*j));
}

#include "pd41_session.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    o2_regional_t n;o2_regional_reset(&n);pd_cohort_t c;pd_init(&c,77);o2_join_t j={0};bool confirm=false;
    assert(!o2_regional_sync(&n,1));
    assert(o2_regional_control(&n,3,O2_EPOCH,77)==O2_RESET_EPOCH);
    for(unsigned i=0;i<10000;i++)assert(o2_regional_control(&n,3,O2_EPOCH,77)==O2_NO_ACTION);
    assert(!o2_regional_sync(&n,1));
    assert(o2_join_begin(&j,&c,3,12345));
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,12345,&confirm));
    assert(o2_regional_control(&n,3,O2_POLL+4,12345)==O2_NO_ACTION);
    assert(o2_regional_control(&n,3,O2_POLL+3,12345)==O2_REPLY_JOIN);
    assert(!o2_join_receive(&j,&c,O2_BOOT+4,88,&confirm));
    assert(o2_join_receive(&j,&c,O2_BOOT+3,88,&confirm));
    assert(!o2_join_receive(&j,&c,0x120+3,77,&confirm)); /* legacy/stale ACK rejected */
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,12344,&confirm));
    assert(o2_join_receive(&j,&c,O2_JOIN_ACK+3,(12345^88),&confirm) && confirm);
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,(12345^88),&confirm)); /* consumed challenge */
    assert(!n.ready); /* lost confirm must not make node emit data */
    assert(o2_regional_control(&n,3,O2_JOIN_OK+3,12344)==O2_NO_ACTION);
    assert(o2_regional_control(&n,3,O2_JOIN_OK+3,12345)==O2_READY);
    assert(o2_regional_sync(&n,100));assert(!o2_regional_sync(&n,100));assert(!o2_regional_sync(&n,99));
    for(unsigned i=0;i<10000;i++)assert(o2_regional_control(&n,3,O2_EPOCH,77)==O2_NO_ACTION);
    assert(n.ready && n.last_seq==100);
    /* New epoch flushes challenge, ready and sequence; old confirmation fails. */
    assert(o2_regional_control(&n,3,O2_EPOCH,78)==O2_RESET_EPOCH);
    assert(!n.ready && !n.last_seq && !n.challenge);
    assert(o2_regional_control(&n,3,O2_JOIN_OK+3,12345)==O2_NO_ACTION);
    /* Reset on bus fault cannot reuse readiness from the preceding boot. */
    o2_regional_reset(&n);assert(!o2_regional_sync(&n,101));
    /* An active sampling cohort cannot consume join messages. */
    assert(pd_begin(&c,1,1000));assert(!o2_join_begin(&j,&c,2,999));
    assert(!o2_join_receive(&j,&c,O2_BOOT+3,999,&confirm));
    pd_sample_t sample;assert(pd_finish(&c,15000,&sample));
    assert(o2_join_begin(&j,&c,3,555));
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,12345,&confirm));
    assert(o2_join_receive(&j,&c,O2_BOOT+3,999,&confirm));
    assert(o2_join_receive(&j,&c,O2_JOIN_ACK+3,(555^999),&confirm) && confirm);
    assert(c.node[2].boot==999 && !c.node[2].blocked);
    /* Presence and valid angle quality are different metrics. */
    sample.presence=63;for(unsigned i=0;i<44;i++)sample.words[i]=i<3?PD_FIXED:0;
    assert(o2_all_angles_normal(&sample));sample.words[12]=PD_FAULT|1;assert(!o2_all_angles_normal(&sample));
    sample.words[12]=PD_MISSING;assert(!o2_all_angles_normal(&sample));sample.words[12]=0;sample.presence=31;assert(!o2_all_angles_normal(&sample));
    /* Wrong/stale BOOT cannot be combined with a new challenge-bound proof. */
    assert(o2_join_begin(&j,&c,3,777));assert(o2_join_receive(&j,&c,O2_BOOT+3,111,&confirm));
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,(777^222),&confirm));
    assert(o2_join_receive(&j,&c,O2_BOOT+3,222,&confirm));assert(o2_join_receive(&j,&c,O2_JOIN_ACK+3,(777^222),&confirm)&&confirm);
    /* Timeout clears all challenge material, rejecting a delayed ACK. */
    o3_join_end(&j,&c,false);assert(!j.node && !j.challenge && c.node[2].blocked);
    assert(!o2_join_receive(&j,&c,O2_JOIN_ACK+3,(777^222),&confirm));
    bool missing[6]={false};o3_recovery_t r;o3_recovery_reset(&r);
    for(unsigned i=0;i<6;i++)c.node[i].blocked=false;
    for(uint64_t now=1;now<1800000000ULL;now+=16667)assert(o3_select_maintenance(&r,&c,missing,now)==0);
    /* Thirty minutes with one permanently missing node: losses are not hidden. */
    missing[2]=true;unsigned polls=0,cohorts=0,tail_polls=0,tail_cohorts=0;uint64_t last=0;
    for(uint64_t now=1;now<1800000000ULL;now+=16667){
        cohorts++;if(now>=30000000)tail_cohorts++;
        unsigned target=o3_select_maintenance(&r,&c,missing,now);
        if(target){assert(target==3);assert(!last || now-last>=100000);last=now;polls++;if(now>=30000000)tail_polls++;}
    }
    assert(polls<380 && polls>350);assert((double)tail_polls/tail_cohorts<.0034);
    assert(r.maintenance_cohorts==polls && r.attempts[2]==polls);
    printf("RECOVERY one_missing cohorts=%u maintenance=%u healthy_opportunity=%.9f tail_opportunity=%.9f max_backoff_us=5000000\n",cohorts,polls,1.0-(double)polls/cohorts,1.0-(double)tail_polls/tail_cohorts);
    /* JOIN_OK loss/repeated admission cannot reset backoff without data. */
    uint16_t attempts=r.consecutive_attempts[2];sample.presence=59;o3_observe_sample(&r,&sample);assert(r.consecutive_attempts[2]==attempts);
    sample.presence=63;o3_observe_sample(&r,&sample);assert(!r.consecutive_attempts[2] && !r.due_us[2]);
    /* A new drop after an observed recovery gets quick retries again. */
    assert(o3_select_maintenance(&r,&c,missing,1801000000ULL)==3);assert(r.consecutive_attempts[2]==1);
    /* Six missing nodes: fair initial round and no indefinite starvation. */
    o3_recovery_reset(&r);for(unsigned i=0;i<6;i++)missing[i]=true;
    unsigned first=0;cohorts=0;
    for(uint64_t now=1;now<60000000ULL;now+=16667){
        cohorts++;unsigned target=o3_select_maintenance(&r,&c,missing,now);
        if(target && first<6){assert(target==++first);}
    }
    assert(first==6);for(unsigned i=0;i<6;i++)assert(r.attempts[i]>=15 && r.attempts[i]<=22);
    printf("RECOVERY six_missing cohorts=%u maintenance=%u attempts=%u,%u,%u,%u,%u,%u\n",cohorts,r.maintenance_cohorts,r.attempts[0],r.attempts[1],r.attempts[2],r.attempts[3],r.attempts[4],r.attempts[5]);
    o3_recovery_reset(&r);assert(!r.attempted && !r.maintenance_cohorts); /* gateway reset */
    puts("PASS: session freshness/loss/replay/reset, timeout cleanup, 30-minute recovery model, backoff reset on data, six-node fairness");
    return 0;
}

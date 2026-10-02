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
    bool missing[6]={false};unsigned cursor=0;uint64_t last=0;unsigned polls=0;
    for(unsigned i=0;i<6;i++)c.node[i].blocked=false;
    for(uint64_t now=1;now<1800000000ULL;now+=16667)assert(o2_select_maintenance(&c,missing,&cursor,now,last)==0);
    missing[2]=true;
    for(uint64_t now=1;now<1000001;now+=16667){unsigned target=o2_select_maintenance(&c,missing,&cursor,now,last);if(target){assert(target==3);assert(!last||now-last>=100000);last=now;polls++;}}
    assert(polls==10); /* failed node cannot consume every sampling cohort */
    puts("PASS: 20000 same-EPOCH no-TX events, addressed join, missing/reordered/replayed handshake, new epoch/reset, sequence freshness, and quality metrics");
    return 0;
}

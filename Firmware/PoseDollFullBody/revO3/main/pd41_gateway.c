#include "pd41_gateway.h"
enum { CAN_BOOT=0x100, CAN_ACK=0x120, CAN_END=0x180, CAN_PAIR=0x200 };
bool pd_o_dispatch(pd_cohort_t *c,uint32_t id,const uint8_t p[8],uint64_t us){
    if(id>=CAN_BOOT+1 && id<=CAN_BOOT+PD_NODE_COUNT)return pd_boot(c,id-CAN_BOOT,pd_get64(p));
    if(id>=CAN_ACK+1 && id<=CAN_ACK+PD_NODE_COUNT){
        unsigned n=id-CAN_ACK;return pd_ack(c,n,pd_get64(p),c->node[n-1].boot);
    }
    if(id>=CAN_END+1 && id<=CAN_END+PD_NODE_COUNT)return pd_end(c,id-CAN_END,pd_get32(p),pd_get16(p+4),pd_get16(p+6),us);
    if(id>=CAN_PAIR+16 && id<CAN_PAIR+(PD_NODE_COUNT+1)*16){
        unsigned x=id-CAN_PAIR;return pd_pair(c,x/16,pd_get32(p),x%16,pd_get16(p+4),pd_get16(p+6),us);
    }
    return false;
}

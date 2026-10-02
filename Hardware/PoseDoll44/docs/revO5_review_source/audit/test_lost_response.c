#include "remote_link.h"
#include <stdio.h>
#include <assert.h>
int main(void) {
    pdr4_message m={0}; pdr4_session s;
    m.type=PDR4_REQUEST; m.link_nonce[0]=1; m.capture[0]=2;
    m.scan=1; m.generation=7; m.capture_counter=1;
    assert(pdr4_bind(&s,m.link_nonce,m.generation));
    int first=pdr4_accept_request(&s,&m);
    /* The response is dropped: the host retries the same outstanding request. */
    int retry1=pdr4_accept_request(&s,&m);
    int retry2=pdr4_accept_request(&s,&m);
    printf("{\"first_request_accepted\":%d,\"retry_after_lost_response\":%d,\"second_retry\":%d,\"last_scan\":%llu}\n",first,retry1,retry2,(unsigned long long)s.last_scan);
    assert(first==1 && retry1==0 && retry2==0 && s.last_scan==1);
    return 0;
}

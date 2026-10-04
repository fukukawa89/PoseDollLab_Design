#pragma once
#include "remote_link.h"
/* PDR4/1 wire unchanged. WAIT is local and produces no invented BUSY frame.
 * A single response remains cached for <=100 ms from first dispatch. */
enum { PDR5_REJECT=0, PDR5_START=1, PDR5_WAIT=2, PDR5_REPLAY=3 };
enum { PDR5_IDLE=0, PDR5_ACQUIRING=1, PDR5_READY=2, PDR5_FAULT=3 };
typedef struct {
    pdr4_session session;
    uint64_t satellite_boot, dispatched_us, measured_start_us, measured_end_us;
    uint8_t phase, request[PDR4_REQUEST_BYTES], response[PDR4_RESPONSE_BYTES];
} pdr5_runtime;
void pdr5_reset(pdr5_runtime* r);
int pdr5_bind(pdr5_runtime* r,const uint8_t nonce[16],uint64_t generation,uint64_t actual_boot);
int pdr5_request(pdr5_runtime* r,const uint8_t* frame,size_t bytes,uint64_t now);
int pdr5_complete(pdr5_runtime* r,const uint16_t words[4],uint64_t start,uint64_t end);
/* Returned buffer is stable until the next accepted request or reset; caller owns UART TC/DE. */
const uint8_t* pdr5_reply(pdr5_runtime* r,uint64_t now);

#ifndef PDR4_REMOTE_LINK_H
#define PDR4_REMOTE_LINK_H
#include <stdint.h>
#include <stddef.h>
/* Experimental point-to-point codec, not a flashed STM32/ESP driver.
   All wire integers little-endian; no packed struct or native ABI on wire. */
#define PDR4_HEADER 64u
#define PDR4_REQUEST_BYTES 68u
#define PDR4_RESPONSE_BYTES 80u
#define PDR4_MAX_BYTES 80u
#define PDR4_REQUEST 2u
#define PDR4_RESPONSE 3u
typedef struct { uint8_t type, link_nonce[16], capture[16]; uint64_t scan, generation, capture_counter; uint32_t duration_us; uint16_t words[4]; } pdr4_message;
typedef struct { uint8_t joined,link_nonce[16]; uint64_t generation,last_scan,capture_counter; uint8_t capture[16]; } pdr4_session;
size_t pdr4_encode(const pdr4_message* m,uint8_t* output,size_t capacity);
int pdr4_decode(const uint8_t* input,size_t size,pdr4_message* output);
void pdr4_reset(pdr4_session* s);
/* Caller must complete a fresh proximal challenge after reset before binding.
   This function cannot create boot uniqueness; the outer join driver is pending. */
int pdr4_bind(pdr4_session* s,const uint8_t nonce[16],uint64_t generation);
int pdr4_accept_request(pdr4_session* s,const pdr4_message* m);
#endif

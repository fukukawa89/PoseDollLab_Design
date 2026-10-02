#ifndef P15_RAW46_H
#define P15_RAW46_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
enum { P15_BYTES=192, P15_AXES=46, P15_CHAINS=6, P15_MAX_CHAIN=10,
       P15_PROBE=0,P15_HELLO,P15_REQUEST,P15_ACCEPTED,P15_SCAN,P15_CANCEL,P15_STOP,P15_ERROR,P15_READ,P15_BODY_SCAN };
#define P15_MASK ((UINT64_C(1)<<46)-1)
#define P15_FAULT UINT16_C(0x8000)
extern const uint8_t p15_counts[6];
extern const uint16_t p15_registers[5];
typedef struct {
 uint8_t type,capture[16];
 uint64_t device,gateway_boot,body_boot,request_us,start_us,end_us,valid_mask;
 uint32_t scan,token;
 uint16_t words[46];
} p15_message;
uint32_t p15_crc(const uint8_t *p,size_t n);
bool p15_encode(const p15_message *m,uint8_t out[192]);
bool p15_decode(const uint8_t *p,size_t n,p15_message *out);
uint16_t p15_command(uint16_t address);
bool p15_decode_chain(const uint16_t rx[6][10],unsigned count,uint16_t *out);
#endif

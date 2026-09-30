#ifndef P17_RAW46_H
#define P17_RAW46_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
enum { P17_BYTES=192, P17_AXES=46, P17_CHAINS=6, P17_MAX_CHAIN=10,
       P17_PROBE=0,P17_HELLO,P17_REQUEST,P17_ACCEPTED,P17_SCAN,P17_CANCEL,P17_STOP,P17_ERROR };
#define P17_MASK ((UINT64_C(1)<<46)-1)
#define P17_FAULT UINT16_C(0x8000)
extern const uint8_t p17_counts[6];
extern const uint16_t p17_registers[5];
typedef struct {
 uint8_t type,capture[16];
 uint64_t device,transport_boot,body_boot,request_us,start_us,end_us,valid_mask;
 uint32_t scan,token;
 uint16_t words[46];
} p17_message;
uint32_t p17_crc(const uint8_t *p,size_t n);
bool p17_encode(const p17_message *m,uint8_t out[192]);
bool p17_decode(const uint8_t *p,size_t n,p17_message *out);
uint16_t p17_command(uint16_t address);
bool p17_decode_chain(const uint16_t rx[6][10],unsigned count,uint16_t *out);
#endif

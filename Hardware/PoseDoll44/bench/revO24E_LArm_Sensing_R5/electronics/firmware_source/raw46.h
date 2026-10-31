#ifndef P21_RAW46_H
#define P21_RAW46_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
enum { P21_BYTES=280, P21_AXES=46,
 P21_PROBE=0,P21_HELLO,P21_REQUEST,P21_ACCEPTED,P21_SCAN,P21_CANCEL,P21_STOP,P21_ERROR };
#define P21_MASK ((UINT64_C(1)<<46)-1)
#define P21_FAULT UINT32_C(0xffffff)
typedef struct {
 uint8_t type,capture[16];
 uint64_t device,transport_boot,body_boot,request_us,start_us,end_us,valid_mask,idle_high_mask;
 uint32_t scan,token,words[46],tm[8];
} p21_message;
uint8_t p21_crc6(uint32_t data18);
bool p21_sensor_valid(uint32_t word,bool idle_high);
uint32_t p21_crc(const uint8_t*p,size_t n);
bool p21_encode(const p21_message*m,uint8_t out[P21_BYTES]);
bool p21_decode(const uint8_t*p,size_t n,p21_message*out);
uint8_t r5_crc4(uint32_t w);
bool r5_tm_crc_ok(uint32_t w);
uint16_t r5_tm_data(uint32_t w);
bool r5_tm_valid(const uint32_t*t);
#endif

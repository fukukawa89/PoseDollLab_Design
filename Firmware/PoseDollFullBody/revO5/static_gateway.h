#pragma once
#include <stdint.h>
#include <stddef.h>
/* PDG5/1 USB and PDC5/1 classic CAN. Deliberately incompatible with legacy PD41. */
enum { PD5_PROBE=1,PD5_HELLO=2,PD5_REQUEST=3,PD5_ACCEPTED=4,PD5_SCAN=5,PD5_CANCEL=6,PD5_ERROR=7,PD5_STOP=8 };
enum { PD5_USB_BYTES=220,PD5_CAN_REQUEST_BYTES=28,PD5_CAN_REPLY_BYTES=52,PD5_MISSING=0xffff,PD5_FIXED=0x4000 };
#define PD5_FULL_MASK (UINT64_C(0xfffffffffff) & ~UINT64_C(7))
typedef struct {
    uint8_t type,capture[16];
    uint64_t device,boot,scan,request_us,start_us,end_us,source_boot[6],physical_mask;
    uint16_t words[44];
} pd5_usb;
typedef struct {uint8_t node,operation;uint64_t gateway_boot,expected_boot;uint32_t token;} pd5_region_request;
typedef struct {uint8_t node,count;uint64_t gateway_boot,boot;uint32_t token,duration_us;uint16_t mask,words[9];} pd5_region_result;
typedef uint16_t (*pd5_read_axis)(void* context,unsigned port);
/* A uses SPI; a future C adapter must supply the same fresh result contract. */
void pd5_acquire_ports(pd5_region_result* out,unsigned ports,pd5_read_axis read,void* context);
int pd5_encode_usb(const pd5_usb* m,uint8_t out[PD5_USB_BYTES]);
int pd5_decode_usb(const uint8_t* wire,size_t bytes,pd5_usb* out);
int pd5_encode_request(const pd5_region_request* r,uint8_t out[28]);
int pd5_decode_request(const uint8_t* wire,size_t bytes,pd5_region_request* out);
int pd5_encode_result(const pd5_region_result* r,uint8_t out[52]);
int pd5_decode_result(const uint8_t* wire,size_t bytes,pd5_region_result* out);
void pd5_blank_scan(pd5_usb* out);
int pd5_merge_region(pd5_usb* scan,const pd5_region_result* r,const pd5_region_request* issued,uint64_t received_us);
typedef struct {uint8_t data[52],next;uint64_t started_us;} pd5_fragments;
/* Fixed <=8 fragments, ordered, bounded by 100 ms. 1 complete, 0 partial, -1 malformed. */
int pd5_fragment(pd5_fragments* s,const uint8_t bytes[8],size_t total,uint64_t now);
void pd5_make_fragment(const uint8_t* raw,size_t total,unsigned index,uint8_t out[8]);
uint32_t pd5_crc(const uint8_t* data,size_t size);

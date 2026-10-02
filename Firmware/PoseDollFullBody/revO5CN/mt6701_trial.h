#ifndef PD_MT6701_TRIAL_H
#define PD_MT6701_TRIAL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
/* Analysis-only codec. It is deliberately not linked into the O5 gateway.
 * CRC init/xor are hypotheses, not an established device protocol contract. */
typedef enum { MT_BAD_ARGUMENT, MT_BAD_CRC, MT_BAD_STATUS, MT_DECODED_UNQUALIFIED } mt_result;
typedef struct { uint16_t angle14; uint8_t status4; bool capture_eligible; } mt_sample;
uint8_t mt_trial_crc18(uint32_t payload18);
mt_result mt_trial_decode(const uint8_t *frame, size_t length, mt_sample *out);
#endif

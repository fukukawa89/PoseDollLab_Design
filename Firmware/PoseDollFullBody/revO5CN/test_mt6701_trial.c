#include "mt6701_trial.h"
#include <assert.h>
#include <stdio.h>
/* Independent polynomial long division (no shift-register implementation). */
static uint8_t reference(uint32_t payload) {
    uint32_t remainder = payload << 6;
    for (int bit = 23; bit >= 6; --bit)
        if ((remainder & (1U << bit)) != 0U) remainder ^= 0x43U << (bit - 6);
    return (uint8_t)remainder;
}
static void bytes(uint32_t word, uint8_t frame[3]) {
    frame[0] = (uint8_t)(word >> 16); frame[1] = (uint8_t)(word >> 8); frame[2] = (uint8_t)word;
}
int main(void) {
    mt_sample sample; uint8_t frame[3]; uint32_t mutations = 0U;
    for (uint32_t p = 0U; p < (1U << 18); ++p) {
        mt_result expected = (p & 15U) ? MT_BAD_STATUS : MT_DECODED_UNQUALIFIED;
        assert(mt_trial_crc18(p) == reference(p));
        bytes((p << 6) | reference(p), frame);
        assert(mt_trial_decode(frame, 3U, &sample) == expected);
        assert(sample.angle14 == (p >> 4) && sample.status4 == (p & 15U));
        assert(!sample.capture_eligible);
    }
    for (uint32_t a = 0U; a < 16384U; ++a) {
        uint32_t w = (a << 10) | reference(a << 4);
        for (uint32_t bit = 0U; bit < 24U; ++bit) {
            bytes(w ^ (1U << bit), frame);
            assert(mt_trial_decode(frame, 3U, &sample) == MT_BAD_CRC);
            assert(!sample.capture_eligible); ++mutations;
        }
    }
    bytes(0U, frame);
    assert(mt_trial_decode(frame, 3U, &sample) == MT_DECODED_UNQUALIFIED);
    assert(!sample.capture_eligible); /* all-low disconnected wire can pass CRC */
    assert(mt_trial_decode(frame, 2U, &sample) == MT_BAD_ARGUMENT);
    assert(mt_trial_decode(frame, 4U, &sample) == MT_BAD_ARGUMENT);
    assert(mt_trial_decode(NULL, 3U, &sample) == MT_BAD_ARGUMENT);
    assert(mt_trial_decode(frame, 3U, NULL) == MT_BAD_ARGUMENT);
    bytes(0xFFFFFFU, frame); assert(mt_trial_decode(frame, 3U, &sample) != MT_DECODED_UNQUALIFIED);
    printf("PASS: 262144 angle/status payloads; %u single-bit mutations; invalid lengths/nulls; all-zero cannot enable capture.\n", mutations);
    return 0;
}

#include "mt6701_trial.h"
uint8_t mt_trial_crc18(uint32_t payload18) {
    uint32_t crc = 0U;
    for (int bit = 17; bit >= 0; --bit) {
        uint32_t feedback = ((crc >> 5) ^ (payload18 >> bit)) & 1U;
        crc = ((crc << 1) & 63U) ^ (feedback ? 3U : 0U);
    }
    return (uint8_t)crc;
}
mt_result mt_trial_decode(const uint8_t *frame, size_t length, mt_sample *out) {
    uint32_t word;
    if (out == NULL) return MT_BAD_ARGUMENT;
    *out = (mt_sample){0U, 0U, false};
    if (frame == NULL || length != 3U) return MT_BAD_ARGUMENT;
    word = ((uint32_t)frame[0] << 16) | ((uint32_t)frame[1] << 8) | frame[2];
    if (mt_trial_crc18(word >> 6) != (word & 63U)) return MT_BAD_CRC;
    out->angle14 = (uint16_t)(word >> 10);
    out->status4 = (uint8_t)((word >> 6) & 15U);
    /* For this pose application, strong/weak/reserved/push/lost-track all fail.
     * No status error may be silently replaced with a zero angle. */
    if (out->status4 != 0U) return MT_BAD_STATUS;
    return MT_DECODED_UNQUALIFIED;
}

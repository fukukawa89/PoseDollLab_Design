#pragma once
#include "pd41_core.h"
/* Shared by the actual G0 firmware and host tests. Measurement slots stay N1..N6. */
bool pd_o_dispatch(pd_cohort_t *cohort, uint32_t id, const uint8_t bytes[8], uint64_t received_us);

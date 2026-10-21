"""Offline reference for O4 static-window acceptance. Not a firmware or UE driver.
Times are G0 monotonic request/response bounds, NOT synchronized per-axis timestamps.
All thresholds are proposed engineering defaults requiring physical validation.
Only accept the final complete scan of a single stable, fresh transaction.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Sequence

FIXED = 0x4000
U64_MAX = (1 << 64) - 1

class CaptureRejected(ValueError):
    """An outer state machine must clear its window on invalid data, not reuse it."""

@dataclass(frozen=True)
class Policy:
    min_scans: int = 6
    stable_window_us: int = 500_000
    max_scan_span_us: int = 100_000
    max_scan_gap_us: int = 150_000
    max_snapshot_age_us: int = 200_000
    transaction_timeout_us: int = 3_000_000
    peak_to_peak_deg: float = 0.30
    max_abs_slope_deg_s: float = 0.20

@dataclass(frozen=True)
class Scan:
    capture_id: str
    gateway_session: str
    profile_hash: str
    calibration_hash: str
    scan_id: int
    start_us: int
    end_us: int
    node_boots: tuple[str, ...]
    words: tuple[int, ...]
    crc_verified: bool

@dataclass(frozen=True)
class Snapshot:
    capture_id: str
    gateway_session: str
    scan_id: int
    source_start_us: int
    source_end_us: int
    profile_hash: str
    calibration_hash: str
    node_boots: tuple[str, ...]
    words: tuple[int, ...]
    stable_span_us: int
    max_peak_to_peak_deg: float
    max_abs_slope_deg_s: float


def _u64(n: int, name: str) -> None:
    if type(n) is not int or not 0 <= n <= U64_MAX:
        raise CaptureRejected('INVALID_TIME_OR_ID:' + name)


def _unwrap_counts(values: Sequence[int]) -> list[float]:
    """Nearest-turn unwrapping for a supposedly static window.
    Real motion faster than the polling rate may alias; this does NOT certify no motion.
    """
    out = [values[0] * 360.0 / FIXED]
    for previous, current in zip(values, values[1:]):
        delta = (current - previous + FIXED // 2) % FIXED - FIXED // 2
        out.append(out[-1] + delta * 360.0 / FIXED)
    return out


def accept_static_window(
    scans: Sequence[Scan], *, capture_id: str, gateway_session: str,
    profile_hash: str, calibration_hash: str,
    request_start_us: int, now_us: int, policy: Policy = Policy(),
) -> Snapshot:
    """Validate an already complete candidate window; do not poll or conceal failures.
    CRC, per-node sample ownership, raw-counter wrap handling, and request/response
    time bracketing must already have been verified by the transport layer.
    A node/boot change invalidates this transaction. An outer coordinator may retry
    with a new transaction, subject to a non-resetting wall-clock user deadline.
    """
    _u64(request_start_us, 'request_start_us')
    _u64(now_us, 'now_us')
    if now_us < request_start_us:
        raise CaptureRejected('CLOCK_REVERSED')
    if now_us - request_start_us > policy.transaction_timeout_us:
        raise CaptureRejected('TRANSACTION_TIMEOUT')
    if not all(type(v) is str and v for v in
               (capture_id, gateway_session, profile_hash, calibration_hash)):
        raise CaptureRejected('MISSING_IDENTITY')
    if len(scans) < policy.min_scans:
        raise CaptureRejected('WAIT_MORE_SCANS')
    expected_identity = (capture_id, gateway_session, profile_hash, calibration_hash)
    boots: tuple[str, ...] | None = None
    last_scan: Scan | None = None
    for scan in scans:
        if (scan.capture_id, scan.gateway_session, scan.profile_hash,
            scan.calibration_hash) != expected_identity:
            raise CaptureRejected('MIXED_TRANSACTION_SESSION_OR_PROFILE')
        _u64(scan.scan_id, 'scan_id')
        _u64(scan.start_us, 'scan.start_us')
        _u64(scan.end_us, 'scan.end_us')
        if scan.scan_id == 0:
            raise CaptureRejected('INVALID_SCAN_ID')
        if not request_start_us <= scan.start_us < scan.end_us <= now_us:
            raise CaptureRejected('OLD_FUTURE_OR_REVERSED_SCAN')
        if scan.end_us - scan.start_us > policy.max_scan_span_us:
            raise CaptureRejected('SCAN_TOO_LONG')
        if scan.crc_verified is not True:
            raise CaptureRejected('UNVERIFIED_CRC')
        if len(scan.node_boots) != 6 or any(type(v) is not str or not v for v in scan.node_boots):
            raise CaptureRejected('INCOMPLETE_NODE_IDENTITIES')
        if boots is None:
            boots = scan.node_boots
        elif boots != scan.node_boots:
            raise CaptureRejected('NODE_RESTART_DURING_TRANSACTION')
        if len(scan.words) != 44 or any(type(w) is not int for w in scan.words):
            raise CaptureRejected('INVALID_WORD_LAYOUT')
        if scan.words[:3] != (FIXED, FIXED, FIXED):
            raise CaptureRejected('ROOT_NOT_FIXED_REFERENCE')
        if any(not 0 <= w < FIXED for w in scan.words[3:]):
            raise CaptureRejected('MISSING_FAULT_OR_FIXED_MEASUREMENT')
        if last_scan is not None:
            if scan.scan_id != last_scan.scan_id + 1:
                raise CaptureRejected('MISSING_OR_REPLAYED_SCAN')
            if scan.start_us <= last_scan.start_us or scan.start_us < last_scan.end_us:
                raise CaptureRejected('NONMONOTONIC_OR_OVERLAPPED_SCAN')
            if scan.start_us - last_scan.start_us > policy.max_scan_gap_us:
                raise CaptureRejected('UNOBSERVED_GAP')
        last_scan = scan
    assert last_scan is not None and boots is not None
    # Conservative support: interval from the end of the first scan to start of last.
    # No claim that every axis was acquired precisely at its scan's midpoint.
    stable_span = scans[-1].start_us - scans[0].end_us
    if stable_span < policy.stable_window_us:
        raise CaptureRejected('WAIT_STABILITY_WINDOW')
    if now_us - last_scan.start_us > policy.max_snapshot_age_us:
        raise CaptureRejected('STALE_FINAL_SCAN')
    t = [((s.start_us + s.end_us) / 2 - scans[0].start_us) / 1_000_000 for s in scans]
    tmean = sum(t) / len(t)
    denom = sum((v - tmean)**2 for v in t)
    max_range = max_slope = 0.0
    for axis in range(3, 44):
        q = _unwrap_counts([s.words[axis] for s in scans])
        span = max(q) - min(q)
        mean = sum(q) / len(q)
        slope = abs(sum((x - tmean) * (y - mean) for x, y in zip(t, q)) / denom)
        max_range, max_slope = max(max_range, span), max(max_slope, slope)
        if span > policy.peak_to_peak_deg + 1e-12 or slope > policy.max_abs_slope_deg_s + 1e-12:
            raise CaptureRejected(f'UNSTABLE_AXIS:{axis}')
    return Snapshot(capture_id, gateway_session, last_scan.scan_id,
                    last_scan.start_us, last_scan.end_us, profile_hash,
                    calibration_hash, boots, last_scan.words,
                    stable_span, max_range, max_slope)


def resolve_single_turn(
    raw_count: int, *, zero_rad: float, sign: int, ratio: float,
    lower_rad: float, upper_rad: float,
) -> float:
    """Resolve an ABSOLUTE static axis using a frozen calibration and hard limits.
    Forward relation: raw phase = (zero + sign*ratio*q) mod 2*pi.
    This simplified adapter is illustrative, not a substitute for the project's
    full calibration model. Never use previous-pose shortest delta as turn evidence.
    """
    if type(raw_count) is not int or not 0 <= raw_count < FIXED:
        raise CaptureRejected('INVALID_RAW_ANGLE')
    if sign not in (-1,1) or type(sign) is not int:
        raise CaptureRejected('INVALID_CALIBRATION_SIGN')
    if not all(math.isfinite(v) for v in (zero_rad,ratio,lower_rad,upper_rad)) or ratio <= 0 or lower_rad > upper_rad:
        raise CaptureRejected('INVALID_CALIBRATION_OR_LIMITS')
    phase=raw_count*(2*math.pi/FIXED)-zero_rad
    gain=sign*ratio
    low,high=sorted((gain*lower_rad,gain*upper_rad))
    k0=math.ceil((low-phase)/(2*math.pi)-1e-12)
    k1=math.floor((high-phase)/(2*math.pi)+1e-12)
    if k0>k1:raise CaptureRejected('OUTSIDE_MECHANICAL_LIMITS')
    if k0!=k1:raise CaptureRejected('AMBIGUOUS_PERIODIC_BRANCH_NEEDS_REFERENCE')
    return (phase+2*math.pi*k0)/gain

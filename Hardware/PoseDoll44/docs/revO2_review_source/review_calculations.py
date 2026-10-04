#!/usr/bin/env python3
"""Independent arithmetic for the Rev O review, NOT a CAD or hardware validator.

Only Python's standard library is needed. Values are explicitly transcribed
from the pinned repository or labeled proposals. No network, writes to the
repository, builds, firmware flashing, or manufacture approval.

Usage: python review_calculations.py --output review_calculations.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

COMMIT = "f59e4d3a7ea3d0940b1810702cd5e1df181e0364"


def annular_radius(ro: float, ri: float, model: str) -> float:
    if not (ro > ri >= 0):
        raise ValueError("Expected ro > ri >= 0, in metres")
    if model == "uniform_pressure":
        return (2 / 3) * (ro**3 - ri**3) / (ro**2 - ri**2)
    if model == "uniform_wear":
        return (ro + ri) / 2
    raise ValueError(f"Unsupported model: {model}")


def power_case(voltage: float, resistance_per_m: float) -> dict:
    load_w = 3.3 * (41 * .015 + 6 * .18 + 6 * .015 + 41 * .001)
    eta = .85  # original allocation assumption, not measured at either voltage
    input_w = load_w / eta
    vin = .95 * voltage
    loop_r = 2 * resistance_per_m + .06
    discriminant = vin**2 - 4 * loop_r * input_w
    if discriminant < 0:
        return {"nominal_V": voltage, "status": "NO_REAL_HIGH_VOLTAGE_SOLUTION_IN_MODEL"}
    vload = (vin + math.sqrt(discriminant)) / 2
    current = input_w / vload
    return {"nominal_V": voltage, "supply_minus_5pct_V": vin,
            "body_3V3_allocated_W": load_w, "input_allocated_W": input_w,
            "loop_ohm": loop_r, "tether_end_V": vload,
            "current_A": current, "tether_contact_loss_W": current**2 * loop_r,
            "scope": "Original lumped allocation; excludes internal branches, protection, peak/inrush, real converter efficiency"}


def epoch_counterexample() -> dict:
    """Possible task ordering, with the repository's 135-bit frame allowance.

    After an unchanged EPOCH, all six nodes handle EPOCH before queued SYNC
    and block on BOOT then ACK. G0's SYNC wins CAN arbitration. All BOOT IDs
    outrank all ACK IDs; only after a node's ACK completes does its acquisition
    start. There are no SDK delays/errors here. This is not exact bit stuffing
    or a proof that every physical device follows this schedule.
    """
    frame_us = 135 / 500_000 * 1e6
    counts = [3, 6, 9, 9, 7, 7]
    cases = []
    for i, count in enumerate(counts, 1):
        # Time measured from the completed SYNC received in each node ISR.
        delay = (6 + i) * frame_us
        span = count * 700
        cases.append({"node": f"N{i}", "ports": count,
                      "delay_from_sync_rx_us": delay, "assumed_span_us": span,
                      "end_from_sync_rx_us": delay + span,
                      "would_exceed_8000us_in_this_model": delay + span > 8000})
    return {"scope": "CONDITIONAL_SCHEDULING_COUNTEREXAMPLE_NOT_HARDWARE_RESULT",
            "frame_bits_allowance": 135, "bitrate": 500_000,
            "assumed_axis_us": 700, "rows": cases,
            "excluded": ["actual per-frame stuffed bit counts", "SDK and ISR overhead", "other feasible scheduling orders", "periodic 250ms BOOT and error traffic"]}


def run() -> dict:
    hold = .38758972532896774
    grav = .2383931502193118
    cable = .02
    rp = annular_radius(.012, .0042, "uniform_pressure")
    rw = annular_radius(.012, .0042, "uniform_wear")
    old_mass = 762.1388657751172 + 625
    # Source family() mapping applied to the 41 measured axes.
    annulus_area_mm2 = sum(n * math.pi * (ro**2 - ri**2)
                           for n, ro, ri in [(11, 8., 3.2), (16, 10., 4.2), (14, 12., 4.2)])
    plate_cases = []
    for aluminum_t in (1.5, 1.7, 1.8):
        old = annulus_area_mm2 * 1.2 * .00785
        proposed = annulus_area_mm2 * (aluminum_t * .00270 + .2 * .00785)
        plate_cases.append({"aluminum_carrier_thickness_mm": aluminum_t,
                            "steel_wear_shim_thickness_mm": .2,
                            "old_annuli_g": old, "proposed_annuli_g": proposed,
                            "annuli_only_saving_g": old - proposed,
                            "scope": "Proposal only; excludes keys, ribs, fasteners, added clutch faces and stiffness checks"})
    result = {
        "reviewed_commit": COMMIT,
        "status": "ARITHMETIC_REPRODUCED_ONLY",
        "not_executed": ["CadQuery build or BRep recheck", "KiCad ERC/DRC/routing", "ESP-IDF build or firmware runtime", "physical tests", "full-body qualification"],
        "rear_cap": {"housing_material_z_min_mm_after_cut": -7.4,
                     "cap_z_min_mm": -10., "cap_z_max_mm": -7.4,
                     "axial_thread_overlap_mm": max(0., min(4., -7.4) - max(-7.4, -10.)),
                     "scope": "Derived from compact_joint.py intervals; not a stress calculation"},
        "friction": {"source_hold_Nm": hold, "source_gravity_Nm": grav,
                     "source_cable_assumption_Nm": cable, "mu_low_assumed": .08,
                     "mu_high_assumed": .22, "effective_radius_pressure_m": rp,
                     "effective_radius_wear_m": rw,
                     "one_face_pressure_required_N": hold / (.08 * rp),
                     "two_face_pressure_required_N": hold / (2 * .08 * rp),
                     "two_face_wear_required_N": hold / (2 * .08 * rw),
                     "two_face_wear_at_350N_torque_Nm": 2 * .08 * 350 * rw,
                     "pressure_at_two_face_wear_force_MPa": hold / (2 * .08 * rw) / (math.pi * (12**2 - 4.2**2)),
                     "friction_only_hand_force_at_60mm_N": hold * (.22 / .08) / .06,
                     "lifting_hand_force_with_gravity_and_cable_at_60mm_N": (hold * (.22 / .08) + grav + cable) / .06,
                     "scope": "Conditional on source load and friction interval, not measured friction/breakaway/actual hand force"},
        "journal_clearance_sensitivity": {
            "source_diametral_clearance_mm": .06, "source_bush_length_mm": 4.6,
            "one_sided_tilt_scale_deg": math.degrees(math.atan(.06 / 4.6)),
            "proposal_diametral_clearance_mm": .03, "proposal_support_span_mm": 14,
            "proposal_tilt_scale_deg": math.degrees(math.atan(.03 / 14)),
            "scope": "Rigid shaft/bush geometric order estimate, not measured play or sensor angle error"},
        "mass": {"source_budget_g": old_mass, "excess_over_1200g": old_mass - 1200,
                 "material_proposals": plate_cases,
                 "board_material_only": {"old_area_mm2": 40 * 66,
                    "proposed_torso_board_mm": [36,48], "proposed_distal_board_mm": [26,30],
                    "proposed_area_mm2": 36*48+26*30,
                    "saving_g_per_arm_at_1p2mm_1p85density": (40*66-36*48-26*30)*1.2*.00185,
                    "scope": "Exploration dimensions, not completed layout; new connectors and harness may reverse saving"}},
        "power_24AWG_1m_allocation": [power_case(5, .0842), power_case(12, .0842)],
        "can_ordinary": {"pairs": sum(math.ceil(n/2) for n in [3,6,9,9,7,7]),
                         "frames_per_cohort": 30, "utilization": 30*135*60/500000},
        "epoch_counterexample": epoch_counterexample(),
        "catalogue_spring_example_002100": {"source": "SCHNORR 2024-02 catalogue printed p11",
            "OD_mm": 12, "ID_mm": 6.2, "thickness_mm": .5,
            "free_height_one_mm": .85, "cone_height_mm": .35,
            "catalogue_force_N_at_0p75_h0": 326,
            "four_in_series_free_height_mm": 4*.85,
            "four_in_series_height_at_catalogue_point_mm": 4*(.85-.75*.35),
            "four_in_series_mass_g": 4*.310,
            "scope": "Catalogue point and ideal series arithmetic; not spring selection approval"},
        "spi_possible_pipeline_arithmetic": {"current_frames_per_axis": 10,
            "candidate_frames_per_axis": 6, "bits_per_frame": 16, "SPI_hz": 250000,
            "current_wire_time_us": 10*16/250000*1e6,
            "candidate_wire_time_us": 6*16/250000*1e6,
            "nine_axis_wire_saving_us": 9*4*16/250000*1e6,
            "scope": "Conditional optimization hypothesis; requires authoritative SPI sequencing review and fault-equivalence tests before implementation"}
    }
    # Arithmetic sanity checks only, never hardware PASS assertions.
    assert abs(result["friction"]["one_face_pressure_required_N"] - 555.2272168867852) < 1e-9
    assert result["rear_cap"]["axial_thread_overlap_mm"] == 0
    assert result["can_ordinary"]["pairs"] == 23
    assert [r["node"] for r in result["epoch_counterexample"]["rows"] if r["would_exceed_8000us_in_this_model"]] == ["N3", "N4", "N6"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON result path")
    args = parser.parse_args()
    text = json.dumps(run(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote arithmetic-only report: {args.output}")
    else:
        print(text, end="")

if __name__ == "__main__":
    main()

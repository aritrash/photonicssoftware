"""
comparison_results.py

Updated timing and error-comparison utilities for Trine PICSIM.

Changes:
1. Structural delay model:
   photonic_delay = n_stages * (t_opt + t_det + t_elec + t_regen)
   - n_stages depends on function and pipeline depth.
   - t_opt weakly depends on wavelength.
2. TER as threshold-crossing problem with explicit decision margins.
3. CMOS delay scaling with logic depth and fan-in.

Author: Aritrash Sarkar (Trine PICSIM project)
"""

from __future__ import annotations

import math
import random
from typing import Dict, Tuple, Callable, List

import numpy as np
import matplotlib.pyplot as plt

C0 = 3e8  # speed of light (m/s)


# ---------------------------------------------------------------------------
# Parameter containers
# ---------------------------------------------------------------------------

class PhotonicTechParams:
    """
    Photonic technology parameters for structural delay and TER.

    Times are in seconds. Wavelength in meters.
    """

    def __init__(
        self,
        wavelength_m: float = 1550e-9,
        group_index_ref: float = 3.6,
        group_index_slope: float = 0.1,   # weak n_g(lambda) dependence
        lambda_ref_m: float = 1550e-9,
        stage_length_m: float = 300e-6,   # effective optical length per stage
        pd_bandwidth_hz: float = 40e9,
        elec_logic_stage_delay_s: float = 5e-12,
        regen_delay_s: float = 5e-12,
        pipeline_depth: int = 1,
    ):
        self.wavelength_m = wavelength_m
        self.group_index_ref = group_index_ref
        self.group_index_slope = group_index_slope
        self.lambda_ref_m = lambda_ref_m
        self.stage_length_m = stage_length_m
        self.pd_bandwidth_hz = pd_bandwidth_hz
        self.elec_logic_stage_delay_s = elec_logic_stage_delay_s
        self.regen_delay_s = regen_delay_s
        self.pipeline_depth = pipeline_depth


class ElectronicTechParams:
    """
    Electronic (CMOS) parameters for structural delay.

    gate_delay_base_s: base FO4-like gate delay.
    fanin_factor: simple multiplier for 3-input functions.
    """

    def __init__(
        self,
        gate_delay_base_s: float = 12e-12,
        fanin_factor: float = 1.3,
        xor_depth_factor: float = 1.5,
    ):
        self.gate_delay_base_s = gate_delay_base_s
        self.fanin_factor = fanin_factor
        self.xor_depth_factor = xor_depth_factor


# ---------------------------------------------------------------------------
# Structural delay model
# ---------------------------------------------------------------------------

def group_index_lambda(params: PhotonicTechParams, wavelength_m: float) -> float:
    """
    Simple linear model: n_g(lambda) = n_ref + slope * (lambda - lambda_ref)/lambda_ref.
    """
    delta = (wavelength_m - params.lambda_ref_m) / params.lambda_ref_m
    return params.group_index_ref + params.group_index_slope * delta


def t_opt_per_stage(params: PhotonicTechParams, wavelength_m: float | None = None) -> float:
    """
    Optical propagation + splitter + SWG per stage.

    t_opt = n_g(lambda) * L_stage / c.
    """
    lam = wavelength_m if wavelength_m is not None else params.wavelength_m
    n_g = group_index_lambda(params, lam)
    return n_g * params.stage_length_m / C0


def t_det_per_stage(params: PhotonicTechParams) -> float:
    """
    Photodiode + TIA per stage: t_det ≈ 0.35 / f_3dB.
    """
    return 0.35 / params.pd_bandwidth_hz


def t_elec_per_stage(params: PhotonicTechParams) -> float:
    """
    Electronic logic within one OEO stage.
    """
    return params.elec_logic_stage_delay_s


def t_regen_per_stage(params: PhotonicTechParams) -> float:
    """
    Polarization re-encoding and rail regeneration per stage.
    """
    return params.regen_delay_s


def n_stages_for_function(func_name: str, pipeline_depth: int) -> int:
    """
    Structural stage count as a function of the ternary function and pipeline depth.

    Unary (C/N/A/TNOT): 1 logical stage.
    Binary (TAND/TOR/TNAND/TNOR/TXOR): 1–2 logical stages.
    HA: ~2 logical stages (sum + carry).
    FA: ~3 logical stages (HA + HA + carry combine).

    Total stages = logical_stages * pipeline_depth.
    """
    fname = func_name.upper()

    if fname in {"C", "N", "A", "TNOT"}:
        logical_stages = 1
    elif fname in {"TAND", "TOR", "TNAND", "TNOR", "TXOR"}:
        logical_stages = 2
    elif fname == "HA":
        logical_stages = 2
    elif fname == "FA":
        logical_stages = 3
    else:
        logical_stages = 2

    return logical_stages * max(1, pipeline_depth)


def estimate_photonic_delay(
    func_name: str,
    pho_params: PhotonicTechParams,
    wavelength_m: float | None = None,
) -> Dict[str, float]:
    """
    Structural photonic delay:

    t_pho = n_stages * (t_opt + t_det + t_elec + t_regen)
    """
    lam = wavelength_m if wavelength_m is not None else pho_params.wavelength_m
    stages = n_stages_for_function(func_name, pho_params.pipeline_depth)

    t_opt = t_opt_per_stage(pho_params, lam)
    t_det = t_det_per_stage(pho_params)
    t_ele = t_elec_per_stage(pho_params)
    t_reg = t_regen_per_stage(pho_params)

    per_stage = t_opt + t_det + t_ele + t_reg
    total = stages * per_stage

    return {
        "n_stages": stages,
        "t_opt": t_opt,
        "t_det": t_det,
        "t_elec": t_ele,
        "t_regen": t_reg,
        "per_stage": per_stage,
        "total": total,
    }


def logic_depth_and_fanin(func_name: str) -> Tuple[int, int]:
    """
    Very simple estimates of logic depth and fan-in for CMOS reference.

    Returns (depth, fanin_max).
    """
    fname = func_name.upper()

    if fname in {"C", "N", "A", "TNOT"}:
        return 1, 1
    elif fname in {"TAND", "TOR"}:
        return 1, 2
    elif fname in {"TNAND", "TNOR"}:
        return 2, 2
    elif fname == "TXOR":
        # XOR-like: deeper network
        return 3, 2
    elif fname == "HA":
        # XOR + consensus network
        return 4, 3
    elif fname == "FA":
        # Two HAs + carry combine
        return 6, 3
    else:
        return 2, 2


def estimate_electronic_delay(
    func_name: str,
    elec_params: ElectronicTechParams,
) -> float:
    """
    CMOS delay with simple scaling:

    t_elec = depth * gate_delay_base * fanin_factor^(fanin_max-1) * extra_xor_factor
    """
    depth, fanin_max = logic_depth_and_fanin(func_name)
    base = elec_params.gate_delay_base_s
    fanin_mult = elec_params.fanin_factor ** max(0, fanin_max - 1)

    fname = func_name.upper()
    xor_mult = elec_params.xor_depth_factor if fname in {"TXOR", "HA", "FA"} else 1.0

    return depth * base * fanin_mult * xor_mult


# ---------------------------------------------------------------------------
# TER as threshold-crossing
# ---------------------------------------------------------------------------

CANONICAL_ANGLES_DEG = {
    -1: 240.0,
    0: 0.0,
    +1: 120.0,
}

DECISION_BOUNDARIES_DEG = {
    # between -1 and 0
    "b_minus_zero": 300.0,  # halfway between 240 and 0 (mod 360)
    # between 0 and +1
    "b_zero_plus": 60.0,    # halfway between 0 and 120
    # between +1 and -1
    "b_plus_minus": 180.0,  # halfway between 120 and 240
}


def canonical_encoder_trit_to_angle(t: int) -> float:
    return CANONICAL_ANGLES_DEG[t]


def decode_with_boundaries(theta_deg: float) -> int:
    """
    Decode using fixed sector boundaries at ±60° from each canonical angle.

    - Sector around 0°  : (-60°, +60°)  => trit 0
    - Sector around 120°: (60°, 180°)   => trit +1
    - Sector around 240°: (180°, 300°)  => trit -1
    """
    theta = theta_deg % 360.0

    if -60.0 <= theta < 60.0 or theta >= 300.0:
        return 0
    elif 60.0 <= theta < 180.0:
        return +1
    else:
        return -1


def simulate_trit_with_decision_margin(
    t_in: int,
    angle_noise_std_deg: float,
    decision_margin_deg: float,
) -> bool:
    """
    Trit error if noisy angle crosses decision margin from its ideal sector.

    decision_margin_deg is the allowed deviation from the canonical angle
    before we consider the symbol unsafe.
    """
    theta_ideal = CANONICAL_ANGLES_DEG[t_in]
    theta_noisy = random.gauss(theta_ideal, angle_noise_std_deg)

    # Compute minimal angular deviation
    diff = abs((theta_noisy - theta_ideal + 180.0) % 360.0 - 180.0)

    # If deviation exceeds decision margin, we treat it as an error
    if diff > decision_margin_deg:
        return True

    # Alternatively, one can decode and compare:
    t_out = decode_with_boundaries(theta_noisy)
    return t_out != t_in


def estimate_TER(
    angle_noise_std_deg: float = 2.0,
    decision_margin_deg: float = 45.0,
    trials: int = 10_000,
) -> float:
    """
    Estimate TER by counting crossing of decision boundaries.

    Error if |theta_noisy - theta_ideal| > decision_margin OR decoded trit differs.
    """
    errors = 0
    for _ in range(trials):
        t_in = random.choice([-1, 0, +1])
        if simulate_trit_with_decision_margin(t_in, angle_noise_std_deg, decision_margin_deg):
            errors += 1
    return errors / float(trials)


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------

def plot_delay_comparison(
    func_name: str,
    pho_params: PhotonicTechParams,
    elec_params: ElectronicTechParams,
    wavelengths_m: np.ndarray,
) -> plt.Figure:
    """
    Delay vs wavelength using the structural photonic delay model.
    """
    pho_delays = []
    for lam in wavelengths_m:
        d = estimate_photonic_delay(func_name, pho_params, wavelength_m=lam)["total"]
        pho_delays.append(d)
    pho_delays = np.array(pho_delays)

    elec_delay = estimate_electronic_delay(func_name, elec_params)

    fig, ax = plt.subplots()
    ax.plot(wavelengths_m * 1e9, pho_delays * 1e12, label="Photonic (ps)")
    ax.hlines(
        elec_delay * 1e12,
        wavelengths_m[0] * 1e9,
        wavelengths_m[-1] * 1e9,
        colors="r",
        linestyles="--",
        label="Electronic (ps)",
    )

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Estimated delay (ps)")
    ax.set_title(f"Delay comparison for {func_name}")
    ax.legend()
    ax.grid(True)
    return fig


def plot_TER_vs_angle_noise(
    noise_std_deg_list: List[float],
    decision_margin_deg: float = 45.0,
    trials: int = 5_000,
) -> plt.Figure:
    """
    TER vs polarization angle noise std using the threshold-crossing model.
    """
    ters = []
    for std in noise_std_deg_list:
        ter = estimate_TER(
            angle_noise_std_deg=std,
            decision_margin_deg=decision_margin_deg,
            trials=trials,
        )
        ters.append(ter)

    fig, ax = plt.subplots()
    ax.plot(noise_std_deg_list, ters, marker="o")
    ax.set_xlabel("Polarization angle noise std (deg)")
    ax.set_ylabel("TER")
    ax.set_title("Trit Error Rate vs polarization angle noise")
    ax.grid(True)
    return fig


# ---------------------------------------------------------------------------
# Convenience wrapper for GUI
# ---------------------------------------------------------------------------

def compare_function_delays(
    func_name: str,
    pho_params: PhotonicTechParams | None = None,
    elec_params: ElectronicTechParams | None = None,
) -> Tuple[Dict[str, float], float]:
    """
    Return (photonic_delay_components, electronic_total_delay).
    """
    if pho_params is None:
        pho_params = PhotonicTechParams()
    if elec_params is None:
        elec_params = ElectronicTechParams()

    pho = estimate_photonic_delay(func_name, pho_params)
    elec = estimate_electronic_delay(func_name, elec_params)
    return pho, elec

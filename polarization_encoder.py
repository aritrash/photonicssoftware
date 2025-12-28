# polarization_encoding.py

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple

from photology_simulator.ternaryops import Trit


@dataclass(frozen=True)
class PolarizationState:
    """
    Simple container for a polarization state.

    angle_deg : linear polarization angle (deg) relative to reference
                (0° = parallel to laser E-field, i.e. trit 0).
    jones     : normalized Jones vector (complex 2D tuple) in (Ex, Ey) basis.
    """
    angle_deg: float
    jones: Tuple[complex, complex]


# ---------- Core mappings: Trit ↔ angle ----------

def trit_to_angle_deg(trit: Trit) -> float:
    """
    Map trit to linear polarization angle (deg) relative to laser E-field:
        0   -> 0°
        +1  -> 120°
        -1  -> 240°
    """
    if trit is Trit.ZERO:
        return 0.0
    if trit is Trit.PLUS:
        return 120.0
    return 240.0


def angle_deg_to_trit(angle_deg: float) -> Trit:
    """
    Map an arbitrary angle (deg) to the nearest trit state.
    Uses nearest of {0°, 120°, 240°}.

    This is a logical decode; physical decode via triple-channel
    goes through transmission coefficients instead.
    """
    # Normalize to [0, 360)
    a = angle_deg % 360.0
    candidates = {
        Trit.ZERO: 0.0,
        Trit.PLUS: 120.0,
        Trit.MINUS: 240.0,
    }
    # Find nearest canonical angle
    best_trit = None
    best_dist = None
    for t, ang in candidates.items():
        # circular distance
        d = min(abs(a - ang), 360.0 - abs(a - ang))
        if best_dist is None or d < best_dist:
            best_trit = t
            best_dist = d
    return best_trit  # type: ignore[return-value]


# ---------- Angle ↔ Jones vector for linear polarization ----------

def angle_deg_to_jones(angle_deg: float) -> Tuple[complex, complex]:
    """
    Convert a linear polarization angle (deg) in the x–y basis to a normalized
    Jones vector (Ex, Ey).

    For linear polarization at angle θ w.r.t. x (reference axis):
        |E> = (cos θ, sin θ)

    Overall phase is irrelevant, so we use real components only.[web:111][web:115]
    """
    theta_rad = math.radians(angle_deg)
    ex = math.cos(theta_rad)
    ey = math.sin(theta_rad)

    # Normalize (should already be unit norm, but normalize defensively)
    norm = math.sqrt(ex * ex + ey * ey)
    if norm == 0:
        return 1.0 + 0j, 0.0 + 0j
    return complex(ex / norm, 0.0), complex(ey / norm, 0.0)


def jones_to_angle_deg(jones: Tuple[complex, complex]) -> float:
    """
    Estimate linear polarization angle (deg) from a Jones vector,
    assuming it represents (approximately) linear polarization.

    We use:
        θ = atan2(|Ey|, |Ex|)

    This discards phase; for strictly linear states this is fine.[web:112][web:124]
    """
    ex, ey = jones
    ax = abs(ex)
    ay = abs(ey)
    if ax == 0 and ay == 0:
        return 0.0
    theta_rad = math.atan2(ay, ax)
    return math.degrees(theta_rad)


# ---------- Trit ↔ PolarizationState convenience ----------

def encode_trit(trit: Trit) -> PolarizationState:
    """
    Encode a trit as a PolarizationState:
        Trit -> (angle, Jones vector)
    """
    angle = trit_to_angle_deg(trit)
    jones = angle_deg_to_jones(angle)
    return PolarizationState(angle_deg=angle, jones=jones)


def decode_trit_from_angle(angle_deg: float) -> Trit:
    """
    Decode trit directly from a linear polarization angle.
    """
    return angle_deg_to_trit(angle_deg)


def decode_trit_from_jones(jones: Tuple[complex, complex]) -> Trit:
    """
    Decode trit from a Jones vector by:
        Jones -> angle -> nearest trit.
    """
    angle = jones_to_angle_deg(jones)
    return angle_deg_to_trit(angle)


# ---------- Stokes parameters / Poincaré sphere ----------

def jones_to_stokes(jones: Tuple[complex, complex]) -> Tuple[float, float, float, float]:
    """
    Compute Stokes parameters (S0, S1, S2, S3) from a Jones vector (Ex, Ey).[web:125][web:119]

    For Jones vector E = (Ex, Ey):
        S0 = |Ex|^2 + |Ey|^2
        S1 = |Ex|^2 - |Ey|^2
        S2 = 2 Re(Ex * Ey*)
        S3 = 2 Im(Ex * Ey*)
    """
    ex, ey = jones
    sx = abs(ex) ** 2
    sy = abs(ey) ** 2
    s0 = sx + sy
    s1 = sx - sy
    s2 = 2.0 * (ex * ey.conjugate()).real
    s3 = 2.0 * (ex * ey.conjugate()).imag
    return s0, s1, s2, s3


def stokes_to_poincare_coords(
    stokes: Tuple[float, float, float, float]
) -> Tuple[float, float, float]:
    """
    Normalize Stokes parameters to get a point (x, y, z) on the Poincaré sphere.[web:125][web:122]

    For fully polarized light:
        (x, y, z) = (S1/S0, S2/S0, S3/S0)
    """
    s0, s1, s2, s3 = stokes
    if s0 == 0:
        return 0.0, 0.0, 0.0
    return s1 / s0, s2 / s0, s3 / s0


def trit_to_poincare_coords(trit: Trit) -> Tuple[float, float, float]:
    """
    Direct helper: Trit -> Poincaré sphere coordinates.
    """
    state = encode_trit(trit)
    stokes = jones_to_stokes(state.jones)
    return stokes_to_poincare_coords(stokes)


if __name__ == "__main__":
    # Quick self-check
    for t in (Trit.MINUS, Trit.ZERO, Trit.PLUS):
        state = encode_trit(t)
        stokes = jones_to_stokes(state.jones)
        x, y, z = stokes_to_poincare_coords(stokes)
        print(f"Trit {t}: angle={state.angle_deg:.1f} deg, "
              f"Jones={state.jones}, "
              f"Poincaré=({x:.3f}, {y:.3f}, {z:.3f})")

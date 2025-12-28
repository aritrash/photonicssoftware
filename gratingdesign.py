# gratingdesign.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Tuple

import math


# ---------- Material model ----------

@dataclass(frozen=True)
class Material:
    name: str
    # Simple scalar refractive index at the operating wavelength.
    # Later you can replace this with a dispersion model.
    n: float


# Very rough representative indices around 1.55 µm; replace with
# values from refractiveindex.info or your own fits as needed.[web:74][web:85][web:81][web:90]
INTRINSIC_SI = Material(name="Si", n=3.597)
SILICON_NITRIDE = Material(name="SiN", n=2.00)


def get_material(name: Literal["Si", "SiN"]) -> Material:
    if name == "Si":
        return INTRINSIC_SI
    if name == "SiN":
        return SILICON_NITRIDE
    raise ValueError(f"Unsupported material: {name}")


# ---------- Effective-medium helpers ----------

def effective_index_te(
    n_core: float,
    n_clad: float,
    duty_cycle: float,
) -> float:
    """
    First-order EMT for TE-like polarization of a 1D subwavelength grating:
        n_eff_TE^2 ≈ f * n_core^2 + (1 - f) * n_clad^2
    where f is duty cycle (ridge width / period).[web:66][web:63][web:134]
    """
    f = duty_cycle
    n2 = f * (n_core ** 2) + (1.0 - f) * (n_clad ** 2)
    return math.sqrt(n2)


def effective_index_tm(
    n_core: float,
    n_clad: float,
    duty_cycle: float,
) -> float:
    """
    First-order EMT for TM-like polarization of a 1D subwavelength grating:
        1 / n_eff_TM^2 ≈ f / n_core^2 + (1 - f) / n_clad^2.[web:66][web:63][web:132]
    """
    f = duty_cycle
    denom = f / (n_core ** 2) + (1.0 - f) / (n_clad ** 2)
    n2 = 1.0 / denom
    return math.sqrt(n2)


# ---------- Design algorithm ----------

@dataclass(frozen=True)
class GratingDesign:
    wavelength_nm: float
    material: str
    n_core: float
    n_clad: float
    period_nm: float
    slit_width_nm: float
    duty_cycle: float
    # Optional: store effective indices at the chosen duty cycle
    n_eff_te: float
    n_eff_tm: float
    fom: float  # |n_eff_TE - n_eff_TM| for reference


def design_grating(
    wavelength_nm: float,
    material_name: Literal["Si", "SiN"],
    n_clad: float = 1.44,
    subwavelength_factor: float = 6.0,
    duty_cycle_min: float = 0.1,
    duty_cycle_max: float = 0.9,
    duty_cycle_step: float = 0.05,
) -> GratingDesign:
    """
    Design a simple subwavelength grating for polarization discrimination
    at a given wavelength and material.

    Algorithm:
      1) Choose period Λ = λ / subwavelength_factor (Λ << λ ensures only 0th order).[web:63][web:135]
      2) Sweep duty cycle f in [duty_cycle_min, duty_cycle_max] with given step.
      3) For each f, compute n_eff_TE and n_eff_TM via EMT.
      4) Choose f* maximizing |n_eff_TE - n_eff_TM| as a crude polarization-contrast FOM.[web:61][web:135]
      5) Output Λ, slit width w = f* Λ, duty cycle f*.

    Parameters
    ----------
    wavelength_nm : float
        Laser wavelength in nm (e.g., 1550).
    material_name : "Si" or "SiN"
        Core grating material.
    n_clad : float
        Cladding refractive index (e.g., silica ~1.44, air ~1.0).
    subwavelength_factor : float
        Λ = λ / subwavelength_factor; larger factor => smaller period.
    duty_cycle_min, duty_cycle_max, duty_cycle_step : float
        Sweep range and resolution for duty cycle f.

    Returns
    -------
    GratingDesign
        Dataclass with chosen period, slit width, duty cycle, and EMT-derived indices.
    """
    if wavelength_nm <= 0:
        raise ValueError("wavelength_nm must be positive")
    if not (0.0 < duty_cycle_min < duty_cycle_max <= 1.0):
        raise ValueError("duty_cycle range must be within (0, 1] and min < max")
    if duty_cycle_step <= 0:
        raise ValueError("duty_cycle_step must be positive")

    material = get_material(material_name)
    n_core = material.n

    # 1) Choose subwavelength period
    period_nm = wavelength_nm / subwavelength_factor

    # 2–4) Sweep duty cycle and maximize |n_eff_TE - n_eff_TM|
    best_f = None
    best_fom = -1.0
    best_te = 0.0
    best_tm = 0.0

    f = duty_cycle_min
    while f <= duty_cycle_max + 1e-9:
        n_te = effective_index_te(n_core, n_clad, f)
        n_tm = effective_index_tm(n_core, n_clad, f)
        fom = abs(n_te - n_tm)  # simple polarization contrast metric.[web:61][web:135]

        if fom > best_fom:
            best_fom = fom
            best_f = f
            best_te = n_te
            best_tm = n_tm

        f += duty_cycle_step

    if best_f is None:
        # Should not happen with valid parameters
        raise RuntimeError("Duty cycle sweep failed to find a valid design.")

    slit_width_nm = best_f * period_nm

    return GratingDesign(
        wavelength_nm=wavelength_nm,
        material=material.name,
        n_core=n_core,
        n_clad=n_clad,
        period_nm=period_nm,
        slit_width_nm=slit_width_nm,
        duty_cycle=best_f,
        n_eff_te=best_te,
        n_eff_tm=best_tm,
        fom=best_fom,
    )


if __name__ == "__main__":
    # Quick self-check
    design = design_grating(
        wavelength_nm=1550.0,
        material_name="Si",
        n_clad=1.44,
    )
    print(design)

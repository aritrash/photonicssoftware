# trichanneldetector.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

import math

from photology_simulator.ternaryops import Trit
from photology_simulator.polarization_encoder import (
    PolarizationState,
    trit_to_angle_deg,
)


@dataclass(frozen=True)
class ChannelConfig:
    """
    Configuration for one detection channel.

    pass_axis_deg : analyzer/grating pass axis (deg) relative to laser E-field.
                    For your ternary system, typical values are 0°, 120°, 240°.
    efficiency    : overall transmission scaling factor (0..1), to model
                    non-ideal gratings or different materials.
    """
    pass_axis_deg: float
    efficiency: float = 1.0


@dataclass(frozen=True)
class ChannelResponse:
    """
    Response of one channel for a given input state.

    intensity : transmitted intensity (arbitrary units).
    """
    intensity: float


@dataclass(frozen=True)
class TripleChannelResult:
    """
    Result of triple-channel detection for a given input polarization.

    intensities : mapping Trit -> ChannelResponse
    decoded     : Trit chosen as argmax intensity
    """
    intensities: Dict[Trit, ChannelResponse]
    decoded: Trit


# ---------- Malus-law-based model ----------

def _malus_intensity(
    input_angle_deg: float,
    pass_axis_deg: float,
    input_intensity: float,
    efficiency: float,
) -> float:
    """
    Malus law:
        I = efficiency * I0 * cos^2(theta_diff)

    where theta_diff is the angle between input polarization and analyzer axis.[web:146][web:120][web:155]
    """
    theta = math.radians(input_angle_deg - pass_axis_deg)
    cos2 = math.cos(theta) ** 2
    return efficiency * input_intensity * cos2


# ---------- Triple-channel detector ----------

@dataclass(frozen=True)
class TripleChannelDetector:
    """
    Triple-channel polarization detector for ternary logic.

    Typically configured with three channels:
        channel for Trit.ZERO  -> pass axis ~ 0°
        channel for Trit.PLUS  -> pass axis ~ 120°
        channel for Trit.MINUS -> pass axis ~ 240°
    """

    # Mapping from logical state to channel configuration
    channels: Dict[Trit, ChannelConfig]
    # Reference input intensity I0 (can be 1.0; only ratios matter)
    input_intensity: float = 1.0

    @classmethod
    def default(cls) -> "TripleChannelDetector":
        """
        Default configuration:
            0   channel at 0°
            +1  channel at 120°
            -1  channel at 240°
        All with efficiency 1.0.
        """
        return cls(
            channels={
                Trit.ZERO: ChannelConfig(pass_axis_deg=0.0, efficiency=1.0),
                Trit.PLUS: ChannelConfig(pass_axis_deg=120.0, efficiency=1.0),
                Trit.MINUS: ChannelConfig(pass_axis_deg=240.0, efficiency=1.0),
            },
            input_intensity=1.0,
        )

    def detect_from_angle(self, angle_deg: float) -> TripleChannelResult:
        """
        Given an input polarization angle (deg), compute channel intensities via Malus law
        and decode the trit as argmax intensity.
        """
        intensities: Dict[Trit, ChannelResponse] = {}
        for trit, cfg in self.channels.items():
            I = _malus_intensity(
                input_angle_deg=angle_deg,
                pass_axis_deg=cfg.pass_axis_deg,
                input_intensity=self.input_intensity,
                efficiency=cfg.efficiency,
            )
            intensities[trit] = ChannelResponse(intensity=I)

        # Decode: choose trit with maximum intensity
        decoded = max(
            intensities.items(),
            key=lambda item: item[1].intensity,
        )[0]

        return TripleChannelResult(intensities=intensities, decoded=decoded)

    def detect_from_state(self, state: PolarizationState) -> TripleChannelResult:
        """
        Convenience wrapper: take a PolarizationState (with angle_deg)
        and run detection.
        """
        return self.detect_from_angle(state.angle_deg)

    def detect_from_trit(self, trit: Trit) -> TripleChannelResult:
        """
        Convenience wrapper for the 'ideal round-trip' path:
            Trit -> angle -> triple-channel detection -> decoded Trit
        """
        angle = trit_to_angle_deg(trit)
        return self.detect_from_angle(angle)


if __name__ == "__main__":
    # Quick self-check
    detector = TripleChannelDetector.default()
    for t in (Trit.MINUS, Trit.ZERO, Trit.PLUS):
        result = detector.detect_from_trit(t)
        I_minus = result.intensities[Trit.MINUS].intensity
        I_zero = result.intensities[Trit.ZERO].intensity
        I_plus = result.intensities[Trit.PLUS].intensity
        print(
            f"Input {t}: "
            f"I(-1)={I_minus:.3f}, I(0)={I_zero:.3f}, I(+1)={I_plus:.3f} "
            f"=> decoded {result.decoded}"
        )

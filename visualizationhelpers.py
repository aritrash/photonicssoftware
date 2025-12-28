# visualizationhelpers.py

from __future__ import annotations
from typing import Tuple

import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (needed for 3D)

from ternaryops import Trit
from polarization_encoder import (
    PolarizationState,
    trit_to_angle_deg,
    trit_to_poincare_coords,
    jones_to_stokes,
)


# Simple color mapping for plotting
TRIT_COLORS = {
    Trit.MINUS: "red",
    Trit.ZERO: "blue",
    Trit.PLUS: "green",
}


# ---------- 1) Angle-on-circle 3D plot ----------

def create_angle_circle_figure(
    output_state: PolarizationState,
) -> plt.Figure:
    """
    Create a 3D figure showing the unit circle in the x–y plane and the
    three canonical ternary states plus the current output state as points.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Unit circle in x–y plane
    theta_vals = [math.radians(t) for t in range(0, 361, 5)]
    xs = [math.cos(t) for t in theta_vals]
    ys = [math.sin(t) for t in theta_vals]
    zs = [0.0 for _ in theta_vals]
    ax.plot(xs, ys, zs, "k-", linewidth=1.0)

    # Canonical ternary states on the circle
    for trit, color in TRIT_COLORS.items():
        ang_deg = trit_to_angle_deg(trit)
        ang_rad = math.radians(ang_deg)
        x = math.cos(ang_rad)
        y = math.sin(ang_rad)
        ax.scatter(x, y, 0.0, color=color, s=40, label=str(trit))

    # Output state point
    out_ang_rad = math.radians(output_state.angle_deg)
    out_x = math.cos(out_ang_rad)
    out_y = math.sin(out_ang_rad)
    ax.scatter(out_x, out_y, 0.0, color="black", s=80, marker="*", label="Output")

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_title("Polarization angle on unit circle")
    ax.set_box_aspect((1, 1, 0.5))

    # Optional: show legend outside
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.0))

    return fig


# ---------- 2) Poincaré sphere 3D plot ----------

def _plot_unit_sphere(ax):
    """Draw a wireframe unit sphere on the given 3D axis."""
    u = [i * math.pi / 30 for i in range(0, 31)]  # 0..pi
    v = [i * 2 * math.pi / 30 for i in range(0, 31)]  # 0..2pi
    xs = []
    ys = []
    zs = []
    for uu in u:
        row_x = []
        row_y = []
        row_z = []
        for vv in v:
            row_x.append(math.cos(vv) * math.sin(uu))
            row_y.append(math.sin(vv) * math.sin(uu))
            row_z.append(math.cos(uu))
        xs.append(row_x)
        ys.append(row_y)
        zs.append(row_z)
    ax.plot_wireframe(xs, ys, zs, color="lightgray", linewidth=0.5)


def create_poincare_figure(
    output_trit: Trit,
) -> plt.Figure:
    """
    Create a 3D figure showing the Poincaré sphere with the three canonical
    ternary states and the current output state.

    Uses Stokes / Poincaré mapping from polarization_encoding.[web:125][web:122]
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    _plot_unit_sphere(ax)

    # Canonical ternary states
    for trit, color in TRIT_COLORS.items():
        x, y, z = trit_to_poincare_coords(trit)
        ax.scatter(x, y, z, color=color, s=40, label=str(trit))

    # Output state (could be one of the canonical ones, but plotted larger)
    out_x, out_y, out_z = trit_to_poincare_coords(output_trit)
    ax.scatter(out_x, out_y, out_z, color="black", s=80, marker="*", label="Output")

    ax.set_xlabel("S1 / S0")
    ax.set_ylabel("S2 / S0")
    ax.set_zlabel("S3 / S0")
    ax.set_title("Poincaré sphere")

    ax.set_box_aspect((1, 1, 1))
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.0))

    return fig


# ---------- 3) 2D Jones-vector plot ----------

def create_jones_figure(
    output_state: PolarizationState,
) -> plt.Figure:
    """
    Create a 2D figure representing the Jones vector components.
    For v1, plot magnitudes and phases of Ex and Ey as two subplots.
    """
    ex, ey = output_state.jones

    mag_ex = abs(ex)
    mag_ey = abs(ey)
    phase_ex = math.degrees(math.atan2(ex.imag, ex.real))
    phase_ey = math.degrees(math.atan2(ey.imag, ey.real))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))

    # Magnitudes
    ax1.bar(["|Ex|", "|Ey|"], [mag_ex, mag_ey], color=["tab:blue", "tab:orange"])
    ax1.set_ylim(0, max(mag_ex, mag_ey, 1.0) * 1.1)
    ax1.set_title("Jones magnitudes")
    ax1.set_ylabel("Amplitude")

    # Phases
    ax2.bar(["arg(Ex)", "arg(Ey)"], [phase_ex, phase_ey], color=["tab:blue", "tab:orange"])
    ax2.set_ylim(-180, 180)
    ax2.set_title("Jones phases")
    ax2.set_ylabel("Phase (deg)")

    fig.suptitle("Jones vector representation")

    fig.tight_layout()
    return fig


# ---------- Convenience for GUI ----------

def create_all_output_figures(
    output_trit: Trit,
    output_state: PolarizationState,
) -> Tuple[plt.Figure, plt.Figure, plt.Figure]:
    """
    Convenience wrapper: given logical output (trit) and its PolarizationState,
    return (angle-circle fig, Poincaré fig, Jones fig).
    """
    fig_angle = create_angle_circle_figure(output_state)
    fig_poincare = create_poincare_figure(output_trit)
    fig_jones = create_jones_figure(output_state)
    return fig_angle, fig_poincare, fig_jones


if __name__ == "__main__":
    # Simple smoke test
    from polarization_encoder import encode_trit

    for t in (Trit.MINUS, Trit.ZERO, Trit.PLUS):
        state = encode_trit(t)
        fig1 = create_angle_circle_figure(state)
        fig2 = create_poincare_figure(t)
        fig3 = create_jones_figure(state)
        plt.show()

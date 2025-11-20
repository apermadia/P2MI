import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# ===========================
# DASHBOARD DATA BUFFERS
# ===========================
max_samples = 200  # history window length

times = deque(maxlen=max_samples)
arc_history = deque(maxlen=max_samples)
grc_history = deque(maxlen=max_samples)

# ===========================
# COLOR MAP FOR RISK LEVELS
# ===========================


def risk_color(level):
    """Return color based on risk level."""
    if level <= 1:
        return "green"
    elif level == 2:
        return "yellow"
    elif level == 3:
        return "orange"
    elif level >= 4:
        return "red"
    return "black"  # fallback


# ===========================
# FIGURE LAYOUT
# ===========================
plt.style.use("ggplot")
fig = plt.figure(figsize=(12, 7))

# ARC plot (top left)
ax_arc = plt.subplot2grid((3, 2), (0, 0))
ax_arc.set_title("ARC Plot")

# GRC plot (top right)
ax_grc = plt.subplot2grid((3, 2), (0, 1))
ax_grc.set_title("GRC Plot")

# Reason for ARC (middle left)
ax_arc_reason = plt.subplot2grid((3, 2), (1, 0))
ax_arc_reason.axis("off")

# Population Density (middle right) (TODO)
ax_pop = plt.subplot2grid((3, 2), (1, 1))
ax_pop.axis("off")

# Current ARC level (bottom left)
ax_arc_level = plt.subplot2grid((3, 2), (2, 0))
ax_arc_level.axis("off")

# Current GRC level (bottom right)
ax_grc_level = plt.subplot2grid((3, 2), (2, 1))
ax_grc_level.axis("off")


# =======================================
# UPDATE FUNCTION (CALLED EACH NEW SAMPLE)
# =======================================
def update_dashboard(t_now, arc, grc, reason_text, arc_label):
    # Append data
    times.append(t_now)
    arc_history.append(arc)
    grc_history.append(grc)

    # ----- ARC Plot -----
    ax_arc.clear()
    ax_arc.plot(times, arc_history, color=risk_color(arc))
    ax_arc.set_title("ARC Plot")
    ax_arc.set_ylabel("ARC Level")
    ax_arc.set_ylim(0, 5)  # modify if different scale

    # ----- GRC Plot -----
    ax_grc.clear()
    ax_grc.plot(times, grc_history, color=risk_color(grc))
    ax_grc.set_title("GRC Plot")
    ax_grc.set_ylabel("GRC Level")
    ax_grc.set_ylim(0, 10)  # modify if different scale

    # ----- ARC Reason -----
    ax_arc_reason.clear()
    ax_arc_reason.axis("off")
    ax_arc_reason.text(0.5, 0.5, f"Reason:\n{reason_text}",
                       ha="center", va="center", fontsize=10)

    # ----- Population Density (TODO) -----
    ax_pop.clear()
    ax_pop.axis("off")
    ax_pop.text(0.5, 0.5,
                f"Population Density:\n[TODO: add pop density]",
                ha="center", va="center", fontsize=10)

    # ----- Current ARC Level -----
    ax_arc_level.clear()
    ax_arc_level.axis("off")
    ax_arc_level.text(0.5, 0.5,
                      f"Current ARC Level = {arc_label}",
                      ha="center", va="center", fontsize=12,
                      fontweight="bold", color=risk_color(arc))

    # ----- Current GRC Level -----
    ax_grc_level.clear()
    ax_grc_level.axis("off")
    ax_grc_level.text(0.5, 0.5,
                      f"Current GRC Level = {grc}",
                      ha="center", va="center", fontsize=12,
                      fontweight="bold", color=risk_color(grc))

    # Redraw Dashboard
    plt.pause(0.001)

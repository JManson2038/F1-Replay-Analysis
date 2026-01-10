
import os
import fastf1 as f1
from fastf1.core import Laps
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider



os.makedirs('cache', exist_ok=True)
f1.Cache.enable_cache('cache')
driver_teams = {}



TEAM_COLORS = {
    'Ferrari': '#FF2800',           # Red
    'Red Bull Racing': '#3671C6',  # Blue
    'Mercedes': '#6CD3BF',          # Silver/Turquoise
    'McLaren': '#FF8000',           # Papaya Orange
    'Alpine': '#FF87BC',            # Pink
    'Aston Martin': '#00665E',      # British Racing Green
    'Williams': '#005AFF',          # Blue
    'Cadillac': '#000000',          # Black
    'Haas F1 Team':'#9C9FA2',      # White/Red/Black (using white as base)
    'AlphaTauri': '#2B4562',        # Navy Blue
    'Kick Sauber': '#52C41A',            # Green
    'Racing Bulls': '#FDD900',      # Yellow
    'alfa romeo':'#972738'          #Red
                  
}
LINE_STYLES = ['-', '--']
SECTOR_MARKERS = ['o', 's', '^']

mode = input("Choose the mode: 'LAP' for lap times or 'SECTOR' for sector time: ").upper().strip()
if mode not in {"LAP", "SECTOR"}:
    print("Invalid mode")
    exit()
    
year = input("Enter the year: ")
round_number = input("Enter the Round number (1-24): ")
type_of_session = input("Enter the type of session (R, Q, P): ").upper()


if not year.isdigit():
    print("Invalid year")
    exit()
if not round_number.isdigit():
    print("Invalid round number")
    exit()
if type_of_session not in {"R", "Q", "P", "FP1", "FP2", "FP3", "SQ"}:
    print("Invalid session type")
    exit()

year = int(year)
round_number = int(round_number)
session = f1.get_session(year, round_number, type_of_session)
session.load()

laps = session.laps
drivers_code = ','.join(sorted(laps['Driver'].unique()))
print(f"Available driver codes: {drivers_code}")
drivers_input = input("Enter the drivers like this: 'HAM,NOR,VER' or 'ALL': ").upper()
if drivers_input == "ALL":
    drivers = sorted(laps["Driver"].unique().tolist())
    print(f"Using all drivers: {', '.join(drivers)}")
else:
    drivers = [d.strip() for d in drivers_input.split(",")]
    available = set(laps["Driver"].unique())
    if not all(d in available for d in drivers):
        print("Invalid driver code entered")
        print("Available drivers:", ", ".join(sorted(available)))
        exit()




REPLAY_MODE = input(
    "Replay mode: 'FASTEST' or 'RACE': "
).upper().strip()

if REPLAY_MODE not in {"FASTEST", "RACE"}:
    print("Invalid replay mode")
    exit()


# Track Animation

fig1, ax1 = plt.subplots(figsize=(8, 8))
ax1.set_title("F1 Lap Replay")
ax1.set_aspect('equal')
plt.subplots_adjust(bottom=0.25, right=0.78)


# Collect telemetry for all drivers
telemetry_data = {}
points = {}
lines = {}
SHOW_TRAILS = False  #  toggle trails ON/OFF
FPS = 30

for drv in drivers:
    drv_laps = laps.pick_driver(drv)
    tel_list = []
    offset = 0.0
    if REPLAY_MODE == "FASTEST":
        lap = drv_laps.pick_fastest()
        if lap is None:
            continue
        t = lap.get_telemetry().dropna(subset=["X", "Y", "Time"])
        t["t"] = t["Time"].dt.total_seconds()
        tel_list.append(t)
    else:
        for _, lap in drv_laps.iterlaps():
            try:
                t = lap.get_telemetry().dropna(subset=["X", "Y", "Time"])
            except:
                    continue  # skip if telemetry is missing entirely
    
            if t.empty:
                    continue  # skip if no telemetry at all
    
    t["t"] = t["Time"].dt.total_seconds() + offset
    offset = t["t"].iloc[-1]
    tel_list.append(t)

    if not tel_list:
        print(f"Skipping {drv} (no telemetry)")
        continue

    tel = pd.concat(tel_list, ignore_index=True)

    # Normalize time
    tel["t"] -= tel["t"].iloc[0]

    # Distance
    dx = tel["X"].diff()
    dy = tel["Y"].diff()
    tel["dist"] = (dx**2 + dy**2).pow(0.5).fillna(0).cumsum()

    # Lap detection
    lap_starts = [0.0]
    for i in range(1, len(tel)):
        if tel["t"].iloc[i] - tel["t"].iloc[i - 1] > 20:
            lap_starts.append(tel["t"].iloc[i])
    tel.attrs["lap_starts"] = lap_starts

    telemetry_data[drv] = tel



all_tel = pd.concat(telemetry_data.values())
# CLEAN TRACK DRAWING
ref_driver = drivers[0]
ref_lap = laps.pick_driver(ref_driver).pick_fastest()
track_tel = ref_lap.get_telemetry().dropna(subset=["X", "Y"])
ax1.plot(
    track_tel["X"],
    track_tel["Y"],
    color="lightgray",
    lw=2,
    alpha=0.7,
    zorder=1
)


for drv, tel in telemetry_data.items():
    team = laps.pick_driver(drv)["Team"].iloc[0]
    color = TEAM_COLORS.get(team, "#888888")

    points[drv], = ax1.plot([], [], "o", color=color, markersize=9, )
    lines[drv], = ax1.plot([], [], color=color, lw=2, alpha=0.7)

ax1.set_xlim(all_tel["X"].min() - 20, all_tel["X"].max() + 20)
ax1.set_ylim(all_tel["Y"].min() - 20, all_tel["Y"].max() + 20)
ax1.legend()

#time setup
t_start = 0.0
t_end = max(t["t"].iloc[-1] for t in telemetry_data.values())
frames = int((t_end - t_start) * FPS)


is_paused = False
manual_scrub = False

def toggle_play(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
        play_button.label.set_text("Pause")
    else:
        ani.event_source.stop()
        play_button.label.set_text("Play")
    is_paused = not is_paused

play_ax = fig1.add_axes([0.1, 0.1, 0.15, 0.06])
play_button = Button(play_ax, "Pause")
play_button.on_clicked(toggle_play)

slider_ax = fig1.add_axes([0.35, 0.12, 0.4, 0.03])
time_slider = Slider(
    slider_ax,
    "Time",
    t_start,
    t_end,
    valinit=t_start
)

#Speed multiplier slider
speed_ax = fig1.add_axes([0.35, 0.06, 0.4, 0.03])
speed_slider = Slider(
    speed_ax,
    "Speed",
    0.25,
    3.0,
    valinit=1.0
)


def on_scrub(val):
    global manual_scrub
    manual_scrub = True
    update(int((val - t_start) * FPS))
    fig1.canvas.draw_idle()

time_slider.on_changed(on_scrub)

leaderboard_ax1 = fig1.add_axes([0.78, 0.25, 0.18, 0.55])
leaderboard_ax1.axis("off")

# Lap counter text (top-left corner)
lap_text = ax1.text(
    0.02, 0.95, "Lap 1",  # position in axes coordinates
    transform=ax1.transAxes,
    fontsize=14,
    fontweight='bold',
    bbox=dict(facecolor='white', alpha=0.7)
)



def update(frame):
    global manual_scrub

    if manual_scrub:
        current_t = time_slider.val
        manual_scrub = False
    else:
        current_t = frame / FPS * speed_slider.val
        time_slider.set_val(current_t)

    snapshots = []

    # Collect positions and distances
    for drv, tel in telemetry_data.items():
        idx = min(tel["t"].searchsorted(current_t), len(tel) - 1)
        x, y = tel.loc[idx, ["X", "Y"]]
        points[drv].set_data([x], [y])

        if SHOW_TRAILS:
            lines[drv].set_data(tel["X"][:idx], tel["Y"][:idx])

        snapshots.append((drv, idx, tel["dist"].iloc[idx], tel))

    # Sort by distance (leader first)
    snapshots.sort(key=lambda x: x[2], reverse=True)
    leader_dist = snapshots[0][2]

    # Clear and redraw leaderboard
    leaderboard_ax1.clear()
    leaderboard_ax1.axis("off")
    leaderboard_ax1.text(
        0.0, 1.0, "Leaderboard",
        fontsize=14,
        fontweight="bold",
        transform=leaderboard_ax1.transAxes
    )

    line_height = 0.06
    for i, (drv, idx, dist, tel) in enumerate(snapshots):
        team = laps.pick_driver(drv)["Team"].iloc[0]
        color = TEAM_COLORS.get(team, "#888888")
         # Determine if driver has finished
    finished = current_t <= tel["t"].iloc[-1]
    
    if i == 0:
        gap_str = "LEADER"
    else:
        if finished:
            gap = (leader_dist - dist) / 80.0
            gap_str = f"+{gap:.1f}s"
        else:
            gap_str = "DNF"  # Only show DNF if their telemetry is over
        leaderboard_ax1.text(
            0.0,
            1.0 - (i + 1) * line_height,
            f"{i+1}. {drv} {gap_str}",
            color=color,
            fontsize=11,
            transform=leaderboard_ax1.transAxes
        )

    # Lap counter (top-left)
    current_lap = max(
        sum(current_t >= t for t in tel.attrs["lap_starts"])
        for tel in telemetry_data.values()
    )
    lap_text.set_text(f"Lap {current_lap}")

    return list(points.values()) + list(lines.values())


ani = FuncAnimation(
    fig1,
    update,
    frames=frames,
    interval=1000 / FPS,
    blit=False 
)


ax1.legend()
plt.show()
if drivers_input != "ALL":

    fig2,ax2 = plt.subplots(figsize=(12, 6))#new figure for lap/sector plot
    team_driver_count = {}

    for driver in drivers:
        driver_laps = laps[laps['Driver'] == driver].dropna(
            subset=['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
    )

    lap_numbers = driver_laps['LapNumber']
    driver_team = driver_laps['Team'].iloc[0]
    color = TEAM_COLORS.get(driver_team, '#888888')

    count = team_driver_count.get(driver_team, 0)
    linestyle = LINE_STYLES[count % len(LINE_STYLES)]
    team_driver_count[driver_team] = count + 1

    if mode == "LAP":
        lap_times = driver_laps['LapTime'].dt.total_seconds()
        ax2.plot(lap_numbers, lap_times, linestyle=linestyle, color=color, marker='o',
                 label=f"{driver} Lap Time")

        fastest_idx = lap_times.idxmin()
        ax2.scatter(lap_numbers.loc[fastest_idx], lap_times.loc[fastest_idx],
                    s=140, edgecolors='black', color=color, zorder=5)

    else:  # SECTOR MODE
        for i in range(3):
            sector_times = driver_laps[f'Sector{i+1}Time'].dt.total_seconds()
            ax2.plot(
                lap_numbers,
                sector_times,
                marker=SECTOR_MARKERS[i],
                linestyle=linestyle,
                color=color,
                label=f"{driver} Sector {i+1}"
            )

    # Pit stops
    pit_laps = driver_laps[driver_laps['PitInTime'].notna()]['LapNumber']
    for pit in pit_laps:
        ax2.axvline(pit, color=color, linestyle=':', alpha=0.4)

    ax2.set_xlabel("Lap Number")
    ax2.set_ylabel("Time (s)")
    ax2.set_title("Lap Time Comparison" if mode == "LAP" else "Sector Time Comparison")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    plt.show()

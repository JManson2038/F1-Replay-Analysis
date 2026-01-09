
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
    'Red Bull Racing': '#00174C',   # Blue
    'Mercedes': '#6CD3BF',          # Silver/Turquoise
    'McLaren': '#FF8000',           # Papaya Orange
    'Alpine': '#FF87BC',            # Pink
    'Aston Martin': '#00665E',      # British Racing Green
    'Williams': '#005AFF',          # Blue
    'Cadillac': '#000000',          # Black
    'Haas F1 Team': '#FFFFFF',      # White/Red/Black (using white as base)
    'AlphaTauri': '#2B4562',        # Navy Blue
    'Sauber': '#52C41A',            # Green
    'Racing Bulls': '#FDD900',                # Yellow
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
drivers = input("Enter the drivers (comma separated) like this: 'HAM,NOR,VER': ").split(',')
drivers = [driver.strip().upper() for driver in drivers]
if not drivers:
    print("No drivers entered")
    exit()
if not all(driver in laps['Driver'].unique() for driver in drivers):
    print("Invalid driver")
    exit()

# Track Animation

fig1, ax1 = plt.subplots(figsize=(8, 8))
ax1.set_title("F1 Fastest Lap Replay")
ax1.set_aspect('equal')
plt.subplots_adjust(bottom=0.25, right=0.78)


# Collect telemetry for all drivers
telemetry_data = {}
points = {}
lines = {}
SHOW_TRAILS = True  #  toggle trails ON/OFF
FPS = 30

for drv in drivers:
    lap = session.laps.pick_driver(drv).pick_fastest()
    tel = lap.get_telemetry().dropna(subset=["X", "Y", "Time"]).reset_index(drop=True)
    tel["t"] = tel["Time"].dt.total_seconds()

    telemetry_data[drv] = tel
    color = TEAM_COLORS.get(lap["Team"], "#888888")

    # Track
    ax1.plot(tel["X"], tel["Y"], color="lightgray", lw=1, alpha=0.6)

    # Dot
    points[drv], = ax1.plot(
        [tel["X"].iloc[0]],
        [tel["Y"].iloc[0]],
        "o",
        color=color,
        markersize=10,
        markeredgecolor="black",
        label=drv,
        zorder=10
    )

    # Trail
    lines[drv], = ax1.plot([], [], color=color, lw=2, alpha=0.8)


# Set axis limits
all_x = pd.concat([t["X"] for t in telemetry_data.values()])
all_y = pd.concat([t["Y"] for t in telemetry_data.values()])
ax1.set_xlim(all_x.min() - 20, all_x.max() + 20)
ax1.set_ylim(all_y.min() - 20, all_y.max() + 20)


#start lights
start_lights = []
light_y = ax1.get_ylim()[1] * 0.95
light_xs = [-40, -20, 0, 20, 40]

for x in light_xs:
    l, = ax1.plot(x, light_y, "o", color="darkred", markersize=18, alpha=0.3)
    start_lights.append(l)

LIGHT_INTERVAL = 0.8
START_DELAY = LIGHT_INTERVAL * 5
race_started = False
#lap count
lap_text = ax1.text(
    0.02, 0.95, "Lap: 1",
    transform=ax1.transAxes,
    fontsize=14,
    bbox=dict(facecolor="white", alpha=0.7))

#time setup
t_start = min(t["t"].iloc[0] for t in telemetry_data.values())
t_end = max(t["t"].iloc[-1] for t in telemetry_data.values())
frames = int((t_end - t_start) * FPS)

leaderboard_ax1 = fig1.add_axes([0.80, 0.25, 0.18, 0.55])
leaderboard_ax1.axis("off")
leaderboard_text = leaderboard_ax1.text(
    0, 1, "", fontsize=12, verticalalignment="top"
)


is_paused = False

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

manual_scrub = False

def on_scrub(val):
    global manual_scrub
    manual_scrub = True
    update(int((val - t_start) * FPS))
    fig1.canvas.draw_idle()

time_slider.on_changed(on_scrub)


def update(frame):
    global manual_scrub

    if manual_scrub:
        current_t = time_slider.val
        manual_scrub = False
    else:
        current_t = t_start + frame / FPS
        time_slider.set_val(current_t)

    artists = []

    # 🚦 Start lights
    for i, light in enumerate(start_lights):
        light.set_alpha(1.0 if current_t > i * LIGHT_INTERVAL else 0.3)

    if current_t > START_DELAY:
        for light in start_lights:
            light.set_alpha(0)

    leaderboard = []

    for drv, tel in telemetry_data.items():
        idx = min(tel["t"].searchsorted(current_t), len(tel) - 1)
        x, y = tel["X"].iloc[idx], tel["Y"].iloc[idx]

        points[drv].set_data([x], [y])
        artists.append(points[drv])

        if SHOW_TRAILS:
            lines[drv].set_data(tel["X"][:idx], tel["Y"][:idx])
            artists.append(lines[drv])

        leaderboard.append((drv, idx))

    # 🏁 Update leaderboard
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    leaderboard_text.set_text(
        "Leaderboard\n\n" +
        "\n".join(f"{i+1}. {drv}" for i, (drv, _) in enumerate(leaderboard))
    )

    return artists


ani = FuncAnimation(
    fig1,
    update,
    frames=frames,
    interval=1000 / FPS,
    blit=False 
)


ax1.legend()
plt.show()

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

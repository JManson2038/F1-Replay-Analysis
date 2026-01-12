

TEAM_COLORS = {
    'Ferrari': '#FF2800',
    'Red Bull Racing': '#3671C6',
    'Mercedes': '#6CD3BF',
    'McLaren': '#FF8000',
    'Alpine': '#FF87BC',
    'Aston Martin': '#00665E',
    'Williams': '#005AFF',
    'Cadillac': '#000000',
    'Haas F1 Team': '#9C9FA2',
    'AlphaTauri': '#2B4562',
    'Kick Sauber': '#52C41A',
    'Racing Bulls': '#FDD900',
    'alfa romeo': '#972738'
}

LINE_STYLES = ['-', '--']
SECTOR_MARKERS = ['o', 's', '^']

# Animation settings
FPS = 30
SHOW_TRAILS = False
TRAIL_LENGTH = 100

# Figure settings
TRACK_FIGURE_SIZE = (10, 8)
COMPARISON_FIGURE_SIZE = (12, 6)

# Cache settings
CACHE_DIR = 'cache'

# DNF detection threshold (percentage of race completion)
DNF_THRESHOLD = 0.95  # Consider DNF if finished 5% early

# Lap detection settings
LAP_TIME_GAP_THRESHOLD = 10  # seconds

# UI Colors
UI_COLORS = {
    'leader': 'gold',
    'podium': 'silver',
    'normal': 'lightgray',
    'dnf': 'darkred',
    'gap_close': 'lime',
    'gap_normal': 'white',
    'gap_large': 'orange',
    'gap_laps_down': 'red'
}

# Gap thresholds (in seconds)
GAP_CLOSE_THRESHOLD = 1.0
GAP_LARGE_THRESHOLD = 10.0
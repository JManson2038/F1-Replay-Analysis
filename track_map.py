
import matplotlib.pyplot as plt
from config import TEAM_COLORS, SHOW_TRAILS


class TrackMap:
    #Manages track visualization and driver positions
    
    def __init__(self, ax, track_telemetry, drivers):
        self.ax = ax
        self.track_telemetry = track_telemetry
        self.drivers = drivers
        self.points = {}
        self.lines = {}
        self.show_trails = SHOW_TRAILS
        
        self.setup_track()
        
    def setup_track(self):
        #Setup the track display
        self.ax.set_title("F1 Lap Replay", fontsize=16, fontweight='bold', pad=20)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Draw track reference line
        self.ax.plot(self.track_telemetry["X"], self.track_telemetry["Y"], 
                    color="lightgray", lw=2, alpha=0.7, zorder=1)
        
        # Set limits with padding
        self.ax.set_xlim(self.track_telemetry["X"].min() - 20, 
                        self.track_telemetry["X"].max() + 20)
        self.ax.set_ylim(self.track_telemetry["Y"].min() - 20, 
                        self.track_telemetry["Y"].max() + 20)
        
        # Create driver markers
        for driver in self.drivers:
            color = TEAM_COLORS.get(driver.team, "#888888")
            self.points[driver.code], = self.ax.plot(
                [], [], "o", color=color, markersize=10, 
                markeredgecolor='white', markeredgewidth=1.5, zorder=10
            )
            self.lines[driver.code], = self.ax.plot(
                [], [], color=color, lw=2, alpha=0.7
            )
    
    def update(self, current_time):
        #Update driver positions on track
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            
            # Set alpha based on DNF status
            alpha = 0.3 if driver.is_dnf() else 1.0
            
            # Update position marker
            self.points[driver.code].set_data([pos['x']], [pos['y']])
            self.points[driver.code].set_alpha(alpha)
            
            # Update trail if enabled
            if self.show_trails:
                idx = pos['idx']
                tel = driver.telemetry
                self.lines[driver.code].set_data(tel["X"][:idx], tel["Y"][:idx])
                self.lines[driver.code].set_alpha(alpha)
    
    def toggle_trails(self):
        #Toggle trail visibility
        self.show_trails = not self.show_trails
        return self.show_trails


class LapCounter:
    #Manages lap counter display
    
    def __init__(self, ax, drivers):
        self.ax = ax
        self.drivers = drivers
        self.text = self.ax.text(
            0.02, 0.98, "Lap 1", transform=self.ax.transAxes, 
            fontsize=16, fontweight='bold', 
            bbox=dict(facecolor='white', alpha=0.9, 
                     edgecolor='black', linewidth=2, boxstyle='round,pad=0.5')
        )
    
    def update(self, current_time):
        #Update lap counter
        max_lap = 1
        for driver in self.drivers:
            if driver.is_dnf() and current_time > driver.dnf_time:
                continue  # Skip DNF drivers
            current_lap = driver.get_current_lap(current_time)
            max_lap = max(max_lap, current_lap)
        
        self.text.set_text(f"Lap {max_lap}")
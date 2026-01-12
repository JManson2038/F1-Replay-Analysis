
import matplotlib.pyplot as plt
from config import TEAM_COLORS
import numpy as np

class SpeedTrace:
    """Real-time speed trace showing current and historical speeds"""
    
    def __init__(self, ax, drivers, window_seconds=10):
        self.ax = ax
        self.drivers = drivers
        self.window_seconds = window_seconds  # Time window to display
        self.lines = {}
        self.speed_data = {d.code: {'times': [], 'speeds': []} for d in drivers}
        
        self.setup_axes()
        
    def setup_axes(self):
        """Setup speed trace axes"""
        self.ax.set_title("Speed Trace (km/h)", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Time (s)", fontsize=10)
        self.ax.set_ylabel("Speed (km/h)", fontsize=10)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_ylim(0, 350)  # F1 cars max ~350 km/h
        
        # Create line for each driver
        for driver in self.drivers:
            color = TEAM_COLORS.get(driver.team, "#888888")
            line, = self.ax.plot([], [], color=color, linewidth=2, 
                                label=driver.code, alpha=0.8)
            self.lines[driver.code] = line
        
        self.ax.legend(loc='upper left', fontsize=8, ncol=2)
    
    def update(self, current_time):
        """Update speed traces"""
        # Clear and reset
        min_time = max(0, current_time - self.window_seconds)
        
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            tel = driver.telemetry
            
            # Get speed at current position
            if 'Speed' in tel.columns:
                speed = tel.loc[pos['idx'], 'Speed']
            else:
                # Calculate speed from distance if Speed column doesn't exist
                speed = 0
            
            # Update data storage
            times = self.speed_data[driver.code]['times']
            speeds = self.speed_data[driver.code]['speeds']
            
            times.append(current_time)
            speeds.append(speed)
            
            # Keep only data within window
            while times and times[0] < min_time:
                times.pop(0)
                speeds.pop(0)
            
            # Update line
            alpha = 0.3 if driver.is_dnf() else 0.8
            self.lines[driver.code].set_data(times, speeds)
            self.lines[driver.code].set_alpha(alpha)
        
        # Adjust x-axis to show rolling window
        self.ax.set_xlim(min_time, current_time + 1)


class SpeedHeatmap:
    """Speed heatmap showing speed distribution across track"""
    
    def __init__(self, ax, driver, track_telemetry):
        self.ax = ax
        self.driver = driver
        self.track_telemetry = track_telemetry
        self.scatter = None
        self.current_marker = None
        
        self.setup_axes()
        
    def setup_axes(self):
        """Setup speed heatmap"""
        self.ax.set_title(f"Speed Map - {self.driver.code}", 
                         fontsize=12, fontweight='bold')
        self.ax.set_aspect('equal')
        self.ax.axis('off')
    
    def update(self, current_time):
        """Update speed heatmap"""
        pos = self.driver.get_position_at_time(current_time)
        tel = self.driver.telemetry
        
        # Clear previous
        if self.scatter:
            self.scatter.remove()
        if self.current_marker:
            self.current_marker.remove()
        
        # Get speed data up to current position
        idx = pos['idx']
        x = tel['X'][:idx]
        y = tel['Y'][:idx]
        
        if 'Speed' in tel.columns:
            speeds = tel['Speed'][:idx]
        else:
            # Use dummy speed data
            speeds = np.ones(len(x)) * 200
        
        # Draw speed heatmap
        if len(x) > 0:
            self.scatter = self.ax.scatter(
                x, y, c=speeds, cmap='RdYlGn', 
                s=10, alpha=0.6, vmin=0, vmax=350
            )
            
            # Mark current position
            color = TEAM_COLORS.get(self.driver.team, "#888888")
            self.current_marker = self.ax.scatter(
                [pos['x']], [pos['y']], 
                color=color, s=100, marker='o',
                edgecolors='white', linewidths=2, zorder=10
            )
        
        # Set limits
        if hasattr(self.track_telemetry, 'X'):
            self.ax.set_xlim(self.track_telemetry["X"].min() - 20,
                           self.track_telemetry["X"].max() + 20)
            self.ax.set_ylim(self.track_telemetry["Y"].min() - 20,
                           self.track_telemetry["Y"].max() + 20)


class CurrentSpeedometer:
    """Digital speedometer showing current speed"""
    
    def __init__(self, ax, driver):
        self.ax = ax
        self.driver = driver
        self.speed_text = None
        self.gear_text = None
        self.throttle_bar = None
        self.brake_bar = None
        
        self.setup_axes()
    
    def setup_axes(self):
        """Setup speedometer display"""
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        color = TEAM_COLORS.get(self.driver.team, "#888888")
        
        # Driver name
        self.ax.text(0.5, 0.9, self.driver.code, 
                    ha='center', va='center', fontsize=16, 
                    fontweight='bold', color=color)
        
        # Speed display (will be updated)
        self.speed_text = self.ax.text(
            0.5, 0.5, "0", 
            ha='center', va='center', 
            fontsize=48, fontweight='bold', color=color
        )
        
        # Unit label
        self.ax.text(0.5, 0.35, "km/h", 
                    ha='center', va='center', 
                    fontsize=12, color='gray')
        
        # Gear display
        self.gear_text = self.ax.text(
            0.5, 0.2, "N", 
            ha='center', va='center', 
            fontsize=20, fontweight='bold', color='white',
            bbox=dict(boxstyle='circle', facecolor=color, 
                     edgecolor='white', linewidth=2)
        )
    
    def update(self, current_time):
        """Update speedometer"""
        pos = self.driver.get_position_at_time(current_time)
        tel = self.driver.telemetry
        
        # Get current speed
        if 'Speed' in tel.columns:
            speed = tel.loc[pos['idx'], 'Speed']
        else:
            speed = 0
        
        # Get gear if available
        if 'nGear' in tel.columns:
            gear = int(tel.loc[pos['idx'], 'nGear'])
        else:
            gear = 0
        
        # Update displays
        self.speed_text.set_text(f"{int(speed)}")
        
        if gear > 0:
            self.gear_text.set_text(str(gear))
        else:
            self.gear_text.set_text("N")
        
        # Fade if DNF
        alpha = 0.3 if self.driver.is_dnf() else 1.0
        self.speed_text.set_alpha(alpha)
        self.gear_text.set_alpha(alpha)
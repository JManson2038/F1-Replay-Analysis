# race_replay.py
# Main race replay manager with enhanced telemetry visualizations

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
from track_map import TrackMap, LapCounter
from leaderboard import Leaderboard
from speed_trace import SpeedTrace, SpeedHeatmap, CurrentSpeedometer
from telemetry import ThrottleBrakeTrace, GearTrace, RPMTrace, DRSIndicator
from config import FPS, DNF_THRESHOLD
import logging

logger = logging.getLogger(__name__)


class RaceReplay:
    #Main race replay manager with comprehensive telemetry
    
    def __init__(self, drivers, track_telemetry, enable_telemetry=True):
        self.drivers = drivers
        self.track_telemetry = track_telemetry
        self.enable_telemetry = enable_telemetry
        self.current_time = 0
        self.is_paused = False
        self.manual_scrub = False
        self.speed = 1.0
        
        # Calculate total duration
        self.max_time = max(d.telemetry["t"].iloc[-1] for d in drivers)
        
        if enable_telemetry:
            self.setup_telemetry_layout()
        else:
            self.setup_basic_layout()
        
        # Setup animation
        self.frames = int(self.max_time * FPS)
        self.ani = None
        
        logger.info(f"Race replay initialized: {len(drivers)} drivers, {self.max_time:.1f}s duration")
    
    def setup_basic_layout(self):
        #Setup basic layout (track + leaderboard only)
        self.fig = plt.figure(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.25, right=0.75, left=0.1, top=0.95)
        
        # Main track
        self.ax_track = self.fig.add_subplot(111)
        self.track_map = TrackMap(self.ax_track, self.track_telemetry, self.drivers)
        self.lap_counter = LapCounter(self.ax_track, self.drivers)
        
        # Leaderboard
        self.ax_leaderboard = self.fig.add_axes([0.76, 0.25, 0.23, 0.65])
        self.leaderboard = Leaderboard(self.ax_leaderboard, self.drivers)
        
        # Controls
        self.setup_controls()
    
    def setup_telemetry_layout(self):
        #Setup enhanced layout with telemetry graphs
        self.fig = plt.figure(figsize=(20, 12))
        
        # Create grid layout
        gs = self.fig.add_gridspec(4, 4, left=0.05, right=0.95, bottom=0.15, 
                                   top=0.95, hspace=0.4, wspace=0.3)
        
        # Main track (top left, large)
        self.ax_track = self.fig.add_subplot(gs[0:2, 0:2])
        self.track_map = TrackMap(self.ax_track, self.track_telemetry, self.drivers)
        self.lap_counter = LapCounter(self.ax_track, self.drivers)
        
        # Leaderboard (top right)
        self.ax_leaderboard = self.fig.add_subplot(gs[0:2, 2])
        self.leaderboard = Leaderboard(self.ax_leaderboard, self.drivers)
        
        # Speed trace (middle left)
        self.ax_speed = self.fig.add_subplot(gs[2, 0:2])
        self.speed_trace = SpeedTrace(self.ax_speed, self.drivers, window_seconds=15)
        
        # Throttle/Brake (middle right)
        self.ax_throttle = self.fig.add_subplot(gs[2, 2:4])
        self.throttle_brake = ThrottleBrakeTrace(self.ax_throttle, self.drivers, window_seconds=15)
        
        # Gear trace (bottom left)
        self.ax_gear = self.fig.add_subplot(gs[3, 0:2])
        self.gear_trace = GearTrace(self.ax_gear, self.drivers, window_seconds=15)
        
        # RPM trace (bottom right)
        self.ax_rpm = self.fig.add_subplot(gs[3, 2:4])
        self.rpm_trace = RPMTrace(self.ax_rpm, self.drivers, window_seconds=15)
        
        # Speedometers for first 3 drivers (top right, stacked)
        self.speedometers = []
        for i, driver in enumerate(self.drivers[:3]):
            ax_speed = self.fig.add_subplot(gs[i, 3])
            speedometer = CurrentSpeedometer(ax_speed, driver)
            self.speedometers.append(speedometer)
        
        # DRS indicator for first driver
        if len(self.drivers) > 0:
            self.ax_drs = self.fig.add_subplot(gs[3, 3])
            self.drs_indicator = DRSIndicator(self.ax_drs, self.drivers[0])
        
        # Controls
        self.setup_controls()
    
    def setup_controls(self):
        #Setup UI controls (buttons and sliders)
        # Play/Pause button
        play_ax = self.fig.add_axes([0.1, 0.05, 0.1, 0.04])
        self.play_button = Button(play_ax, "Pause", color='lightgray', hovercolor='gray')
        self.play_button.on_clicked(self.toggle_play)
        
        # Time slider
        time_slider_ax = self.fig.add_axes([0.25, 0.07, 0.5, 0.02])
        self.time_slider = Slider(time_slider_ax, "Time", 0.0, self.max_time, 
                                  valinit=0.0, color='blue')
        self.time_slider.on_changed(self.on_scrub)
        
        # Speed slider
        speed_slider_ax = self.fig.add_axes([0.25, 0.03, 0.5, 0.02])
        self.speed_slider = Slider(speed_slider_ax, "Speed", 0.25, 3.0, 
                                   valinit=1.0, color='green')
        self.speed_slider.on_changed(lambda val: setattr(self, 'speed', val))
        
        # Time display
        self.time_text = self.fig.text(0.8, 0.06, "00:00.0", 
                                       fontsize=14, fontweight='bold',
                                       ha='center',
                                       bbox=dict(boxstyle='round', 
                                               facecolor='black', 
                                               edgecolor='white',
                                               linewidth=2, alpha=0.8),
                                       color='white')
    
    def toggle_play(self, event):
        #Toggle play/pause
        if self.is_paused:
            self.ani.event_source.start()
            self.play_button.label.set_text("Pause")
            self.play_button.color = 'lightgray'
        else:
            self.ani.event_source.stop()
            self.play_button.label.set_text("Play")
            self.play_button.color = 'lightgreen'
        self.is_paused = not self.is_paused
    
    def on_scrub(self, val):
        #Handle manual time scrubbing
        self.manual_scrub = True
        self.update(int(val * FPS))
        self.fig.canvas.draw_idle()
    
    def detect_dnf(self, current_time):
        #Detect and mark DNF drivers
        for driver in self.drivers:
            if driver.is_dnf():
                continue
                
            if driver.has_finished(current_time):
                # Check if finished significantly early
                if driver.telemetry["t"].iloc[-1] < self.max_time * DNF_THRESHOLD:
                    lap = driver.get_current_lap(driver.telemetry["t"].iloc[-1])
                    driver.set_dnf(driver.telemetry["t"].iloc[-1], lap)
                    logger.info(f"{driver.code} DNF detected at lap {lap}")
    
    def format_time(self, seconds):
        #Format seconds to MM:SS.s
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:04.1f}"
    
    def update(self, frame):
        #Update animation frame
        # Calculate current time
        if self.manual_scrub:
            current_time = self.time_slider.val
            self.manual_scrub = False
        else:
            current_time = frame / FPS * self.speed
            self.time_slider.set_val(current_time)
        
        # Update time display
        self.time_text.set_text(self.format_time(current_time))
        
        # Detect DNFs
        self.detect_dnf(current_time)
        
        # Update core components
        self.track_map.update(current_time)
        self.lap_counter.update(current_time)
        self.leaderboard.update(current_time)
        
        # Update telemetry graphs if enabled
        if self.enable_telemetry:
            self.speed_trace.update(current_time)
            self.throttle_brake.update(current_time)
            self.gear_trace.update(current_time)
            self.rpm_trace.update(current_time)
            
            # Update speedometers
            for speedometer in self.speedometers:
                speedometer.update(current_time)
            
            # Update DRS
            if hasattr(self, 'drs_indicator'):
                self.drs_indicator.update(current_time)
        
        return []
    
    def start(self):
        """Start the animation"""
        logger.info("Starting race replay animation")
        self.ani = FuncAnimation(
            self.fig, self.update, 
            frames=self.frames, 
            interval=1000/FPS, 
            blit=False
        )
        plt.show()


class MinimalReplay(RaceReplay):
    #Minimal version for performance (no telemetry graphs)
    
    def __init__(self, drivers, track_telemetry):
        super().__init__(drivers, track_telemetry, enable_telemetry=False)
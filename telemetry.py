
import matplotlib.pyplot as plt
from config import TEAM_COLORS
import numpy as np


class ThrottleBrakeTrace:
    #Shows throttle and brake inputs over time
    
    def __init__(self, ax, drivers, window_seconds=10):
        self.ax = ax
        self.drivers = drivers
        self.window_seconds = window_seconds
        self.throttle_lines = {}
        self.brake_lines = {}
        self.data = {d.code: {'times': [], 'throttle': [], 'brake': []} 
                     for d in drivers}
        
        self.setup_axes()
    
    def setup_axes(self):
        """Setup axes for throttle/brake"""
        self.ax.set_title("Throttle & Brake Input (%)", fontsize=11, fontweight='bold')
        self.ax.set_xlabel("Time (s)", fontsize=9)
        self.ax.set_ylabel("Input %", fontsize=9)
        self.ax.set_ylim(0, 105)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        for driver in self.drivers:
            color = TEAM_COLORS.get(driver.team, "#888888")
            
            # Throttle (solid line)
            throttle_line, = self.ax.plot([], [], color=color, 
                                         linewidth=1.5, alpha=0.7,
                                         label=f"{driver.code} Throttle")
            self.throttle_lines[driver.code] = throttle_line
            
            # Brake (dashed line, red tint)
            brake_color = '#FF0000' if color == '#888888' else color
            brake_line, = self.ax.plot([], [], color=brake_color, 
                                      linewidth=1.5, alpha=0.7,
                                      linestyle='--',
                                      label=f"{driver.code} Brake")
            self.brake_lines[driver.code] = brake_line
        
        self.ax.legend(loc='upper left', fontsize=7, ncol=2)
    
    def update(self, current_time):
        """Update throttle/brake traces"""
        min_time = max(0, current_time - self.window_seconds)
        
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            tel = driver.telemetry
            
            # Get inputs
            throttle = tel.loc[pos['idx'], 'Throttle'] if 'Throttle' in tel.columns else 0
            brake = tel.loc[pos['idx'], 'Brake'] if 'Brake' in tel.columns else 0
            
            # Store data
            data = self.data[driver.code]
            data['times'].append(current_time)
            data['throttle'].append(throttle)
            data['brake'].append(brake)
            
            # Trim old data
            while data['times'] and data['times'][0] < min_time:
                data['times'].pop(0)
                data['throttle'].pop(0)
                data['brake'].pop(0)
            
            # Update lines
            alpha = 0.3 if driver.is_dnf() else 0.7
            self.throttle_lines[driver.code].set_data(data['times'], data['throttle'])
            self.throttle_lines[driver.code].set_alpha(alpha)
            
            self.brake_lines[driver.code].set_data(data['times'], data['brake'])
            self.brake_lines[driver.code].set_alpha(alpha)
        
        self.ax.set_xlim(min_time, current_time + 1)


class GearTrace:
    """Shows gear changes over time"""
    
    def __init__(self, ax, drivers, window_seconds=10):
        self.ax = ax
        self.drivers = drivers
        self.window_seconds = window_seconds
        self.lines = {}
        self.data = {d.code: {'times': [], 'gears': []} for d in drivers}
        
        self.setup_axes()
    
    def setup_axes(self):
        """Setup gear trace axes"""
        self.ax.set_title("Gear Selection", fontsize=9, fontweight='bold')
        self.ax.set_xlabel("Time (s)", fontsize=7)
        self.ax.set_ylabel("Gear", fontsize=7)
        self.ax.set_ylim(0, 9)
        self.ax.set_yticks(range(0, 9))
        self.ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        for driver in self.drivers:
            color = TEAM_COLORS.get(driver.team, "#888888")
            line, = self.ax.plot([], [], color=color, linewidth=2, 
                               marker='o', markersize=3,
                               label=driver.code, alpha=0.7)
            self.lines[driver.code] = line
        
        self.ax.legend(loc='upper left', fontsize=8, ncol=3)
    
    def update(self, current_time):
        #Update gear traces
        min_time = max(0, current_time - self.window_seconds)
        
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            tel = driver.telemetry
            
            # Get gear
            gear = tel.loc[pos['idx'], 'nGear'] if 'nGear' in tel.columns else 0
            
            # Store data
            data = self.data[driver.code]
            data['times'].append(current_time)
            data['gears'].append(gear)
            
            # Trim old data
            while data['times'] and data['times'][0] < min_time:
                data['times'].pop(0)
                data['gears'].pop(0)
            
            # Update line
            alpha = 0.3 if driver.is_dnf() else 0.7
            self.lines[driver.code].set_data(data['times'], data['gears'])
            self.lines[driver.code].set_alpha(alpha)
        
        self.ax.set_xlim(min_time, current_time + 1)


class RPMTrace:
    """Shows engine RPM over time"""
    
    def __init__(self, ax, drivers, window_seconds=10):
        self.ax = ax
        self.drivers = drivers
        self.window_seconds = window_seconds
        self.lines = {}
        self.data = {d.code: {'times': [], 'rpm': []} for d in drivers}
        
        self.setup_axes()
    
    def setup_axes(self):
        #Setup RPM trace axes
        self.ax.set_title("Engine RPM", fontsize=11, fontweight='bold')
        self.ax.set_xlabel("Time (s)", fontsize=9)
        self.ax.set_ylabel("RPM", fontsize=9)
        self.ax.set_ylim(8000, 13000)  # F1 typical range
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        # Red line indicator
        self.ax.axhline(y=12000, color='red', linestyle=':', 
                       linewidth=1, alpha=0.5, label='Red Line')
        
        for driver in self.drivers:
            color = TEAM_COLORS.get(driver.team, "#888888")
            line, = self.ax.plot([], [], color=color, linewidth=1.5,
                               label=driver.code, alpha=0.7)
            self.lines[driver.code] = line
        
        self.ax.legend(loc='lower left', fontsize=8, ncol=3)
    
    def update(self, current_time):
        """Update RPM traces"""
        min_time = max(0, current_time - self.window_seconds)
        
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            tel = driver.telemetry
            
            # Get RPM
            rpm = tel.loc[pos['idx'], 'RPM'] if 'RPM' in tel.columns else 10000
            
            # Store data
            data = self.data[driver.code]
            data['times'].append(current_time)
            data['rpm'].append(rpm)
            
            # Trim old data
            while data['times'] and data['times'][0] < min_time:
                data['times'].pop(0)
                data['rpm'].pop(0)
            
            # Update line
            alpha = 0.3 if driver.is_dnf() else 0.7
            self.lines[driver.code].set_data(data['times'], data['rpm'])
            self.lines[driver.code].set_alpha(alpha)
        
        self.ax.set_xlim(min_time, current_time + 1)


class DRSIndicator:
    #Shows DRS (Drag Reduction System) status#
    
    def __init__(self, ax, driver):
        self.ax = ax
        self.driver = driver
        self.indicator = None
        
        self.setup_axes()
    
    def setup_axes(self):
        #Setup DRS indicator
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        # DRS label
        self.ax.text(0.6, 0.9, "DRS", 
                    ha='center', va='center',
                    fontsize=14, fontweight='bold')
        
        # Status box (will be updated)
        self.indicator = self.ax.add_patch(
            plt.Rectangle((0.25, 0.2), 0.5, 0.3,
                         facecolor='gray', alpha=0.3,
                         edgecolor='white', linewidth=2)
        )
        
        self.status_text = self.ax.text(
            0.5, 0.35, "CLOSED",
            ha='center', va='center',
            fontsize=12, fontweight='bold', color='white'
        )
    
    def update(self, current_time):
        """Update DRS indicator"""
        pos = self.driver.get_position_at_time(current_time)
        tel = self.driver.telemetry
        
        # Check DRS status
        drs_active = False
        if 'DRS' in tel.columns:
            drs_value = tel.loc[pos['idx'], 'DRS']
            drs_active = drs_value > 0
        
        # Update indicator
        if drs_active:
            self.indicator.set_facecolor('lime')
            self.indicator.set_alpha(0.8)
            self.status_text.set_text("OPEN")
            self.status_text.set_color('black')
        else:
            self.indicator.set_facecolor('gray')
            self.indicator.set_alpha(0.3)
            self.status_text.set_text("CLOSED")
            self.status_text.set_color('white')
        
        # Fade if DNF
        if self.driver.is_dnf():
            self.indicator.set_alpha(0.2)
            self.status_text.set_alpha(0.3)
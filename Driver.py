# driver.py
# Driver class to encapsulate driver data and status

import pandas as pd
from config import LAP_TIME_GAP_THRESHOLD


class Driver:
    #Represents an F1 driver with telemetry and status
    
    def __init__(self, code, team, telemetry):
        self.code = code
        self.team = team
        self.telemetry = telemetry
        self.status = "ACTIVE"
        self.dnf_time = None
        self.dnf_lap = None
        self.dnf_position = None
        
    def is_dnf(self):
        #Check if driver has DNF'd
        return self.dnf_time is not None
    
    def set_dnf(self, time, lap):
        #Mark driver as DNF
        self.status = "DNF"
        self.dnf_time = time
        self.dnf_lap = lap
        
    def get_position_at_time(self, current_time):
        """Get driver's position data at a specific time"""
        if self.is_dnf() and current_time > self.dnf_time:
            # Return last known position
            idx = len(self.telemetry) - 1
        else:
            idx = min(self.telemetry["t"].searchsorted(current_time), 
                     len(self.telemetry) - 1)
        
        return {
            'idx': idx,
            'x': self.telemetry.loc[idx, 'X'],
            'y': self.telemetry.loc[idx, 'Y'],
            'dist': self.telemetry.loc[idx, 'dist'],
            'race_time': self.telemetry.loc[idx, 'race_time'],
            'laps_done': sum(current_time >= t for t in self.telemetry.attrs["lap_starts"])
        }
    
    def get_current_lap(self, current_time):
        """Get the current lap number"""
        return sum(current_time >= t for t in self.telemetry.attrs["lap_starts"])
    
    def has_finished(self, current_time):
        """Check if driver has finished their telemetry data"""
        return current_time > self.telemetry["t"].iloc[-1]
    
    @staticmethod
    def process_telemetry(telemetry_list):
        """Process raw telemetry data into usable format"""
        if not telemetry_list:
            return None
            
        tel = pd.concat(telemetry_list, ignore_index=True)
        tel["t"] -= tel["t"].iloc[0]
        tel["race_time"] = tel["t"]
        
        # Calculate distance
        dx = tel["X"].diff()
        dy = tel["Y"].diff()
        tel["dist"] = (dx**2 + dy**2).pow(0.5).fillna(0).cumsum()
        
        # Detect lap starts
        lap_starts = [0.0]
        for i in range(1, len(tel)):
            time_gap = tel["t"].iloc[i] - tel["t"].iloc[i - 1]
            # Detect lap completion by large time gaps
            if time_gap > LAP_TIME_GAP_THRESHOLD:
                lap_starts.append(tel["t"].iloc[i])
        
        tel.attrs["lap_starts"] = lap_starts
        tel.attrs["total_laps"] = len(lap_starts)
        
        return tel


import matplotlib.pyplot as plt
from config import TEAM_COLORS, UI_COLORS, GAP_CLOSE_THRESHOLD, GAP_LARGE_THRESHOLD


class Leaderboard:
#Manages leaderboard display and calculations
    
    def __init__(self, ax, drivers):
        self.ax = ax
        self.drivers = drivers
        self.setup_axes()
        
    def setup_axes(self):
        #Setup the leaderboard axes
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis("off")
        
    def calculate_gap(self, driver, leader_driver, current_time):
        #Calculate gap between driver and leader
        driver_pos = driver.get_position_at_time(current_time)
        leader_pos = leader_driver.get_position_at_time(current_time)
        
        # Check for laps down
        if driver_pos['laps_done'] < leader_pos['laps_done']:
            laps_down = leader_pos['laps_done'] - driver_pos['laps_done']
            gap_str = f"+{laps_down}L"
            gap_color = UI_COLORS['gap_laps_down']
            return gap_str, gap_color
        
        # Same lap - calculate time gap
        current_dist = driver_pos['dist']
        leader_tel = leader_driver.telemetry
        leader_dist_array = leader_tel["dist"].values
        leader_time_array = leader_tel["race_time"].values
        
        if current_dist <= leader_dist_array[-1]:
            leader_at_dist_idx = leader_tel["dist"].searchsorted(current_dist)
            leader_at_dist_idx = min(leader_at_dist_idx, len(leader_tel) - 1)
            leader_time_at_dist = leader_time_array[leader_at_dist_idx]
            gap_seconds = driver_pos['race_time'] - leader_time_at_dist
        else:
            gap_seconds = driver_pos['race_time'] - leader_time_array[leader_pos['idx']]
        
        # Format gap
        if gap_seconds < 0.05:
            gap_str = "±0.0s"
            gap_color = UI_COLORS['gap_close']
        elif gap_seconds < GAP_CLOSE_THRESHOLD:
            gap_str = f"+{gap_seconds:.2f}s"
            gap_color = UI_COLORS['gap_close']
        elif gap_seconds < GAP_LARGE_THRESHOLD:
            gap_str = f"+{gap_seconds:.1f}s"
            gap_color = UI_COLORS['gap_normal']
        else:
            gap_str = f"+{gap_seconds:.1f}s"
            gap_color = UI_COLORS['gap_large']
        
        return gap_str, gap_color
    
    def update(self, current_time):
        """Update the leaderboard display"""
        self.ax.clear()
        self.setup_axes()
        
        # Create snapshots of all drivers
        snapshots = []
        for driver in self.drivers:
            pos = driver.get_position_at_time(current_time)
            snapshots.append((driver, pos['laps_done'], pos['dist']))
        
        # Sort by laps done, then distance
        snapshots.sort(key=lambda x: (-x[1], -x[2]))
        
        # Draw title
        title_bg = plt.Rectangle((0, 0.94), 1, 0.06, facecolor='black', 
                                  edgecolor='white', linewidth=2, 
                                  transform=self.ax.transAxes)
        self.ax.add_patch(title_bg)
        self.ax.text(0.5, 0.97, "LEADERBOARD", fontsize=13, fontweight="bold", 
                    color='white', ha='center', va='center', 
                    transform=self.ax.transAxes)
        
        # Calculate line height
        num_drivers = len(snapshots)
        line_height = 0.85 / max(num_drivers, 1)
        
        # Leader reference
        leader_driver = snapshots[0][0] if snapshots else None
        
        # Draw each position
        for i, (driver, laps_done, dist) in enumerate(snapshots):
            y_pos = 0.90 - (i * line_height)
            is_dnf = driver.is_dnf()
            
            # Get gap
            if i == 0:
                gap_str = "LEADER"
                gap_color = UI_COLORS['leader']
            elif is_dnf:
                gap_str = f"DNF (L{driver.dnf_lap})"
                gap_color = UI_COLORS['dnf']
            else:
                gap_str, gap_color = self.calculate_gap(driver, leader_driver, current_time)
            
            # Draw position box
            self._draw_position_box(y_pos, line_height, i, driver, is_dnf)
            
            # Draw position number
            self._draw_position_number(y_pos, i, driver, is_dnf)
            
            # Draw driver code
            self._draw_driver_code(y_pos, driver, is_dnf)
            
            # Draw gap
            self._draw_gap(y_pos, gap_str, gap_color, is_dnf)
    
    def _draw_position_box(self, y_pos, line_height, position, driver, is_dnf):
        #Draw background box for position
        if is_dnf:
            bg_color = UI_COLORS['dnf']
            bg_alpha = 0.3
        elif position == 0:
            bg_color = UI_COLORS['leader']
            bg_alpha = 0.3
        elif position < 3:
            bg_color = UI_COLORS['podium']
            bg_alpha = 0.2
        else:
            bg_color = UI_COLORS['normal']
            bg_alpha = 0.1
        
        color = TEAM_COLORS.get(driver.team, "#888888")
        edge_color = UI_COLORS['dnf'] if is_dnf else color
        
        pos_box = plt.Rectangle((0.02, y_pos - line_height*0.4), 0.96, line_height*0.8, 
                                facecolor=bg_color, alpha=bg_alpha, 
                                edgecolor=edge_color, linewidth=2,
                                transform=self.ax.transAxes)
        self.ax.add_patch(pos_box)
    
    def _draw_position_number(self, y_pos, position, driver, is_dnf):
        #Draw position number circle
        color = TEAM_COLORS.get(driver.team, "#888888")
        pos_bg_color = UI_COLORS['dnf'] if is_dnf else color
        
        self.ax.text(0.08, y_pos, f"{position+1}", fontsize=12, fontweight='bold', 
                    ha='center', va='center', transform=self.ax.transAxes,
                    bbox=dict(boxstyle='circle', facecolor=pos_bg_color, 
                            edgecolor='white', linewidth=1.5, 
                            alpha=0.7 if is_dnf else 1.0))
    
    def _draw_driver_code(self, y_pos, driver, is_dnf):
        #Draw driver code with strikethrough if DNF
        color = TEAM_COLORS.get(driver.team, "#888888")
        
        if is_dnf:
            # Draw strikethrough
            self.ax.plot([0.18, 0.32], [y_pos, y_pos], color='red', 
                        linewidth=2, transform=self.ax.transAxes, zorder=10)
        
        self.ax.text(0.25, y_pos, driver.code, fontsize=11, fontweight='bold', 
                    color=color, ha='left', va='center', 
                    transform=self.ax.transAxes,
                    alpha=0.5 if is_dnf else 1.0)
    
    def _draw_gap(self, y_pos, gap_str, gap_color, is_dnf):
        #Draw gap time/status
        if is_dnf:
            self.ax.text(0.90, y_pos, gap_str, fontsize=9, fontweight='bold',
                        color='white', ha='right', va='center', 
                        transform=self.ax.transAxes,
                        bbox=dict(facecolor=UI_COLORS['dnf'], alpha=0.9, 
                                edgecolor='red', linewidth=1.5, pad=2))
        else:
            self.ax.text(0.90, y_pos, gap_str, fontsize=10, fontweight='bold',
                        color=gap_color, ha='right', va='center', 
                        transform=self.ax.transAxes,
                        bbox=dict(facecolor='black', alpha=0.7, 
                                edgecolor=gap_color, linewidth=1, pad=2))
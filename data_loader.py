
import os
import fastf1 as f1
from Driver import Driver
from config import CACHE_DIR
import logging

logger = logging.getLogger(__name__)


class SessionLoader:
    #Loads and processes F1 session data
    
    def __init__(self, year, round_number, session_type):
        self.year = year
        self.round_number = round_number
        self.session_type = session_type
        self.session = None
        self.laps = None
        
        # Setup cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        f1.Cache.enable_cache(CACHE_DIR)
        
    def load_session(self):
        #Load the F1 session
        try:
            logger.info(f"Loading {self.year} Round {self.round_number} {self.session_type}")
            self.session = f1.get_session(self.year, self.round_number, self.session_type)
            self.session.load()
            self.laps = self.session.laps
            logger.info("Session loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def get_available_drivers(self):
        #Get list of available driver codes
        if self.laps is None:
            return []
        return sorted(self.laps['Driver'].unique().tolist())
    
    def validate_drivers(self, driver_codes):
        #Validate that driver codes exist in the session
        available = set(self.get_available_drivers())
        invalid = [d for d in driver_codes if d not in available]
        
        if invalid:
            logger.error(f"Invalid driver codes: {', '.join(invalid)}")
            logger.info(f"Available drivers: {', '.join(sorted(available))}")
            return False
        return True
    
    def load_driver_telemetry(self, driver_code, replay_mode):
        #Load telemetry for a specific driver
        try:
            drv_laps = self.laps.pick_driver(driver_code)
            tel_list = []
            offset = 0.0
            
            if replay_mode == "FASTEST":
                lap = drv_laps.pick_fastest()
                if lap is None:
                    logger.warning(f"No valid lap for {driver_code}")
                    return None
                    
                t = lap.get_telemetry().dropna(subset=["X", "Y", "Time"])
                t["t"] = t["Time"].dt.total_seconds()
                tel_list.append(t)
                
            else:  # RACE mode
                for _, lap in drv_laps.iterlaps():
                    try:
                        t = lap.get_telemetry().dropna(subset=["X", "Y", "Time"])
                    except Exception as e:
                        logger.debug(f"Skipping lap for {driver_code}: {e}")
                        continue
                        
                    if t.empty:
                        continue
                        
                    t["t"] = t["Time"].dt.total_seconds() + offset
                    offset = t["t"].iloc[-1]
                    tel_list.append(t)
            
            if not tel_list:
                logger.warning(f"No telemetry data for {driver_code}")
                return None
                
            # Process telemetry
            telemetry = Driver.process_telemetry(tel_list)
            
            # Get team info
            team = drv_laps["Team"].iloc[0]
            
            logger.info(f"Loaded {driver_code} ({team}) - {len(telemetry)} data points")
            return Driver(driver_code, team, telemetry)
            
        except Exception as e:
            logger.error(f"Error loading telemetry for {driver_code}: {e}")
            return None
    
    def load_all_drivers(self, driver_codes, replay_mode):
        #Load telemetry for multiple drivers
        drivers = []
        
        for code in driver_codes:
            driver = self.load_driver_telemetry(code, replay_mode)
            if driver:
                drivers.append(driver)
        
        logger.info(f"Successfully loaded {len(drivers)}/{len(driver_codes)} drivers")
        return drivers
    
    def get_reference_track(self):
        #Get track coordinates from fastest lap
        if self.laps is None:
            return None
            
        try:
            ref_driver = self.get_available_drivers()[0]
            ref_lap = self.laps.pick_driver(ref_driver).pick_fastest()
            track_tel = ref_lap.get_telemetry().dropna(subset=["X", "Y"])
            return track_tel
        except Exception as e:
            logger.error(f"Failed to get reference track: {e}")
            return None
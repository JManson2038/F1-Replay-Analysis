
import logging
import sys
from data_loader import SessionLoader
from race_replay import RaceReplay

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_user_input():
    #Get user input for session configuration
    print("\n" + "="*50)
    print("F1 RACE REPLAY - Configuration")
    print("="*50 + "\n")
    
    # Get year
    while True:
        year = input("Enter the year: ").strip()
        if year.isdigit():
            year = int(year)
            break
        print(" Invalid year. Please enter a number.")
    
    # Get round number
    while True:
        round_num = input("Enter the Round number (1-24): ").strip()
        if round_num.isdigit():
            round_num = int(round_num)
            if 1 <= round_num <= 24:
                break
        print(" Invalid round number. Please enter 1-24.")
    
    # Get session type
    while True:
        session_type = input("Enter session type (R/Q/P/FP1/FP2/FP3/SQ): ").upper().strip()
        if session_type in {"R", "Q", "P", "FP1", "FP2", "FP3", "SQ"}:
            break
        print(" Invalid session type.")
    
    # Get replay mode
    while True:
        replay_mode = input("Replay mode (FASTEST/RACE): ").upper().strip()
        if replay_mode in {"FASTEST", "RACE"}:
            break
        print("Invalid mode. Choose FASTEST or RACE.")
    
    return year, round_num, session_type, replay_mode


def select_drivers(loader):
    #Allow user to select drivers
    available = loader.get_available_drivers()
    print(f"\n Available drivers: {', '.join(available)}")
    
    while True:
        drivers_input = input("Enter drivers (e.g., 'HAM,VER,NOR') or 'ALL': ").upper().strip()
        
        if drivers_input == "ALL":
            return available
        
        drivers = [d.strip() for d in drivers_input.split(",")]
        
        if loader.validate_drivers(drivers):
            return drivers
        
        print(" Invalid driver codes. Try again.")


def main():
    #Main application entry point
    try:
        print("\n  F1 RACE REPLAY SYSTEM")
        print("=" * 50)
        
        # Get configuration
        year, round_num, session_type, replay_mode = get_user_input()
        
        # Load session
        print("\n Loading session data...")
        loader = SessionLoader(year, round_num, session_type)
        
        if not loader.load_session():
            print(" Failed to load session. Check your internet connection.")
            return 1
        
        print(" Session loaded successfully!")
        
        # Select drivers
        driver_codes = select_drivers(loader)
        print(f"\n Selected {len(driver_codes)} drivers: {', '.join(driver_codes)}")
        
        # Load driver telemetry
        print("\nLoading telemetry data...")
        drivers = loader.load_all_drivers(driver_codes, replay_mode)
        
        if not drivers:
            print(" No valid driver data loaded.")
            return 1
        
        print(f" Loaded telemetry for {len(drivers)} drivers")
        
        # Get reference track
        print("Loading track layout...")
        track_telemetry = loader.get_reference_track()
        
        if track_telemetry is None:
            print(" Failed to load track layout.")
            return 1
        
        print(" Track layout loaded")
        
        # Create and start race replay
        print("\n Starting race replay...\n")
        replay = RaceReplay(drivers, track_telemetry)
        replay.start()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n Interrupted by user")
        return 0
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
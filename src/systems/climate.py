import math
import numpy as np
from src.engine.systems import System

class ClimateSystem(System):
    """
    Simulates realistic climate based on geographic location.
    - Latitude: Determines base temperature and seasonal variance.
    - Elevation: Lapse rate cooling (-6.5C per 1000m).
    - Seasons: Orbital mechanics approximation.
    """
    def update(self, state):
        # 1. Get Params from Globals (Defaults if not set)
        lat = state.globals.get('latitude', 45.0) # Degrees
        elevation = state.globals.get('elevation', 0.0) # Meters
        
        # 2. Orbital Mechanics (Day of Year 0-365)
        day_of_year = state.day % 365
        
        # 3. Calculate Temperature
        # Base Temp at Eqautor approx 30C, Poles approx -20C
        # Simple formula: T = 30 - 50 * sin(lat)^2 (approx)
        # Actually linear interpolation is easier to control for game:
        # Equator (0): 30C, Pole (90): -30C
        base_temp = 30.0 - (abs(lat) / 90.0 * 60.0)
        
        # Seasonal Swing
        # Swing amplitude increases with latitude
        # Equator: 0 variation. Poles: +/- 20 variation.
        season_amp = (abs(lat) / 90.0) * 20.0
        
        # Season Offset (Peak Summer day ~180 in N Hemisphere)
        # Cosine wave: +1 at 0, -1 at pi.
        # We want Peak at day 172 (June 21)
        phase = (day_of_year - 172) / 365.0 * 2 * math.pi
        seasonal_temp = -math.cos(phase) * season_amp
        
        if lat < 0: # Southern Hemisphere flips
            seasonal_temp *= -1
            
        # Elevation Lapse Rate
        # Standard: -6.5C per 1000m
        altitude_cooling = (elevation / 1000.0) * 6.5
        
        # Diurnal Cycle (Day/Night)
        # Peak heat at 2pm, min at 4am
        # Simplified: Sine wave based on hour (if we had hours)
        # Assume daily mean stored in globals
        
        daily_temp = base_temp + seasonal_temp - altitude_cooling
        
        # Adding randomness (Weather fronts)
        # Should be coherent day-to-day, but simple random for now
        weather_noise = np.random.normal(0, 2.0)
        
        current_temp = daily_temp + weather_noise
        
        # Update State
        state.globals['temperature'] = current_temp
        
        # Determine Biome (Simple classification logic)
        # Rainfall assumed static/random for now, or could map to lat (ITCZ, Horse Latitudes)
        # Let's simple heuristic for visualization
        if current_temp < -10:
            state.globals['biome'] = 'Tundra/Ice'
        elif current_temp < 0 and elevation > 2000:
            state.globals['biome'] = 'Alpine'
        elif current_temp > 25 and abs(lat) < 15:
            state.globals['biome'] = 'Tropical Rainforest'
        elif current_temp > 20 and abs(lat) < 30:
            state.globals['biome'] = 'Savanna'
        else:
            state.globals['biome'] = 'Temperate Forest'

        state.globals['is_night'] = False # Todo: Intra-day cycle

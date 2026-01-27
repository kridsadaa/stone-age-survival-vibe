import math
import numpy as np
import random
from src.engine.systems import System

class ClimateSystem(System):
    """
    Simulates realistic climate based on geographic location.
    - Latitude: Determines base temperature and seasonal variance.
    - Elevation: Lapse rate cooling (-6.5C per 1000m).
    - Seasons: Orbital mechanics approximation.
    """
    def update(self, state):
        # 1. Get Params
        lat = state.globals.get('latitude', 45.0)
        elevation = state.globals.get('elevation', 100.0)
        day_of_year = state.day % 365
        
        # 2. Orbital / Base Temp
        # Equator (0) -> 30C, Pole (90) -> -30C
        base_temp = 30.0 - (abs(lat) / 90.0 * 60.0)
        
        # Season Offset (Peak Day 172)
        season_amp = (abs(lat) / 90.0) * 20.0
        phase = (day_of_year - 172) / 365.0 * 2 * math.pi
        seasonal_temp = math.cos(phase) * season_amp
        if lat < 0: seasonal_temp *= -1
        
        altitude_cooling = (elevation / 1000.0) * 6.5
        
        # 3. Advanced Wether Generation
        # Random noise handles fronts
        weather_noise = np.random.normal(0, 2.0)
        
        # Humidity (0.0 - 1.0)
        # Higher at equator, lower at poles, random variance
        base_humid = 0.5 + (0.3 * math.cos(math.radians(lat))) # More humid at equator
        current_humid = np.clip(base_humid + np.random.normal(0, 0.2), 0.1, 1.0)
        
        # Cloud Cover (Correlated with Humidity)
        cloud_cover = 0.0
        if current_humid > 0.6:
            cloud_cover = (current_humid - 0.6) * 2.5 # 0.0 to 1.0
        
        # Precipitation
        precip = "None"
        if cloud_cover > 0.7 and random.random() < (current_humid * 0.5):
            # Rain or Snow?
            precip = "Rain"
            
        # Wind Speed (0 - 100 km/h)
        # Random storms
        wind_speed = abs(np.random.normal(10, 15)) 
        if random.random() < 0.05: wind_speed += 40 # Storm gust
        
        # 4. Temperature Final Calculation
        # Clouds trap heat at night, block sun at day.
        # Simple: Clouds reduce max temp
        temp_mod = 0
        if cloud_cover > 0.5: temp_mod = -3.0
        
        current_temp = base_temp + seasonal_temp - altitude_cooling + weather_noise + temp_mod
        
        if precip == "Rain" and current_temp < 0:
            precip = "Snow"
            
        # 5. UV Index Calculation (0 - 11+)
        # Factors: Latitude (Closer to 0 is higher), Season (Summer higher), Cloud Cover (Blocks), Elevation (Higher is worse)
        
        # Base UV by Lat (0 deg -> 10, 90 deg -> 0)
        uv_base = 10.0 * (1.0 - (abs(lat) / 90.0))
        
        # Season Multiplier (Summer 1.5x, Winter 0.5x)
        # Reuse phase cosine
        # If North Hem: Summer is max cosine.
        uv_season = 1.0 + (math.cos(phase) * 0.5 * (1 if lat >= 0 else -1))
        
        # Cloud Block
        uv_cloud = 1.0 - (cloud_cover * 0.8) # Clouds block up to 80%
        
        # Elevation Boost (+10% per 1000m)
        uv_elev = 1.0 + (elevation / 10000.0)
        
        current_uv = uv_base * uv_season * uv_cloud * uv_elev
        current_uv = max(0.0, current_uv)
        
        # Update State
        state.globals['temperature'] = current_temp
        state.globals['humidity'] = current_humid
        state.globals['wind_speed'] = wind_speed
        state.globals['precipitation'] = precip
        state.globals['uv_index'] = current_uv
        
        # Determine Biome (Keep existing logic but upgrade later)
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

        state.globals['is_night'] = False

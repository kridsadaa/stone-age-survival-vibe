from src.engine.systems import System
import pandas as pd
import numpy as np
import random

class MapSystem(System):
    """
    Manages World Terrain and Resources.
    Grid Size: 20x20 (Representing 100x100 world, so 5x5 units per block)
    """
    def update(self, state):
        # Initialize map if missing
        # Initialize map if missing OR if schema is outdated (missing x2)
        if not hasattr(state, 'map_data') or state.map_data is None:
            self._generate_map(state)
        elif 'x2' not in state.map_data.columns:
            state.log("🌍 Regenerating Map (Schema Update)...")
            self._generate_map(state)
            
        # Dynamic Map Updates & Regeneration
        # 1. Weather System (Realism Phase 5)
        current_weather = state.globals.get('weather', 'Sunny')
        
        # Weather Transition Logic (Markov Chain-ish)
        # Sunny: 80% stay, 20% Rain
        # Rain: 60% stay, 20% Sunny, 20% Storm
        # Storm: 50% stay, 50% Rain
        
        roll = random.random()
        new_weather = current_weather
        
        if current_weather == 'Sunny':
            if roll < 0.2: new_weather = 'Rain'
        elif current_weather == 'Rain':
            if roll < 0.2: new_weather = 'Sunny'
            elif roll > 0.8: new_weather = 'Storm'
        elif current_weather == 'Storm':
            if roll < 0.5: new_weather = 'Rain'
            
        if new_weather != current_weather:
            state.globals['weather'] = new_weather
            icon = {'Sunny': '☀️', 'Rain': '🌧️', 'Storm': '⛈️'}[new_weather]
            state.log(f"{icon} Weather changed to {new_weather}!")
            
        # 2. Get Season
        season = state.globals.get('season', 'Spring')
        regen_rate = 0.05 # 5% per tick base
        
        # Weather effects on Regrow
        if new_weather == 'Rain': regen_rate *= 1.5
        elif new_weather == 'Storm': regen_rate *= 1.2
        elif season == 'Winter': regen_rate = 0.0

            
        # 2. Regenerate Resources (Vectorized)
        if hasattr(state, 'map_data') and state.map_data is not None:
            df = state.map_data
            
            # Wood Regrows (Forests)
            df['res_wood'] += df['max_wood'] * regen_rate * 0.01
            df['res_wood'] = df[['res_wood', 'max_wood']].min(axis=1)
            
            # Food Regrows (Plants/Fish)
            df['res_food'] += df['max_food'] * regen_rate * 0.05
            df['res_food'] = df[['res_food', 'max_food']].min(axis=1)
            
            # Stone does NOT regrow (Finite resource?) Or extremely slow geological process?
            # Let's say no regrowth for stone to force exploration.


    def _generate_map(self, state):
        rows = []
        grid_size = 20
        scale = 100 / grid_size # 5.0
        
        # Simple Procedural Generation
        # 1. Base: Plains
        # 2. Add River (center vertical)
        # 3. Add Forest (Random patches)
        # 4. Add Mountains (North)
        # 5. Add Lake (South East)
        
        for x in range(grid_size):
            for y in range(grid_size):
                # Coordinates (Center of the block)
                real_x = x * scale + (scale/2)
                real_y = y * scale + (scale/2)
                
                terrain = 'Plains'
                color = '#C2B280' # Sand/Plains
                
                # Logic
                # Mountains at Top (y < 4)
                if y < 3:
                     if random.random() < 0.7:
                        terrain = 'Mountain'
                        color = '#8B8B8B'
                
                # Forest in Middle-Left (Red Tribe area)
                elif x < 8 and 5 < y < 15:
                    if random.random() < 0.6:
                         terrain = 'Forest'
                         color = '#228B22'
                         
                # Lake in Bottom-Right (Green Tribe area) - Shrink it
                elif x > 14 and y > 14:
                    if random.random() < 0.7:
                         terrain = 'Water'
                         color = '#4169E1'
                
                # River flowing from North(Mountain) to Lake - Make it meandering
                # Center around x=14, but wiggle
                river_center = 14 + int(np.sin(y/2) * 2) # Wiggle
                if x == river_center and y < 15: 
                     if random.random() < 0.95:
                        terrain = 'Water'
                        color = '#4169E1'
                        
                # Define tile bounds for explicit MarkRect
                # x/y is index. Scale is size.
                # Let's say (0,0) -> x=[0, 5], y=[0, 5]
                start_x = x * scale
                start_y = y * scale
                end_x = start_x + scale
                end_y = start_y + scale
                
                # Initialize Dynamic Resources (Max Capacity)
                res_wood = 0.0
                res_stone = 0.0
                res_food = 0.0
                
                if terrain == 'Forest':
                    res_wood = random.uniform(500.0, 1000.0)
                    res_food = random.uniform(200.0, 400.0)
                    res_stone = random.uniform(50.0, 100.0)
                elif terrain == 'Mountain':
                    res_wood = random.uniform(0.0, 50.0)
                    res_food = random.uniform(0.0, 50.0)
                    res_stone = random.uniform(800.0, 1500.0)
                elif terrain == 'Plains':
                    res_wood = random.uniform(10.0, 50.0)
                    res_food = random.uniform(100.0, 300.0)
                    res_stone = random.uniform(10.0, 30.0)
                elif terrain == 'Water':
                    res_food = random.uniform(500.0, 1000.0) # Fish
                
                rows.append({
                    'grid_x': x,
                    'grid_y': y,
                    'real_x': real_x, 
                    'real_y': real_y,
                    'x': start_x, 
                    'y': start_y,
                    'x2': end_x,
                    'y2': end_y,
                    'terrain': terrain,
                    'color': color,
                    'resource_bonus': 1.0,
                    # Current Resources
                    'res_wood': res_wood,
                    'res_stone': res_stone,
                    'res_food': res_food,
                    # Max Capacity (for regeneration)
                    'max_wood': res_wood,
                    'max_stone': res_stone,
                    'max_food': res_food
                })
                
        state.map_data = pd.DataFrame(rows)
        state.log("🌍 New World Terrain Generated!")
        
        # Optimize Lookup for SettlementSystem
        # Map: (grid_x, grid_y) -> terrain_type
        # Used for O(1) checking during movement
        lookup = {}
        for row in rows:
            lookup[(row['grid_x'], row['grid_y'])] = row['terrain']
            
        state.globals['terrain_lookup'] = lookup

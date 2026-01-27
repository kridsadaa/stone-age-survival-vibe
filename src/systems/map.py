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
            
        # Optional: Dynamic map updates (seasons affecting water/ice?)

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
                
                rows.append({
                    'grid_x': x,
                    'grid_y': y,
                    'real_x': real_x, # Center for point reference if needed 
                    'real_y': real_y,
                    'x': start_x, 
                    'y': start_y,
                    'x2': end_x,
                    'y2': end_y,
                    'terrain': terrain,
                    'color': color,
                    'resource_bonus': 1.0
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

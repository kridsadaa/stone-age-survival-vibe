import sys
import os
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.map import MapSystem
import pandas as pd

def run_map_test():
    print("Initializing Map Test Engine...")
    engine = SimulationEngine()
    
    # Systems
    engine.add_system(MapSystem())
    
    # Trigger Update to generate map
    engine.tick(force=True)
    
    # Verify Map Data
    if not hasattr(engine.state, 'map_data') or engine.state.map_data is None:
        print("FAIL: map_data is None.")
        return
        
    df = engine.state.map_data
    print(f"Map Generated: {len(df)} tiles (Expected 400 for 20x20).")
    
    if len(df) != 400:
        print(f"FAIL: Incorrect grid size {len(df)}")
        return
        
    # Check Terrain Types
    terrains = df['terrain'].unique()
    print(f"Terrain Types Found: {terrains}")
    
    required = ['Plains'] # At minimum
    for r in required:
        if r not in terrains:
            print(f"WARNING: No {r} found on map.")
            
    # Check Colors
    if 'color' not in df.columns:
        print("FAIL: Color column missing.")
        return

    # Check Bounds
    if 'x2' not in df.columns or 'y2' not in df.columns:
        print("FAIL: x2/y2 columns missing.")
        return
        
    print("SUCCESS: Map generated correctly with bounds.")
    print(df[['grid_x', 'grid_y', 'terrain', 'color', 'x', 'x2']].head())

if __name__ == "__main__":
    run_map_test()

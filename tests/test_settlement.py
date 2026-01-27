import sys
import os
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.settlement import SettlementSystem
from src.systems.tribe import TribalSystem
from src.loaders import generate_initial_state
import pandas as pd
import numpy as np

def run_settlement_test():
    print("Initializing Settlement Test Engine...")
    engine = SimulationEngine()
    
    # Systems
    engine.add_system(BiologySystem())
    engine.add_system(TribalSystem())
    engine.add_system(SettlementSystem())
    
    # Init Pop
    traits = pd.DataFrame() 
    engine.state.population = generate_initial_state(100, traits)
    
    df = engine.state.population
    
    # 1. Check Init Coordinates
    if 'x' not in df.columns or 'y' not in df.columns:
        print("FAIL: x/y columns missing.")
        return
        
    print("Spatial Columns Found.")
    
    # Check Tribe Locations
    reds = df[df['tribe_id'] == 'Red_Tribe']
    if not reds.empty:
        mx, my = reds['x'].mean(), reds['y'].mean()
        print(f"Red Tribe Mean Pos: ({mx:.1f}, {my:.1f}) [Target: Top-Left 20,20]")
        if mx > 50 or my > 50:
            print("WARNING: Red Tribe seems out of place.")
            
    blues = df[df['tribe_id'] == 'Blue_Tribe']
    if not blues.empty:
        mx, my = blues['x'].mean(), blues['y'].mean()
        print(f"Blue Tribe Mean Pos: ({mx:.1f}, {my:.1f}) [Target: Top-Right 80,20]")

    # 2. Run Movement
    print("Running 10 ticks of movement...")
    start_x = df['x'].copy()
    
    for _ in range(10):
        engine.tick(force=True)
        
    end_x = engine.state.population['x']
    
    diff = (end_x - start_x).abs().sum()
    print(f"Total Movement Delta: {diff:.2f}")
    
    if diff > 0:
        print("SUCCESS: Agents are moving.")
    else:
        print("FAIL: Agents are static.")

if __name__ == "__main__":
    run_settlement_test()

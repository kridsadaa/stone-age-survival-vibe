import time
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.disease import DiseaseSystem
from src.loaders import generate_initial_state

def run_benchmark(pop_size=1000, duration_sec=5):
    print(f"\n--- Benchmarking with {pop_size} agents for {duration_sec}s ---")
    
    engine = SimulationEngine()
    engine.add_system(BiologySystem())
    engine.add_system(DiseaseSystem())
    
    # Init
    pop_df = generate_initial_state(pop_size, pd.DataFrame()) # dummy traits
    engine.state.population = pop_df
    
    # Run
    engine.tps_limit = 10000 # No limit
    engine.simulation_speed = 0 # Max speed logic in engine might need tweak if 0 means unlimited?
    # Engine logic: 
    # if self.simulation_speed > 0:
    #   target_wait = (1.0 / (self.tps_limit * self.simulation_speed))
    # So if we set limit huge, wait is small.
    
    start_time = time.time()
    ticks = 0
    
    while time.time() - start_time < duration_sec:
        engine.tick()
        ticks += 1
        
    elapsed = time.time() - start_time
    tps = ticks / elapsed
    
    print(f"Total Ticks: {ticks}")
    print(f"TPS: {tps:.2f}")
    return tps

if __name__ == "__main__":
    run_benchmark(1000, 5)
    run_benchmark(5000, 5)

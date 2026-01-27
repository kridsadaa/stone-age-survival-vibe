
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.disease import DiseaseSystem
from src.systems.climate import ClimateSystem
from src.systems.economy import EconomySystem
from src.systems.genetics import GeneticsSystem
from src.systems.culture import CultureSystem
from src.systems.psychology import PsychologySystem
from src.systems.social import SocialSystem
from src.systems.politics import PoliticalSystem
from src.loaders import load_traits, generate_initial_state
import pandas as pd
import time

def run_repro():
    print("Initializing Engine...")
    engine = SimulationEngine()
    
    # Add Systems
    engine.add_system(BiologySystem())
    engine.add_system(DiseaseSystem())
    engine.add_system(ClimateSystem())
    engine.add_system(EconomySystem())
    engine.add_system(GeneticsSystem())
    # Note: app.py listed GeneticsSystem twice? I'll replicate that just in case it's relevant
    # engine.add_system(GeneticsSystem()) 
    engine.add_system(CultureSystem(brain_path="data/test_brain.pkl")) # Use test brain
    engine.add_system(PsychologySystem())
    engine.add_system(SocialSystem())
    engine.add_system(PoliticalSystem())
    
    # Load Data
    traits = load_traits('data/traits.csv')
    
    # Spawn Population
    init_pop = 500
    pop_df = generate_initial_state(init_pop, traits)
    engine.state.population = pop_df
    
    print("Starting Simulation Loop...")
    
    # Run for 100 ticks or until crash
    try:
        for i in range(1, 50): # Start from 1 to match Day
            engine.tick(force=True)
            print(f"Tick {i} (Day {engine.state.day}) complete.")
            time.sleep(0.01) # Small delay for buffer
    except Exception as e:
        print(f"CRASH CAUGHT IN REPRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_repro()

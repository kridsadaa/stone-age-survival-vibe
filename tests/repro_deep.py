
import sys
import os
import time
import traceback
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

def run_deep_repro():
    print("Initializing Deep Repro Engine...")
    engine = SimulationEngine()
    
    # EXACTLY matching app.py
    engine.add_system(BiologySystem())
    engine.add_system(DiseaseSystem())
    engine.add_system(ClimateSystem())
    engine.add_system(EconomySystem())
    engine.add_system(GeneticsSystem())
    engine.add_system(GeneticsSystem()) # Duplicate!
    engine.add_system(CultureSystem(brain_path="data/test_brain.pkl"))
    engine.add_system(PsychologySystem())
    engine.add_system(SocialSystem())
    engine.add_system(PoliticalSystem())
    
    # Load Data
    traits = load_traits('data/traits.csv')
    
    # Spawn Population
    init_pop = 500
    pop_df = generate_initial_state(init_pop, traits)
    engine.state.population = pop_df
    
    print("Starting Loop (200 ticks)...")
    
    try:
        for i in range(1, 201):
            engine.tick(force=True)
            if i % 10 == 0:
                print(f"Tick {i} (Day {engine.state.day}) - Alive: {len(engine.state.population[engine.state.population['is_alive']])}")
            time.sleep(0.001)
    except Exception as e:
        print("\n!!! CRASH DETECTED !!!")
        traceback.print_exc()

if __name__ == "__main__":
    run_deep_repro()

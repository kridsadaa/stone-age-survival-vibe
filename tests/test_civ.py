import sys
import os
sys.path.append(os.getcwd())
from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.tech import TechSystem
from src.systems.tribe import TribalSystem
from src.systems.knowledge import KnowledgeSystem
from src.loaders import load_traits, generate_initial_state
import pandas as pd
import time

def run_civ_test():
    print("Initializing Civilization Test Engine...")
    engine = SimulationEngine()
    
    # Add relevant systems
    # We need Biology/Age for correct functioning
    engine.add_system(BiologySystem()) 
    engine.add_system(TechSystem())
    engine.add_system(TribalSystem())
    engine.add_system(KnowledgeSystem())
    
    # Init Pop
    traits = pd.DataFrame() # Mock traits
    engine.state.population = generate_initial_state(100, traits)
    
    print(f"Initial Pop: {len(engine.state.population)}")
    
    # Check Tribe IDs
    tribes = engine.state.population['tribe_id'].unique()
    print(f"Tribes Found: {tribes}")
    if len(tribes) < 1:
        print("FAIL: No tribe_ids assigned!")
        return

    # Run loop
    print("Running 60 days (2 months)...")
    for i in range(60):
        engine.tick(force=True)
        if i % 10 == 0:
            score = engine.state.globals.get('evo_score', 0)
            era = engine.state.globals.get('era', 'Unknown')
            skills = len(engine.state.skills)
            print(f"Day {i}: Era={era}, EvoScore={score:.1f}, Skills/Memes={skills}")
            
    # Verify Knowledge
    if len(engine.state.skills) > 0:
        print("SUCCESS: Skills discovered/learned!")
        print(engine.state.skills.head())
    else:
        print("WARNING: No skills discovered in 60 days (Might be luck, or bug).")
        
    # Verify Tech
    if engine.state.globals.get('evo_score', 0) > 0:
        print("SUCCESS: Evo Score is being calculated.")
    else:
        print("FAIL: Evo Score is 0.")

if __name__ == "__main__":
    run_civ_test()

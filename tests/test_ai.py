import sys
import os
import shutil
from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.culture import CultureSystem
from src.loaders import load_traits, generate_initial_state

def run_test():
    brain_path = "tests/test_brain.pkl"
    if os.path.exists(brain_path):
        os.remove(brain_path)
        
    print("--- 🧠 AI Persistence Test ---")
    
    # Run 1: Generation 0
    print("\nRun 1: Initializing AI...")
    engine = SimulationEngine()
    engine.add_system(BiologySystem())
    culture = CultureSystem(brain_path=brain_path)
    engine.add_system(culture)
    
    # Mock efficient state
    engine.state.population = generate_initial_state(50, {}) # Small pop
    engine.state.globals['resources'] = 1000
    
    # Force some learning
    print("Simulating 30 days...")
    for _ in range(30):
        engine.update()
        
    print(f"Run 1 Brain Size: {len(culture.q_table)}")
    assert len(culture.q_table) > 0, "Brain should have learned something"
    
    # Force Save
    culture.save_brain()
    del engine
    del culture
    
    # Run 2: Generation 1 (Load Brain)
    print("\nRun 2: Loading Brain...")
    engine2 = SimulationEngine()
    culture2 = CultureSystem(brain_path=brain_path) # Should load
    
    print(f"Run 2 Brain Size: {len(culture2.q_table)}")
    assert len(culture2.q_table) > 0, "Brain should have loaded knowledge"
    
    # Check if policy exists
    policy = engine2.state.globals.get('policy_mating', 'FreeForAll') # Default
    # The culture system updates policy on update, so run once
    culture2.update(engine2.state)
    new_policy = engine2.state.globals.get('policy_mating')
    
    print(f"Policy Loaded: {new_policy}")
    print("✅ Persistence Test Passed!")
    
    # Cleanup
    if os.path.exists(brain_path):
        os.remove(brain_path)

if __name__ == "__main__":
    run_test()

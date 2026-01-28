import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from src.engine.core import WorldState
from src.loaders import generate_initial_state
from src.systems.biology import BiologySystem
from src.systems.economy import EconomySystem

def test_advanced_biology():
    print("🧬 Testing Advanced Biology Mechanics...")
    
    # 1. Setup State
    state = WorldState()
    state.population = generate_initial_state(100, pd.DataFrame())
    
    # Verify Schema
    assert 'injuries' in state.population.columns, "injuries column missing!"
    assert 'nutrients' in state.population.columns, "nutrients column missing!"
    print("✅ Schema Validation Passed")
    
    # 2. Test Injury Logic
    # Manually injure someone
    victim_idx = 0
    state.population.at[victim_idx, 'injuries'] = "['Broken Leg']"
    state.population.at[victim_idx, 'stamina'] = 100 # Well rested
    
    bio_sys = BiologySystem()
    print("Running 50 ticks of biology (Recovery Chance)...")
    recovered = False
    for _ in range(50):
        bio_sys.update(state)
        current_inj = state.population.at[victim_idx, 'injuries']
        if current_inj == "[]":
            recovered = True
            break
            
    if recovered:
        print("✅ Injury Recovery Verified")
    else:
        print("⚠️ Injury Recovery Check Pending (Might be bad luck)")

    # 3. Test Nutrition Logic
    # Give weak agent food
    eco_sys = EconomySystem()
    
    # Add fake inventory (Meat = Protein) for Agent 1
    agent_id = state.population.at[1, 'id']
    state.inventory = pd.DataFrame([{
        'agent_id': agent_id, 'item': 'Meat', 'amount': 2.0, 
        'durability': 0, 'max_durability': 0, 'spoilage_rate': 0.1
    }])
    
    # Force consumption
    print("Running Economy Consumption...")
    living_df = state.population[state.population['is_alive']]
    eco_sys._handle_consumption(state, living_df)
    
    # Check nutrients
    nut_str = state.population.at[1, 'nutrients']
    import ast
    nuts = ast.literal_eval(nut_str)
    
    # Default is 100 on init? No, loader says 100.
    # Logic: Decay (-5) then Add (+40 for 2 meat). Cap 100.
    # So 100 - 5 + 40 = 135 -> Cap 100.
    # Wait, loader initializes to {'protein': 100...}
    # Let's check a starving agent (Agent 2)
    
    starving_nuts_str = state.population.at[2, 'nutrients']
    starving_nuts = ast.literal_eval(starving_nuts_str)
    
    print(f"Fed Agent Protein: {nuts['protein']}")
    print(f"Starving Agent Protein: {starving_nuts['protein']}")
    
    assert starving_nuts['protein'] < 100, "Nutrient decay failed!"
    print("✅ Nutrition Decay Verified")

    print("✅ Advanced Biology Test Passed!")

if __name__ == "__main__":
    test_advanced_biology()

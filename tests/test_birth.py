import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.getcwd())

from src.engine.core import WorldState
from src.systems.biology import BiologySystem
from src.loaders import generate_initial_state

def test_birth_crash():
    print("👶 Testing Birth Logic Crash...")
    
    # Setup State
    state = WorldState()
    # Mock traits
    traits = pd.DataFrame({'name':[], 'survival_bonus':[]})
    state.population = generate_initial_state(50, traits)
    
    # Ensure columns exist that BiologySystem expects
    # 'tribe_id' is suspected missing from loaders.py
    if 'tribe_id' not in state.population.columns:
        print("⚠️ 'tribe_id' missing from initial state! Patching for test...")
        state.population['tribe_id'] = 'None'
        
    biology = BiologySystem()
    
    # Force a pregnancy
    # Find a female
    females = state.population[state.population['gender'] == 'Female']
    if females.empty:
        print("No females generated, skipping.")
        return
        
    mom_idx = females.index[0]
    state.population.at[mom_idx, 'is_pregnant'] = True
    state.population.at[mom_idx, 'pregnancy_days'] = 270 # Ready to birth
    state.population.at[mom_idx, 'age'] = 25
    state.population.at[mom_idx, 'stamina'] = 100
    
    # Force 'partner_id' if needed by logic
    state.population.at[mom_idx, 'partner_id'] = None
    
    print(f"Forcing birth for Agent {state.population.at[mom_idx, 'id']}")
    
    try:
        biology.update(state)
        print("✅ Biology Update (Birth) Passed!")
        
        # Check if baby exists
        babies = state.population[state.population['age'] == 0]
        if not babies.empty:
            print(f"✅ Created {len(babies)} babies.")
            print("Baby Columns:", babies.columns.tolist())
        else:
            print("❌ No babies created despite conditions met.")
            
    except Exception as e:
        print(f"❌ Crash during birth: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    test_birth_crash()

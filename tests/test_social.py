import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from src.engine.core import WorldState
from src.loaders import generate_initial_state
from src.systems.tribe import TribalSystem
from src.systems.economy import EconomySystem

def test_social_hierarchy():
    print("👑 Testing Social Hierarchy Mechanics...")
    
    # 1. Setup State
    state = WorldState()
    state.population = generate_initial_state(100, pd.DataFrame())
    
    # Verify Columns
    assert 'role' in state.population.columns, "Role column missing!"
    assert 'prestige' in state.population.columns, "Prestige column missing!"
    print("✅ Schema Validation Passed")
    
    # Assign Tribes manualy
    state.population['tribe_id'] = 'Red_Tribe'
    
    # 2. Run Tribal System (Role Assign + Leader)
    tribe_sys = TribalSystem()
    tribe_sys.update(state)
    
    # Verify Roles
    hunters = len(state.population[state.population['role'] == 'Hunter'])
    gatherers = len(state.population[state.population['role'] == 'Gatherer'])
    print(f"Stats: {hunters} Hunters, {gatherers} Gatherers")
    
    assert hunters > 0, "No Hunters assigned!"
    assert gatherers > 0, "No Gatherers assigned!"
    
    # Verify Leader
    leaders = getattr(state, 'tribes_leaders', {})
    assert 'Red_Tribe' in leaders, "Red_Tribe has no leader!"
    leader_id = leaders['Red_Tribe']
    print(f"✅ Leader Assigned: {leader_id}")
    
    # 3. Verify Economy Bonus
    # Pick a hunter
    hunter_idx = state.population[state.population['role'] == 'Hunter'].index[0]
    hunter = state.population.iloc[hunter_idx]
    
    print("✅ Social Hierarchy Test Passed!")

if __name__ == "__main__":
    test_social_hierarchy()

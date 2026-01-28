import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.getcwd())

from src.engine.core import WorldState
from src.loaders import generate_initial_state
from src.systems.map import MapSystem
from src.systems.economy import EconomySystem
from src.systems.settlement import SettlementSystem

def test_weather_system():
    print("🌪️ Testing Weather System...")
    
    # 1. Setup State
    state = WorldState()
    state.population = generate_initial_state(100, pd.DataFrame())
    state.map_data = pd.DataFrame() # Mock map
    
    # 2. Test Weather Cycling
    map_sys = MapSystem()
    print("Cycling weather...")
    
    weather_states = set()
    for _ in range(100):
        map_sys.update(state)
        w = state.globals.get('weather')
        if w: weather_states.add(w)
        
    print(f"Weather states seen: {weather_states}")
    assert 'Sunny' in weather_states, "Sunny weather missing"
    # Rain/Storm depend on RNG, might not trigger in 100 ticks but likely. 
    # Can't strictly assert Rain/Storm without mocking random.
    
    # 3. Test Effect on Settlement (Crash Check)
    print("Testing Settlement Movement with Weather...")
    settlement_sys = SettlementSystem()
    
    # Force Storm
    state.globals['weather'] = 'Storm'
    try:
        settlement_sys.update(state)
        print("✅ Settlement Update (Storm) Passed")
    except Exception as e:
        print(f"❌ Settlement Crash: {e}")
        raise e

    # 4. Test Effect on Economy (Risk)
    print("Testing Economy Risk (Storm)...")
    eco_sys = EconomySystem()
    state.inventory = pd.DataFrame() # Empty inv
    
    # Just ensure no crash on gathering
    try:
        eco_sys.update(state)
        print("✅ Economy Update (Storm) Passed")
    except Exception as e:
         print(f"❌ Economy Crash: {e}")
         raise e

    print("✅ Weather System Test Passed!")

if __name__ == "__main__":
    test_weather_system()

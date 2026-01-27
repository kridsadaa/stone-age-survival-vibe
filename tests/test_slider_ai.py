import sys
import os
from src.engine.core import SimulationEngine
from src.systems.culture import CultureSystem

def run_test():
    print("--- 🎚️ Dynamic AI Slider Test ---")
    
    # 1. Init
    brain_path = "tests/test_brain_slider.pkl"
    if os.path.exists(brain_path): os.remove(brain_path)
    
    engine = SimulationEngine()
    culture = CultureSystem(brain_path=brain_path)
    engine.add_system(culture)
    
    # Mock efficient state
    engine.state.day = 7 # Trigger update
    engine.state.population = engine.state.population # Empty is fine for checking logic flow
    engine.state.globals['resources'] = 500
    
    # 2. Check Initial State
    m_init = engine.state.globals.get('policy_mating_strictness', 0.5)
    r_init = engine.state.globals.get('policy_rationing_strictness', 0.5)
    print(f"Initial: M={m_init}, R={r_init}")
    
    assert m_init == 0.5
    
    # 3. Force Action (Mocking _choose_action/apply)
    # Action 0: M+, R+
    print("Forcing Action 0 (Both Increase)...")
    culture._apply_policy(engine.state, 0)
    
    m_new = engine.state.globals['policy_mating_strictness']
    r_new = engine.state.globals['policy_rationing_strictness']
    print(f"New: M={m_new:.2f}, R={r_new:.2f}")
    
    # Precision check
    assert abs(m_new - 0.6) < 0.001, "Mating should increase by 0.1"
    assert abs(r_new - 0.6) < 0.001, "Rationing should increase by 0.1"
    
    # 4. Force Action 8 (Both Decrease)
    print("Forcing Action 8 (Both Decrease)...")
    culture._apply_policy(engine.state, 8)
    
    m_final = engine.state.globals['policy_mating_strictness']
    r_final = engine.state.globals['policy_rationing_strictness']
    print(f"Final: M={m_final:.2f}, R={r_final:.2f}")
    
    assert abs(m_final - 0.5) < 0.001, "Should return to 0.5"
    
    print("✅ Slider Logic Verified!")
    if os.path.exists(brain_path): os.remove(brain_path)

if __name__ == "__main__":
    run_test()

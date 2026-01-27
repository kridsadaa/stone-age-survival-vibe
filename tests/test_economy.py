import sys
import os
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.inventory import InventorySystem
from src.systems.economy import EconomySystem
from src.systems.map import MapSystem
from src.loaders import generate_initial_state
import pandas as pd

def run_economy_test():
    print("Initializing Economy Test Engine...")
    engine = SimulationEngine()
    
    # Systems
    engine.add_system(MapSystem())
    engine.add_system(InventorySystem())
    engine.add_system(EconomySystem())
    
    # Init Pop with specific jobs
    traits = pd.DataFrame()
    engine.state.population = generate_initial_state(20, traits)
    # Force some jobs
    engine.state.population['job'] = 'Gatherer'
    engine.state.population['age'] = 20 # Healthy
    
    # Run Map Gen
    engine.tick(force=True)
    
    # Mock lookup if needed (or rely on MapSystem)
    if not hasattr(engine.state, 'map_data'):
         print("FAIL: Map not generated.")
         return
         
    # Run Economy Cycle (Gathering)
    print("Running 1 tick of Economy...")
    engine.tick(force=True)
    
    inv = engine.state.inventory
    print(f"Inventory Size: {len(inv)}")
    
    if inv.empty:
        print("FAIL: Inventory empty after gathering.")
        return
        
    print(inv.head())
    
    # Check item types
    items = inv['item'].unique()
    print(f"Items found: {items}")
    
    # Check Spoilage (Run 10 ticks)
    print("Running 10 ticks for spoilage...")
    initial_amt = inv.groupby('item')['amount'].sum()
    
    for _ in range(10):
        engine.tick(force=True)
        
    final_amt = engine.state.inventory.groupby('item')['amount'].sum()
    
    print("Spoilage Report:")
    for item in items:
        start = initial_amt.get(item, 0)
        end = final_amt.get(item, 0)
        print(f"  {item}: {start:.2f} -> {end:.2f} (Delta: {end-start:.2f})")

    # --- Crafting Test ---
    print("\n--- Crafting Test ---")
    # Grant materials to a specific agent
    test_id = engine.state.population.iloc[0]['id']
    engine.add_system(InventorySystem()) # Re-add helper if needed? No, it's there.
    
    # Manually add materials (using raw DF append for speed in test)
    new_rows = [
        {"agent_id": test_id, "item": "Wood", "amount": 5.0, "durability": 0, "max_durability": 0, "spoilage_rate": 0},
        {"agent_id": test_id, "item": "Stone", "amount": 5.0, "durability": 0, "max_durability": 0, "spoilage_rate": 0}
    ]
    engine.state.inventory = pd.concat([engine.state.inventory, pd.DataFrame(new_rows)], ignore_index=True)
    
    print(f"Agent {test_id} given 5 Wood, 5 Stone.")
    
    # Run Tick
    engine.tick(force=True)
    
    # Check Result
    inv = engine.state.inventory
    ag_inv = inv[inv['agent_id'] == test_id]
    
    has_spear = 'Spear' in ag_inv['item'].values
    wood_left = ag_inv[ag_inv['item'] == 'Wood']['amount'].sum()
    
    if has_spear:
        print("SUCCESS: Agent crafted a Spear!")
        print(f"Wood Left: {wood_left} (Expected ~3.0)")
    else:
        print("FAIL: No Spear crafted.")
        print(ag_inv)

if __name__ == "__main__":
    run_economy_test()

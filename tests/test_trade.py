import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.getcwd())

from src.engine.core import WorldState
from src.loaders import generate_initial_state
from src.systems.trade import TradeSystem

def test_trade_system():
    print("💰 Testing Trade System...")
    
    # 1. Setup State
    state = WorldState()
    state.population = generate_initial_state(2, pd.DataFrame()) # Only 2 agents
    
    buyer = state.population.iloc[0]
    seller = state.population.iloc[1]
    
    # Make them close
    state.population.at[0, 'x'] = 10.0
    state.population.at[0, 'y'] = 10.0
    state.population.at[1, 'x'] = 12.0 # Dist = 2
    state.population.at[1, 'y'] = 10.0
    
    # Make Buyer Need Food
    state.population.at[0, 'stamina'] = 10.0
    
    # Setup Inventory
    # Buyer has Wood (Payment)
    # Seller has Meat (Need)
    inv_data = [
        {'agent_id': buyer['id'], 'item': 'Wood', 'amount': 5.0, 'durability': 0, 'max_durability': 0, 'spoilage_rate': 0},
        {'agent_id': seller['id'], 'item': 'Meat', 'amount': 5.0, 'durability': 0, 'max_durability': 0, 'spoilage_rate': 0.1}
    ]
    state.inventory = pd.DataFrame(inv_data)
    
    # 2. Run Trade System
    trade_sys = TradeSystem()
    
    # We need to force update to trigger random trade.
    # Since it's random, we might need to loop a few times or Mock the random choice?
    # The logic in _handle_random_trades picks random samples. With 2 agents, it WILL pick them eventually.
    
    trade_occurred = False
    for i in range(10):
        print(f"Tick {i}...")
        trade_sys.update(state)
        
        # Check if Buyer has Meat
        buyer_meat = state.inventory[
            (state.inventory['agent_id'] == buyer['id']) & (state.inventory['item'] == 'Meat')
        ]
        if not buyer_meat.empty and buyer_meat.iloc[0]['amount'] >= 1.0:
            trade_occurred = True
            print("✅ Trade Verified: Buyer acquired Meat!")
            break
            
    if not trade_occurred:
        print("⚠️ Trade did not occur (Random chance failed or logic bug)")
        # Debug inventory
        print(state.inventory)
        assert False, "Trade failed"

    print("✅ Trade System Test Passed!")

if __name__ == "__main__":
    test_trade_system()

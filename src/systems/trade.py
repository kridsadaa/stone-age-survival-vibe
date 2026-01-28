from src.engine.systems import System
import pandas as pd
import numpy as np
import random

class TradeSystem(System):
    """
    Manages Barter Trade between Agents.
    Agents identify NEEDS (e.g., Hunger -> Need Food) and SURPLUS (e.g., Inventory > 5 -> Surplus).
    Trades happen between agents in the same cell.
    """
    def update(self, state):
        # 1. Identify Needs & Surplus
        # Optimized: Only process agents with > 2 items (Potential sellers) or < 20 stamina (Potential buyers)
        inv = state.inventory
        if inv.empty: return
        
        # 2. Matchmakers
        # Group by location (grid_x, grid_y)
        # Vectorized matching is hard, so we iterate over active cells?
        # Or simpler: Randomly pick N pairs to attempt trade
        
        # trade_attempts = 50
        # For simplicity in V1: Random encounters
        self._handle_random_trades(state)
        
    def _handle_random_trades(self, state):
        # Pick random agents with inventory
        if state.inventory.empty: return
        
        # Get active agents
        live_mask = state.population['is_alive'] == True
        population = state.population[live_mask]
        if len(population) < 2: return
        
        # Attempt 20 trades per tick
        for _ in range(20):
             # Pick 2 random agents
             buyer = population.sample(1).iloc[0]
             seller = population.sample(1).iloc[0]
             
             if buyer['id'] == seller['id']: continue
             
             # Spatial Check (dist < 10)
             dist = np.sqrt((buyer['x'] - seller['x'])**2 + (buyer['y'] - seller['y'])**2)
             if dist > 10.0: continue
             
             self._attempt_trade(state, buyer, seller)

    def _attempt_trade(self, state, buyer, seller):
        # 1. Identify Buyer Need
        # Priority: Food (if Stamina < 50) > Tools (if none)
        needed_item = None
        
        # Check Food
        if buyer['stamina'] < 50 or buyer['happiness'] < 50:
            # Need Food
            needed_item = 'Meat' # Prefer high value
        else:
            # Need Tool?
            needed_item = 'Spear'
            
        # 2. Check Seller Surplus
        # Does seller have it?
        seller_inv = state.inventory[state.inventory['agent_id'] == seller['id']]
        if seller_inv.empty: return
        
        has_item = seller_inv[seller_inv['item'] == needed_item]
        if has_item.empty or has_item.iloc[0]['amount'] < 1.0: return
        
        # 3. Determine Payment (Barter)
        # Buyer must give something of Value
        buyer_inv = state.inventory[state.inventory['agent_id'] == buyer['id']]
        if buyer_inv.empty: return
        
        # Simplistic: Give anything distinct
        payment_item = None
        for idx, row in buyer_inv.iterrows():
            if row['item'] != needed_item and row['amount'] >= 1.0:
                payment_item = row['item']
                break
        
        if payment_item:
            self._execute_trade(state, buyer['id'], seller['id'], needed_item, payment_item)
             
    def _execute_trade(self, state, buyer_id, seller_id, item_buy, item_pay):
        # 1. Seller gives Item -> Buyer
        # 2. Buyer gives Payment -> Seller
        
        # Use simple decrement/increment for now (assuming 1 unit trade)
        # In reality need to handle indices.
        
        # Seller -> Buyer (Item)
        seller_inv_idx = state.inventory[
            (state.inventory['agent_id'] == seller_id) & (state.inventory['item'] == item_buy)
        ].index[0]
        
        state.inventory.at[seller_inv_idx, 'amount'] -= 1.0
        
        # Add to Buyer
        # Check if exists
        buyer_has = state.inventory[
            (state.inventory['agent_id'] == buyer_id) & (state.inventory['item'] == item_buy)
        ]
        if not buyer_has.empty:
            state.inventory.at[buyer_has.index[0], 'amount'] += 1.0
        else:
            # New row
            new_row = {'agent_id': buyer_id, 'item': item_buy, 'amount': 1.0, 'durability': 0, 'max_durability': 0, 'spoilage_rate': 0.1}
            state.inventory = pd.concat([state.inventory, pd.DataFrame([new_row])], ignore_index=True)
            
        # Buyer -> Seller (Payment)
        buyer_pay_idx = state.inventory[
            (state.inventory['agent_id'] == buyer_id) & (state.inventory['item'] == item_pay)
        ].index[0]
        
        state.inventory.at[buyer_pay_idx, 'amount'] -= 1.0
        
         # Add to Seller
        seller_has = state.inventory[
            (state.inventory['agent_id'] == seller_id) & (state.inventory['item'] == item_pay)
        ]
        if not seller_has.empty:
            state.inventory.at[seller_has.index[0], 'amount'] += 1.0
        else:
            new_row = {'agent_id': seller_id, 'item': item_pay, 'amount': 1.0, 'durability': 0, 'max_durability': 0, 'spoilage_rate': 0.1}
            state.inventory = pd.concat([state.inventory, pd.DataFrame([new_row])], ignore_index=True)
            
        state.log(f"🤝 Trade: {buyer_id[-4:]} bought {item_buy} from {seller_id[-4:]} for {item_pay}")

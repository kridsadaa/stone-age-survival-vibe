from src.engine.systems import System
from src.systems.inventory import InventorySystem
import pandas as pd
import numpy as np
import random

class EconomySystem(System):
    """
    Handles economic activities:
    - Resource Gathering (Biome dependent)
    - Crafting (Wood/Stone -> Tools)
    - Consumption (Inventory based)
    """
    def update(self, state):
        df = state.population
        if df.empty: return
        live_mask = df['is_alive'] == True
        living_df = df[live_mask]
        
        # Access Inventory System helper (need to find instance or use static helper if we made one)
        # We'll instantiate a helper or just use direct dataframe manip for speed, 
        # but helper is cleaner for 'add_item'.
        # Let's verify if we can find the system instance or just assume logic here.
        # We can implement a local helper.
        
        # 1. Gathering Phase
        # 1. Gathering Phase
        self._handle_gathering(state, living_df)
        
        # 2. Crafting Phase
        self._handle_crafting(state, living_df)
        
        # 3. Consumption Phase
        self._handle_consumption(state, living_df)

    def _handle_crafting(self, state: 'WorldState', df: pd.DataFrame) -> None:
        # Recipes
        # Spear: 2 Wood + 1 Stone
        # Basket: 3 Wood
        
        inv = state.inventory
        if inv.empty or df.empty:
            return
        
        try:
            # Identify Potential Crafters
            # Filter inventory for materials
            materials = inv[inv['item'].isin(['Wood', 'Stone'])]
            if materials.empty: return

            
            # Agents who have materials
            agent_ids = materials['agent_id'].unique()
            
            updates = []
            drops = [] # Indices to drop from inventory
            
            for ag_id in agent_ids:
                # Get Agent's materials
                ag_mat = materials[materials['agent_id'] == ag_id]
                
                wood = ag_mat[ag_mat['item'] == 'Wood']['amount'].sum()
                stone = ag_mat[ag_mat['item'] == 'Stone']['amount'].sum()
                
                # Check for existing tools (prevent hoarding)
                # This requires full inventory check for this agent
                # Assume they make 1 if they can.
                
                # Recipe: Spear (Priority for Hunters)
                # 2 Wood + 1 Stone
                crafted = False
                if wood >= 2.0 and stone >= 1.0:
                     # Craft Spear
                     # Remove mats
                     # Logic isn't atomic here, need to update DF later. 
                     # For simulation speed, we'll just queue updates and assume no double-spend in one tick.
                     
                     # Add Spear
                     updates.append({
                        "agent_id": ag_id, "item": "Spear", "amount": 1, 
                        "durability": 50, "max_durability": 50, "spoilage_rate": 0
                     })
                     
                     # Consume materials (We need to find rows to reduce)
                     # This is tricky in loop.
                     # Let's simple-subtract from global DF using index found in Ag_Mat
                     crafted = True
                
                elif wood >= 3.0:
                     # Craft Basket
                     updates.append({
                        "agent_id": ag_id, "item": "Basket", "amount": 1, 
                        "durability": 30, "max_durability": 30, "spoilage_rate": 0
                     })
                     crafted = True
                     
                # If crafted, we should deduct materials.
                # Doing this correctly requires row-level manipulation.
                if crafted:
                     # Find rows to deduct wood/stone from this agent
                     # We need to access 'ag_mat' indices again
                     
                     # Deduct Wood
                     wood_needed = 2.0 if stone >= 1.0 else 3.0 # Spear vs Basket
                     wood_rows = ag_mat[ag_mat['item'] == 'Wood']
                     
                     remaining_cost = wood_needed
                     for idx, row in wood_rows.iterrows():
                         if remaining_cost <= 0: break
                         current = row['amount']
                         deduct = min(current, remaining_cost)
                         # Queue deduction? Can't queue easily if we iterate.
                         # Direct mod is okay here as we don't iterate main DF loop
                         state.inventory.at[idx, 'amount'] -= deduct
                         remaining_cost -= deduct
                         
                     # Deduct Stone (if Spear)
                     if stone >= 1.0 and wood_needed == 2.0:
                         stone_rows = ag_mat[ag_mat['item'] == 'Stone']
                         remaining_cost = 1.0
                         for idx, row in stone_rows.iterrows():
                             if remaining_cost <= 0: break
                             current = row['amount']
                             deduct = min(current, remaining_cost)
                             state.inventory.at[idx, 'amount'] -= deduct
                             remaining_cost -= deduct
            
            # Batch Add new items
            if updates:
                new_items = pd.DataFrame(updates)
                state.inventory = pd.concat([state.inventory, new_items], ignore_index=True)
        
        except (KeyError, ValueError, IndexError) as e:
            print(f"⚠️ [EconomySystem] Warning: Crafting failed - {e}")
            # Simulation continues even if crafting fails
            return
             
    def _handle_gathering(self, state: 'WorldState', df: pd.DataFrame) -> None:
        workers = df[(df['job'].isin(['Gatherer', 'Hunter', 'Fisherman'])) & (df['age'] > 5)]
        if workers.empty:
            return
        
        try:
            lookup = state.globals.get('terrain_lookup', {})
            scale = 5.0 
            
            updates = [] 
            durability_damage = [] # List of (index, damage)

            
            era = state.globals.get('era', 'Paleolithic')
            
            # Helper map: Agent -> Inventory Subset (Tools)
            # Pre-calc for performance
            inv = state.inventory
            tool_map = {}
            if not inv.empty:
                tools_df = inv[inv['item'].isin(['Spear', 'Basket'])]
                # We need indices to apply damage later
                # Group by agent?
                for idx, row in tools_df.iterrows():
                    aid = row['agent_id']
                    if aid not in tool_map: tool_map[aid] = []
                    tool_map[aid].append((row['item'], idx))

            for idx, agent in workers.iterrows():
                ax, ay = agent['x'], agent['y']
                gx, gy = int(ax // scale), int(ay // scale)
                terrain = lookup.get((gx, gy), 'Plains')
                
                # Check Tools
                tools = tool_map.get(agent['id'], [])
                has_spear = False
                has_basket = False
                spear_idx = -1
                basket_idx = -1
                
                for t_item, t_idx in tools:
                    if t_item == 'Spear': 
                        has_spear = True
                        spear_idx = t_idx
                    elif t_item == 'Basket': 
                        has_basket = True
                        basket_idx = t_idx

                # Yield Logic
                yield_amt = 1.0 + (agent['trait_conscientiousness'] * 0.5)
                
                # Apply Tool Bonuses
                tool_used_idx = -1
                if has_spear and terrain in ['Plains', 'Forest', 'Water']: 
                    yield_amt *= 2.0 
                    tool_used_idx = spear_idx
                elif has_basket and terrain in ['Forest', 'Plains']:
                    yield_amt *= 1.5 
                    tool_used_idx = basket_idx
                
                # Record Damage
                if tool_used_idx != -1:
                    durability_damage.append(tool_used_idx)

                items_found = []
                
                if terrain == 'Water':
                    items_found.append(('Fish', yield_amt * 2, 0.15)) 
                elif terrain == 'Forest':
                    items_found.append(('Fruit', yield_amt * 3, 0.1)) 
                    if random.random() < 0.3: items_found.append(('Wood', 1, 0.0)) 
                    if random.random() < 0.2: items_found.append(('Meat', yield_amt, 0.3)) 
                elif terrain == 'Mountain':
                    if random.random() < 0.5: items_found.append(('Stone', 1, 0.0))
                    if random.random() < 0.2: items_found.append(('Fruit', yield_amt, 0.1))     
                else: # Plains
                    if era != 'Paleolithic' and random.random() < 0.4:
                        items_found.append(('Grain', yield_amt * 2, 0.01)) 
                    if random.random() < 0.3: items_found.append(('Meat', yield_amt, 0.3))
                    else: items_found.append(('Fruit', yield_amt, 0.1))
                
                for item, amt, sp in items_found:
                    updates.append({
                        "agent_id": agent['id'], "item": item, "amount": amt, 
                        "durability": 0, "max_durability": 0, "spoilage_rate": sp
                    })
            
            # Apply Durability Damage (BEFORE adding new items to avoid index mismatch)
            if durability_damage and not state.inventory.empty:
                # -2 durability per use
                # Filter valid indices just in case
                valid_idx = [i for i in durability_damage if i in state.inventory.index]
                if valid_idx:
                     state.inventory.loc[valid_idx, 'durability'] -= 2.0

            # Apply Updates (New Items)
            if updates:
                new_items = pd.DataFrame(updates)
                state.inventory = pd.concat([state.inventory, new_items], ignore_index=True)
        
        except (KeyError, ValueError, IndexError) as e:
            print(f"⚠️ [EconomySystem] Warning: Gathering failed - {e}")
            # Continue simulation even if gathering fails
            return

    def _handle_consumption(self, state: 'WorldState', living_df: pd.DataFrame) -> None:
        # Agents need to eat.
        # Priority: Meat (spoils fast) > Fish > Fruit > Grain
        
        # Get Inventory
        inv = state.inventory
        if inv.empty: 
            # Fallback to global resources if inv empty (Legacy Support)
            # Or starve?
            # Let's support legacy global resources for 1-2 ticks
            return

        # Demand
        needed = 2.0 # Calories
        
        # Identify food holders
        # We need to process each agent or group?
        # Group by agent_id
        
        # Optimize: 
        # 1. Pivot Inventory to get columns: agent_id | Meat | Fish ...
        # 2. Vectorized subtraction
        # 3. Melt back?
        
        # Too complex. Let's interact with Global Pool for now to keep things moving?
        # No, user asked for inventory.
        
        # Simplified Consumption:
        # Just reduce random food from inventory.
        
        # Filter only food items
        food_items = ['Meat', 'Fish', 'Fruit', 'Grain']
        food_mask = inv['item'].isin(food_items)
        food_inv = inv[food_mask]
        
        if food_inv.empty: return
        
        # Sort by spoilage rate descending (Eat spoiling food first)
        # This global sort doesn't help per agent.
        
        # Let's do a trick: Group by Agent, Sum Total Food Amount.
        # If Total > Need, they survive. Remove Need amount from their high-spoilage items.
        
        # This is hard to vectorize perfectly.
        # Approximation:
        # Decrease ALL food amounts by a tiny fraction (Simulating grazing/snacking)? NO.
        
        # Let's go row-by-row for FOOD ITEMS only?
        # 500 agents * ~3 items = 1500 rows. Fast enough.
        
        # Complete food consumption logic
        # Food items and priority
        food_items = ['Meat', 'Fish', 'Fruit', 'Grain']
        food_priority = {'Meat': 3.0, 'Fish': 2.5, 'Fruit': 1.5, 'Grain': 1.0}
        
        # Process living agents
        for idx, agent in living_df.iterrows():
            agent_id = agent['id']
            needed = 2.0
            
            # Get agent's food sorted by spoilage
            agent_food = inv[
                (inv['agent_id'] == agent_id) & 
                (inv['item'].isin(food_items))
            ].sort_values(by='spoilage_rate', ascending=False)
            
            if agent_food.empty:
                state.population.at[idx, 'stamina'] -= 15.0
                continue
            
            consumed_calories = 0.0
            for food_idx, food_row in agent_food.iterrows():
                if consumed_calories >= needed: break
                
                item = food_row['item']
                avail = food_row['amount']
                val = food_priority.get(item, 1.0)
                
                eat_amt = min(avail, (needed - consumed_calories) / val)
                if eat_amt > 0:
                    state.inventory.at[food_idx, 'amount'] -= eat_amt
                    consumed_calories += eat_amt * val
            
            # Apply stamina effects
            if consumed_calories >= needed:
                state.population.at[idx, 'stamina'] += 10.0
            elif consumed_calories >= needed * 0.5:
                state.population.at[idx, 'stamina'] += 2.0
            else:
                state.population.at[idx, 'stamina'] -= (needed - consumed_calories) * 5.0

        # Cleanup zero amounts
        state.inventory = state.inventory[state.inventory['amount'] > 0.01].copy()
        state.inventory.reset_index(drop=True, inplace=True)
        return
        
        # Update alive agents stamina
        # Using index map
        
        # Optimization:
        # living_df matches on 'id'
        fed_mask = living_df['id'].isin(fed_agents)
        
        # Boost stamina for fed
        # Note: We need to access the main state.population, not the copy living_df
        # Use indices
        
        fed_indices = living_df[fed_mask].index
        state.population.loc[fed_indices, 'stamina'] += 10.0
        
        # Reduce food?
        # We should reduce food from inventory corresponding to consumption.
        # Ideally remove 2.0 units per agent.
        # We'll just Apply a flat tax to all food inventory for now to simulate consumption
        # InventorySystem already decays food. Let's add 'Consumption Rate' to natural decay?
        # No, that's spoilage.
        
        # Let's force reduce all food items by 0.5 (Eating)
        state.inventory.loc[food_mask, 'amount'] -= 0.5
        
        # Starving:
        starving_indices = living_df[~fed_mask].index
        state.population.loc[starving_indices, 'stamina'] -= 10.0

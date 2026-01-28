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
        
        # 4. Spatial Trade (New)
        self._handle_p2p_trade(state, living_df)

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
            
        # Guard against missing map (Fixes TypeError)
        if state.map_data is None or state.map_data.empty:
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
                
                # Checks
                role = agent.get('role', 'Gatherer')
                
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

                # Yield Logic (Base)
                yield_amt = 1.0 + (agent['trait_conscientiousness'] * 0.5)
                
                # Role Bonuses (Realism Phase 2)
                # Hunter: Base yield +50% for Meat/Leather
                # Gatherer: Base yield +50% for Fruit/Wood/Grain
                is_hunter = (role == 'Hunter')
                is_gatherer = (role == 'Gatherer')
                
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

                # Injury Chance (Realism Phase 3)
                # Forest/Mountain = Risky. Night = Very Risky (TODO: Day/Night)
                # Tools reduce risk
                base_risk = 0.0
                if terrain == 'Mountain': base_risk = 0.05
                elif terrain == 'Forest': base_risk = 0.03
                elif terrain == 'Water': base_risk = 0.02
                
                # Weather Risk (Realism Phase 5)
                weather = state.globals.get('weather', 'Sunny')
                if weather == 'Storm': base_risk *= 2.0
                elif weather == 'Rain': base_risk *= 1.2
                
                # Tools reduce risk
                if has_spear: base_risk *= 0.1 # Spear protects well
                elif has_basket: base_risk *= 0.8 # Basket helps slightly
                
                if random.random() < base_risk:
                     # Agent gets injured!
                     current_injuries = agent.get('injuries', "[]")
                     if current_injuries == "[]":
                         state.population.at[idx, 'injuries'] = "['Sprained Ankle']"
                         state.population.at[idx, 'hp'] -= 10.0
                         state.log(f"🩹 Agent {agent['id']} injured while gathering in {terrain}!")

                # Resource Depletion Logic (Realism Phase 1)
                map_idx = gx * 20 + gy
                if map_idx < 0 or map_idx >= len(state.map_data): map_idx = 0
                
                # Check resources
                tile_wood = state.map_data.at[map_idx, 'res_wood']
                tile_food = state.map_data.at[map_idx, 'res_food']
                tile_stone = state.map_data.at[map_idx, 'res_stone']
                
                items_found = []
                
                if terrain == 'Water':
                    # Fishing
                    if tile_food > 0:
                        amt = yield_amt * 2
                        if is_hunter: amt *= 1.5 # Hunter fishing bonus
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Fish', actual_amt, 0.15))
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                        
                elif terrain == 'Forest':
                    # Foraging/Wood
                    if tile_food > 0:
                        amt = yield_amt * 3
                        if is_gatherer: amt *= 1.5 # Gatherer bonus
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Fruit', actual_amt, 0.1)) 
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                        
                    if random.random() < 0.3 and tile_wood > 0: 
                        actual_amt = min(1.0, tile_wood)
                        if is_gatherer: actual_amt *= 1.2
                        items_found.append(('Wood', actual_amt, 0.0)) 
                        state.map_data.at[map_idx, 'res_wood'] -= actual_amt
                        
                    if random.random() < 0.2 and tile_food > 0: 
                        amt = yield_amt
                        if is_hunter: amt *= 1.5
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Meat', actual_amt, 0.3)) 
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                        
                elif terrain == 'Mountain':
                    if random.random() < 0.5 and tile_stone > 0: 
                        actual_amt = min(1.0, tile_stone)
                        items_found.append(('Stone', actual_amt, 0.0))
                        state.map_data.at[map_idx, 'res_stone'] -= actual_amt
                        
                    if random.random() < 0.2 and tile_food > 0: 
                        amt = yield_amt
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Fruit', actual_amt, 0.1))
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                        
                else: # Plains
                    if era != 'Paleolithic' and random.random() < 0.4 and tile_food > 0:
                        amt = yield_amt * 2
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Grain', actual_amt, 0.01)) 
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                        
                    if random.random() < 0.3 and tile_food > 0: 
                        amt = yield_amt
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Meat', actual_amt, 0.3))
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                    elif tile_food > 0: 
                        amt = yield_amt
                        actual_amt = min(amt, tile_food)
                        items_found.append(('Fruit', actual_amt, 0.1))
                        state.map_data.at[map_idx, 'res_food'] -= actual_amt
                
                for item, amt, sp in items_found:
                    if amt > 0: # Only add if we actually gathered something
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
        
        # Policy-based Distribution Priority
        # Decentralized Logic: 
        # Assign 'priority_score' based on Tribe Policy, then sort globally.
        # Policy-based Distribution Priority
        # Decentralized Logic: 
        # Assign 'priority_score' based on Tribe Policy, then sort globally.
        living_df = living_df.copy() # Fix SettingWithCopyWarning
        living_df['priority_score'] = 0.0
        
        if hasattr(state, 'tribes'):
             for tid, tdata in state.tribes.items():
                 pol = tdata.get('policies', {}).get('rationing_label', 'Communal')
                 t_mask = living_df['tribe_id'] == tid
                 
                 if pol == 'Meritocracy':
                     # Prestige based (High prestige first)
                     # Normalize to be competitive with other schemes? 
                     # Let's assume Prestige is 0-100 range.
                     living_df.loc[t_mask, 'priority_score'] = living_df.loc[t_mask, 'prestige'] * 2 # Boosted
                 elif pol == 'ChildFirst':
                     # Children first (Younger = Higher score)
                     # Max age ~80. 
                     living_df.loc[t_mask, 'priority_score'] = 200 - living_df.loc[t_mask, 'age']
                 else: # Communal
                     # Random shuffle equivalent
                     living_df.loc[t_mask, 'priority_score'] = np.random.uniform(0, 100, size=t_mask.sum())
        
        # Sort by priority (Highest Score Eats First)
        living_df = living_df.sort_values(by='priority_score', ascending=False)
        
        # Process living agents
        for idx, agent in living_df.iterrows():
            agent_id = agent['id']
            needed = 2.0
            
            # Get agent's food sorted by spoilage
            agent_food = inv[
                (inv['agent_id'] == agent_id) & 
                (inv['item'].isin(food_items))
            ].sort_values(by='spoilage_rate', ascending=False)
            
            consumed_calories = 0.0
            daily_nutrients = {'protein': 0, 'carbs': 0, 'vitamins': 0}

            if agent_food.empty:
                state.population.at[idx, 'stamina'] -= 15.0
                # Do NOT continue; must process nutrient decay below
            else:
                for food_idx, food_row in agent_food.iterrows():
                    if consumed_calories >= needed: break
                    
                    item = food_row['item']
                    avail = food_row['amount']
                    val = food_priority.get(item, 1.0)
                    
                    eat_amt = min(avail, (needed - consumed_calories) / val)
                    if eat_amt > 0:
                        state.inventory.at[food_idx, 'amount'] -= eat_amt
                        consumed_calories += eat_amt * val
                        
                        # Nutrient Intake (Realism Phase 3)
                        # Meat: Protein++
                        # Fish: Protein+, Vitamin+
                        # Fruit: Vitamin++, Carb+
                        # Grain: Carb++
                        if item == 'Meat':
                            daily_nutrients['protein'] += eat_amt * 20
                        elif item == 'Fish':
                            daily_nutrients['protein'] += eat_amt * 15
                            daily_nutrients['vitamins'] += eat_amt * 10
                        elif item == 'Fruit':
                            daily_nutrients['carbs'] += eat_amt * 10
                            daily_nutrients['vitamins'] += eat_amt * 20
                        elif item == 'Grain':
                            daily_nutrients['carbs'] += eat_amt * 30

            # Update Nutrients State
            # Parse - Update - Write Back (Slow but functional for Phase 3)
            try:
                import ast
                current_nuts = ast.literal_eval(agent.get('nutrients', "{'protein': 50, 'carbs': 50, 'vitamins': 50}"))
            except:
                current_nuts = {'protein': 50, 'carbs': 50, 'vitamins': 50}
                
            # Decay (Daily Burn)
            current_nuts['protein'] -= 5
            current_nuts['carbs'] -= 5
            current_nuts['vitamins'] -= 5
            
            # Add Intake
            current_nuts['protein'] += daily_nutrients['protein']
            current_nuts['carbs'] += daily_nutrients['carbs']
            current_nuts['vitamins'] += daily_nutrients['vitamins']
            
            # Cap at 100, Min 0
            for k in current_nuts:
                current_nuts[k] = max(0, min(100, current_nuts[k]))
                
            state.population.at[idx, 'nutrients'] = str(current_nuts)
            
            # Malnutrition Penalties
            is_malnourished = False
            if current_nuts['protein'] < 20: # Kwashiorkor (Weakness)
                state.population.at[idx, 'max_hp'] -= 0.5
                is_malnourished = True
            if current_nuts['vitamins'] < 20: # Scurvy (Bleeding)
                state.population.at[idx, 'hp'] -= 0.5
                is_malnourished = True
            if current_nuts['carbs'] < 20: # Weakness
                state.population.at[idx, 'stamina'] -= 10.0
                is_malnourished = True
                
            if is_malnourished and random.random() < 0.05:
                state.log(f"⚠️ Agent {agent_id} is suffering from malnutrition.", agent_id=agent_id, category='Health')



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

    def _handle_p2p_trade(self, state, df):
        # 4. Spatial Trade (Barter/Gifting)
        # Agents with surplus help neighbors in need (or trade for missing resources)
        
        if 'x' not in df.columns: return
        
        # Identify Needy (Food < 2.0 or missing tools)
        inv = state.inventory
        if inv.empty: return
        
        # Aggregate Food per agent
        food_items = ['Meat', 'Fish', 'Fruit', 'Grain']
        # Groupby is essential
        agent_food = inv[inv['item'].isin(food_items)].groupby('agent_id')['amount'].sum()
        
        # Needy: < 2.0 food
        needy_ids = agent_food[agent_food < 2.0].index.values
        
        if len(needy_ids) == 0: return
        
        needy_df = df[df['id'].isin(needy_ids)]
        rich_df = df[~df['id'].isin(needy_ids)]
        
        if rich_df.empty: return
        
        # Sample limit
        sample_needy = needy_df.sample(min(len(needy_df), 20))
        
        for _, beggar in sample_needy.iterrows():
            bx, by = beggar['x'], beggar['y']
            
            # Find neighbors < 20.0
            dx = rich_df['x'] - bx
            dy = rich_df['y'] - by
            dists_sq = dx*dx + dy*dy
            
            # Radius 20.0 (400 sq)
            neighbor_mask = dists_sq < 400.0
            potential_givers = rich_df[neighbor_mask]
            
            if potential_givers.empty: continue
            
            # Pick one
            giver = potential_givers.sample(1).iloc[0]
            giver_id = giver['id']
            
            # Execute Trade
            g_inv_mask = (inv['agent_id'] == giver_id) & (inv['item'].isin(food_items))
            if not g_inv_mask.any(): continue
            
            # Take one unit of whatever they have
            g_indices = inv[g_inv_mask].index
            item_idx = g_indices[0]
            
            item_name = inv.at[item_idx, 'item']
            amount_to_give = 1.0
            
            # Deduct
            inv.at[item_idx, 'amount'] -= amount_to_give
            if inv.at[item_idx, 'amount'] <= 0:
                inv.drop(item_idx, inplace=True)
                
            # Add to Beggar
            new_item = {
                "agent_id": beggar['id'], "item": item_name, "amount": amount_to_give, 
                "durability": 0, "max_durability": 0, "spoilage_rate": 0.1 
            }
            state.inventory = pd.concat([state.inventory, pd.DataFrame([new_item])], ignore_index=True)
            
            state.log(f"🤝 Trade: {beggar['id'][-4:]} bought {item_name} from {giver['id'][-4:]} for Promise", category='Economy')



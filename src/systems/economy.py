import pandas as pd
import numpy as np
from src.engine.systems import System

class EconomySystem(System):
    """
    Handles economic activities:
    - Resource Gathering (Food, Wood, Stone)
    - Consumption (Eating)
    - Production is influenced by Biome and Tech.
    """
    def update(self, state):
        df = state.population
        live_mask = df['is_alive'] == True
        
        # 1. Gathering (Food)
        # Only healthy enough people gather
        gatherers_mask = (df['job'] == 'Gatherer') & (df['age'] > 5) & live_mask
        num_gatherers = gatherers_mask.sum()
        
        if num_gatherers > 0:
            # Biome Modifier
            biome = state.globals.get('biome', 'Temperate Forest')
            base_yield = 10.0 # Calories per person per day
            
            if biome == 'Tropical Rainforest':
                base_yield = 15.0 # Abundant
            elif biome == 'Savanna':
                base_yield = 12.0
            elif biome == 'Tundra/Ice':
                base_yield = 2.0 # Harsh
            elif biome == 'Alpine':
                base_yield = 5.0
                
            # Season Modifier
            season = state.globals.get('season', 'Spring')
            if season == 'Winter':
                base_yield *= 0.5
            elif season == 'Autumn':
                base_yield *= 1.2 # Harvest
                
            total_food_gain = num_gatherers * base_yield
            
            # Add to Globals
            state.globals['resources'] += total_food_gain
            
            # Stamina Cost for working
            df.loc[gatherers_mask, 'stamina'] -= 5.0

        # 2. Consumption (Eating)
        # Everyone eats if food is available
        # Avg need ~2000 kcal? scaled down to game units e.g. 10 units
        food_demand = len(df[live_mask]) * 2.0 # Daily cost per person
        
        available_food = state.globals['resources']
        
        if available_food >= food_demand:
            # Everyone eats full
            state.globals['resources'] -= food_demand
            df.loc[live_mask, 'stamina'] += 20.0
            df.loc[live_mask, 'stamina'] = df.loc[live_mask, 'stamina'].clip(upper=100.0)
        else:
            # Famine Logic controlled by AI Rationing Slider
            strictness = state.globals.get('policy_rationing_strictness', 0.5)
            
            # Default: Everyone is equal (Low Priority)
            # We split population into Priority (A) and Non-Priority (B)
            
            priority_mask = pd.Series(False, index=df.index)
            
            if strictness > 0.3:
                # Workers First
                priority_mask |= (df['job'].isin(['Gatherer', 'Hunter', 'Builder']))
            
            if strictness > 0.6:
                # Protect Future (Pregnant & Children)
                priority_mask |= (df['is_pregnant']) | (df['age'] < 10)
                
            # If priority exists, feed them first
            # But ensure priority mask is within living mask
            priority_mask = priority_mask & live_mask
            others_mask = live_mask & (~priority_mask)
            
            # 1. Feed Priority
            p_count = priority_mask.sum()
            p_demand = p_count * 2.0
            
            if available_food >= p_demand:
                # Priority eats full
                df.loc[priority_mask, 'stamina'] += 20.0
                state.globals['resources'] -= p_demand
                available_food -= p_demand
                
                # Others share remainder
                o_count = others_mask.sum()
                if o_count > 0 and available_food > 0:
                     fraction = available_food / (o_count * 2.0)
                     df.loc[others_mask, 'stamina'] += (10.0 * fraction) # Reduced benefit
                     state.globals['resources'] = 0
                else:
                     # Others get nothing
                     pass
            else:
                # Even Priority starves a bit
                fraction = available_food / p_demand
                df.loc[priority_mask, 'stamina'] += (10.0 * fraction)
                state.globals['resources'] = 0
                # Others get absolutely nothing
            
            # Clamp all
            df.loc[live_mask, 'stamina'] = df.loc[live_mask, 'stamina'].clip(upper=100.0)
                
        # 3. Resource Gathering (Materials)
        # TODO: Implement Wood/Stone gathering for builders

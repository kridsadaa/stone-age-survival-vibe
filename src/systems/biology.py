import pandas as pd
import numpy as np
from src.engine.systems import System

class BiologySystem(System):
    """
    Handles the biological processes of the population:
    - Aging
    - Metabolism (Stamina decay)
    - Health Checks (Starvation damage)
    - Natural Death (Old age)
    """
    def update(self, state):
        df = state.population
        
        # Work only on living agents to save compute
        live_mask = df['is_alive'] == True
        if not live_mask.any():
            return

        # 1. Aging (1 Tick = 1 Day)
        df.loc[live_mask, 'age'] += (1/365.0)
        
        # 2. Metabolic Burn
        base_cost = 5.0
        
        # Seasonal Modifier
        season = state.globals.get('season', 'Spring')
        if season == 'Winter':
            # TODO: Check for Fire tech/warmth
            base_cost += 2.0
            
        # Apply Base Cost
        # We can do more complex vectorized calculations here later
        df.loc[live_mask, 'stamina'] -= base_cost
        
        # Personality Modifier (Extraversion burns more energy)
        if 'trait_extraversion' in df.columns:
            # Vectorized addition
            extra_burn = df.loc[live_mask, 'trait_extraversion'] * 1.5
            df.loc[live_mask, 'stamina'] -= extra_burn

        # 3. Starvation Logic (Negative Stamina -> HP Damage)
        # Identify who is starving
        starving_mask = (df['stamina'] < 0) & live_mask
        
        if starving_mask.any():
            # Damage
            df.loc[starving_mask, 'hp'] -= 5.0
            # Clamp stamina to 0
            df.loc[starving_mask, 'stamina'] = 0.0
            
        # 4. Death Logic
        # A. Health Failure
        dead_hp_mask = (df['hp'] <= 0) & live_mask
        if dead_hp_mask.any():
            df.loc[dead_hp_mask, 'is_alive'] = False
            df.loc[dead_hp_mask, 'cause_of_death'] = 'Health Failure'
            state.log(f"☠️ {dead_hp_mask.sum()} villagers died of health failure.")

        # B. Old Age
        # Chance starts at 80
        elderly_mask = (df['age'] > 80) & (df['is_alive'] == True)
        if elderly_mask.any():
            # Calculate probabilities
            # Annual chance approx 10% base + 2% per year over 80
            # Daily chance = Annual / 365
            ages = df.loc[elderly_mask, 'age']
            annual_chance = 0.10 + ((ages - 80) * 0.02)
            daily_chance = annual_chance / 365.0
            
            # Roll dice
            rolls = np.random.random(len(ages))
            old_age_deaths = rolls < daily_chance
            
            # Apply death
            if old_age_deaths.any():
                # Get indices of those who died
                dead_indices = elderly_mask.index[old_age_deaths] # This mapping in pandas is tricky
                # elderly_mask is a boolean Series. 
                # ages is a Series slice. 
                # rolls is numpy array matching ages length.
                
                # Safer generic way:
                # 1. Get subset dataframe
                target_subset = df.loc[elderly_mask]
                # 2. Filter by dice roll
                dying_ids = target_subset[old_age_deaths].index
                
                if len(dying_ids) > 0:
                    df.loc[dying_ids, 'is_alive'] = False
                    df.loc[dying_ids, 'cause_of_death'] = 'Old Age'
                    state.log(f"🕊️ {len(dying_ids)} elders passed away peacefully.")

import pandas as pd
import numpy as np
import random
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

        if 'mother_id' not in df.columns: df['mother_id'] = None
        if 'father_id' not in df.columns: df['father_id'] = None
        if 'partner_id' not in df.columns: df['partner_id'] = None
        if 'family_id' not in df.columns: df['family_id'] = None
        
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

        if 'genetic_vulnerability' in df.columns:
            # High vulnerability = Higher metabolic cost (Inefficient body)
            vul_mask = (df['genetic_vulnerability'] > 0.5) & live_mask
            if vul_mask.any():
                # Penalize up to +50% cost
                penalty = df.loc[vul_mask, 'genetic_vulnerability'] * 2.5 
                df.loc[vul_mask, 'stamina'] -= penalty

        # 3. Starvation Logic (Negative Stamina -> HP Damage)
        # Identify who is starving
        starving_mask = (df['stamina'] < 0) & live_mask
        
        if starving_mask.any():
            # Damage
            df.loc[starving_mask, 'hp'] -= 5.0
            # Clamp stamina to 0
            df.loc[starving_mask, 'stamina'] = 0.0
            
        # 3.5 Natural Healing
        # If Fed (Stamina > 80) and Not Old (< 60)
        # TODO: Check for active disease? (Complex)
        healing_mask = (df['stamina'] > 80) & (df['age'] < 60) & (df['hp'] < df['max_hp']) & live_mask
        if healing_mask.any():
            df.loc[healing_mask, 'hp'] += 1.0
            # Cap at Max HP
            # Vectorized cap requires matching index or simple clip if max_hp is scalar (but it's column)
            # df.loc[healing_mask, 'hp'] = df.loc[healing_mask, ['hp', 'max_hp']].min(axis=1) # Slower
            # Simplified: active cap
            current_hp = df.loc[healing_mask, 'hp']
            max_hp = df.loc[healing_mask, 'max_hp']
            df.loc[healing_mask, 'hp'] = np.minimum(current_hp, max_hp)
            
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

        # 5. Reproduction (Scientific Model)
        self._handle_reproduction(state, df, live_mask)

    def _handle_reproduction(self, state, df, live_mask):
        # Constants
        GESTATION_PERIOD = 270 # Days (9 months)
        FERTILITY_MIN_AGE_F = 15
        FERTILITY_MAX_AGE_F = 45
        FERTILITY_MIN_AGE_M = 15
        FERTILITY_MAX_AGE_M = 60
        
        # A. Handle Pregnancies
        pregnant_mask = (df['is_pregnant'] == True) & live_mask
        if pregnant_mask.any():
            # Advance pregnancy
            df.loc[pregnant_mask, 'pregnancy_days'] += 1
            
            # Birth Check
            birth_mask = (df['pregnancy_days'] >= GESTATION_PERIOD) & pregnant_mask
            if birth_mask.any():
                num_births = birth_mask.sum()
                mothers = df.loc[birth_mask]
                
                # Reset Mother
                df.loc[birth_mask, 'is_pregnant'] = False
                df.loc[birth_mask, 'pregnancy_days'] = 0
                
                # Create Children
                import uuid
                new_ids = [f"HMN-{str(uuid.uuid4())[:8]}" for _ in range(num_births)]
                new_genders = np.random.choice(['Male', 'Female'], size=num_births)
                
                # Inheritance Logic (Simple average of traits + mutation)
                # For now random, later match with partner_id
                
                new_babies = pd.DataFrame({
                    "id": new_ids,
                    "age": np.zeros(num_births),
                    "gender": new_genders,
                    "job": "Child",
                    "hp": 100.0, "max_hp": 30.0, # Babies are fragile
                    "stamina": 50.0,
                    "is_alive": True,
                    "is_pregnant": False, "pregnancy_days": 0,
                    "partner_id": None,
                    "mother_id": mothers['id'].values,
                    "father_id": mothers['partner_id'].values if 'partner_id' in mothers.columns else None, # Needs partner tracking fix
                    "family_id": mothers['family_id'].values, # Inherit family
                    "cause_of_death": None,
                    # Random Traits
                    "trait_openness": np.random.random(num_births),
                    "trait_conscientiousness": np.random.random(num_births),
                    "trait_extraversion": np.random.random(num_births),
                    "trait_agreeableness": np.random.random(num_births),
                    "trait_neuroticism": np.random.random(num_births),
                })
                
                # Append to Population
                state.population = pd.concat([state.population, new_babies], ignore_index=True)
                state.log(f"👶 {num_births} new babies were born!")

        # B. Conception Logic
        # Population Cap Check (Soft)
        if len(df[live_mask]) > 2000: return
        
        # Find Eligible Women
        # Not pregnant, Age 15-45, Healthy (Stamina > 50) as proxy for Ovulation health
        eligible_women = (
            (df['gender'] == 'Female') &
            (df['age'] >= FERTILITY_MIN_AGE_F) &
            (df['age'] <= FERTILITY_MAX_AGE_F) &
            (df['is_pregnant'] == False) &
            (df['stamina'] > 50) &
            live_mask
        )
        
        # Find Eligible Men
        eligible_men_count = (
            (df['gender'] == 'Male') &
            (df['age'] >= FERTILITY_MIN_AGE_M) &
            (df['age'] <= FERTILITY_MAX_AGE_M) &
            live_mask
        ).sum()
        
        if eligible_women.any() and eligible_men_count > 0:
            # Chance of conception per day
            base_chance = 0.007
            
            rng = np.random.random(len(df)) # Use full length mask for alignment simplified
            # Re-masking
            women_indices = df[eligible_women].index
            
            # Roll for each eligible woman
            conceptions = []
            for w_idx in women_indices:
                if random.random() < base_chance:
                    conceptions.append(w_idx)
            
            if conceptions:
                # Assign Partners
                eligible_men_ids = df[
                    (df['gender'] == 'Male') &
                    (df['age'] >= FERTILITY_MIN_AGE_M) &
                    (df['age'] <= FERTILITY_MAX_AGE_M) &
                    live_mask
                ]['id'].values
                
                if len(eligible_men_ids) == 0: return

                policy = state.globals.get('policy_mating', 'FreeForAll')
                
                valid_pregnancies = []
                final_partners = []
                
                # Optimization: Pre-fetch men data for O(1) lookup
                # This prevents O(N) scan inside the loop
                men_data = df.loc[df['id'].isin(eligible_men_ids)].set_index('id')
                
                # Pick candidates
                # Optimization: Block process per woman
                for w_idx in conceptions:
                    partner_cand = random.choice(eligible_men_ids)
                    
                    woman = df.loc[w_idx]
                    
                    # Fast Lookup
                    partner = men_data.loc[partner_cand]
                    
                    is_incest = False
                    
                    # Incest Check
                    # 1. Sibling (Share Mom or Dad)
                    # Handle Nan/None carefully
                    w_mom = woman['mother_id']
                    w_dad = woman['father_id']
                    p_mom = partner['mother_id']
                    p_dad = partner['father_id']
                    
                    if (w_mom is not None and w_mom == p_mom) or \
                       (w_dad is not None and w_dad == p_dad):
                        is_incest = True
                        
                    # 2. Parent-Child
                    if w_mom == partner_cand or w_dad == partner_cand or \
                       p_mom == woman['id'] or p_dad == woman['id']:
                        is_incest = True
                        
                    # Policy Enforcer (Dynamic Slider)
                    strictness = state.globals.get('policy_mating_strictness', 0.5)
                    approved = True
                    
                    # Level 1: Anti-Incest (Strictness > 0.4)
                    if strictness > 0.4 and is_incest:
                        approved = False
                        
                    # Level 2: Eugenics (Strictness > 0.8)
                    # Reject if either parent has high genetic vulnerability
                    if strictness > 0.8:
                        w_vul = woman.get('genetic_vulnerability', 0.0)
                        p_vul = partner.get('genetic_vulnerability', 0.0)
                        # Nan safety
                        if pd.isna(w_vul): w_vul = 0.0
                        if pd.isna(p_vul): p_vul = 0.0
                        
                        if w_vul > 0.4 or p_vul > 0.4:
                            approved = False
                    
                    if approved:
                        valid_pregnancies.append(w_idx)
                        final_partners.append(partner_cand)
                
                # Apply
                if valid_pregnancies:
                    df.loc[valid_pregnancies, 'is_pregnant'] = True
                    df.loc[valid_pregnancies, 'pregnancy_days'] = 0
                    df.loc[valid_pregnancies, 'partner_id'] = final_partners

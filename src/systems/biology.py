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
            # Check for Fire technology
            unlocked_techs = state.globals.get('unlocked_techs', [])
            has_fire = 'Fire Control' in unlocked_techs or 'Fire' in unlocked_techs
            
            if has_fire:
                # Fire provides warmth - 50% reduction in winter penalty
                base_cost += 1.0
            else:
                # Full winter penalty without fire
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
            
        # 3.1 Environmental Effects (Evolutionary Pressure)
        uv_index = state.globals.get('uv_index', 0.0)
        
        # A. Sunburn (High UV)
        if uv_index > 7.0:
            # Pale skin burns
            # Threshold: skin_tone < 0.3 (Very pale)
            # Damage increases with UV and lack of melanin
            burn_mask = (df['skin_tone'] < 0.3) & live_mask
            if burn_mask.any():
                # Damage = (UV - 7) * (1 - skin_tone)
                # e.g. UV 10, Skin 0.1 -> 3 * 0.9 = 2.7 dmg
                burn_dmg = (uv_index - 7.0) * (0.5 - df.loc[burn_mask, 'skin_tone'])
                burn_dmg = np.clip(burn_dmg, 0.0, 5.0)
                df.loc[burn_mask, 'hp'] -= burn_dmg
                
        # B. Vitamin D Deficiency (Low UV)
        elif uv_index < 2.0:
            # Dark skin cannot synthesize Vit D
            # Threshold: skin_tone > 0.7
            defic_mask = (df['skin_tone'] > 0.7) & live_mask
            if defic_mask.any():
                # Slow decay of health (Rickets/Immune fail)
                df.loc[defic_mask, 'hp'] -= 0.5
            
        # 3.5 Natural Healing
        # If Fed (Stamina > 80) and Not Old (< 60)
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
            
        # 3.8 Injury Recovery (Realism Phase 3)
        # 5% chance to recover from injury if resting (Stamina > 50)
        # Note: Injuries are stored as string "['Broken Leg']" or empty "[]"
        # Parsing string list is slow, so we'll do simple string check
        injured_mask = (df['injuries'] != "[]") & live_mask
        if injured_mask.any():
            # Chance to recover
            recovering = (np.random.random(len(df)) < 0.05) & injured_mask & (df['stamina'] > 50)
            if recovering.any():
                # For now simply clear all injuries
                df.loc[recovering, 'injuries'] = "[]"
                # state.log("🩹 Some agents recovered from injuries")
                
            # Apply Injury Effects (Health Drain)
            # Anyone still injured loses small HP
            still_injured = injured_mask & ~recovering
            if still_injured.any():
                df.loc[still_injured, 'hp'] -= 0.2
                df.loc[still_injured, 'stamina'] -= 1.0
            
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

    def _handle_reproduction(self, state: 'WorldState', df: pd.DataFrame, live_mask: pd.Series) -> None:
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
                
                new_babies = pd.DataFrame({
                    "id": new_ids,
                    "age": np.zeros(num_births),
                    "gender": new_genders,
                    "job": "Child",
                    "role": "Child",
                    "hp": 30.0, 
                    "max_hp": 30.0,
                    "stamina": 50.0,
                    "prestige": 0.0,
                    "is_alive": True,
                    "is_pregnant": False, "pregnancy_days": 0,
                    "partner_id": None,
                    "mother_id": mothers['id'].values,
                    "family_id": mothers['family_id'].values, 
                    "cause_of_death": None,
                    # Realism Phase 6
                    "parents": [str([mid]) for mid in mothers['id'].values],
                    "children": "[]",
                    "injuries": "[]",
                    "nutrients": "{'protein': 100, 'carbs': 100, 'vitamins': 100}",
                    # Inherited Traits (Mutation)
                    "trait_openness": np.clip(mothers['trait_openness'].values + np.random.normal(0, 0.1, num_births), 0.0, 1.0),
                    "trait_conscientiousness": np.clip(mothers['trait_conscientiousness'].values + np.random.normal(0, 0.1, num_births), 0.0, 1.0),
                    "trait_extraversion": np.clip(mothers['trait_extraversion'].values + np.random.normal(0, 0.1, num_births), 0.0, 1.0),
                    "trait_agreeableness": np.clip(mothers['trait_agreeableness'].values + np.random.normal(0, 0.1, num_births), 0.0, 1.0),
                    "trait_neuroticism": np.clip(mothers['trait_neuroticism'].values + np.random.normal(0, 0.1, num_births), 0.0, 1.0),
                    # Location
                    "x": mothers['x'].values,
                    "y": mothers['y'].values,
                    "tribe_id": mothers['tribe_id'].values
                })
                
                # Append to Population
                state.population = pd.concat([state.population, new_babies], ignore_index=True)
                state.log(f"👶 {num_births} new babies were born!")

        # B. Conception Logic
        # Population Cap Check (Soft)
        if len(df[live_mask]) > 2000: return        # Policy Check: Handled per-tribe below
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
        
        # Apply Policy Modifiers to Libido (Interest Chance)
        # Open Policy -> Higher interest
        # Strict Policy -> Lower interest (controlled)
        libido_mod = pd.Series(1.0, index=df.index)
        if hasattr(state, 'tribes'):
             for tid, tdata in state.tribes.items():
                 # Default Strict if missing
                 pol = tdata.get('policies', {}).get('mating_label', 'Strict')
                 t_mask = df['tribe_id'] == tid
                 if pol == 'Open':
                     libido_mod[t_mask] = 2.0 # Double interest
                 else:
                     libido_mod[t_mask] = 0.8 # Slightly less random mating
        
        # Update DF temporary (or just use in calculation)
        # We can't update DF directly if we don't want to persist.
        # Just use in calculation.
        
        # Find Eligible Men
        eligible_men_count = (
            (df['gender'] == 'Male') &
            (df['age'] >= FERTILITY_MIN_AGE_M) &
            (df['age'] <= FERTILITY_MAX_AGE_M) &
            live_mask
        ).sum()
        
        if eligible_women.any() and eligible_men_count > 0:
            # Chance of "Interest" per day (Base Libido check)
            # Use Libido attribute if available, else default 0.5
            if 'libido' not in df.columns: df['libido'] = 0.5
            if 'attractiveness' not in df.columns: df['attractiveness'] = 0.5
            
            # Vectorized Interest Check
            # Roll < 0.01 * Libido
            # High Libido (0.9) = 0.9% daily chance. Low (0.1) = 0.1% chance.
            interest_rolls = np.random.random(len(df))
            interest_threshold = df['libido'] * 0.02 * libido_mod # Policy multiplier
            
            interested_mask = eligible_women & (interest_rolls < interest_threshold)
            
            if not interested_mask.any():
                return
                
            women_indices = df[interested_mask].index
            
            # Prepare Men Pool (Candidate list)
            # Optimization: Pre-fetch men data
            eligible_men_ids = df[
                (df['gender'] == 'Male') &
                (df['age'] >= FERTILITY_MIN_AGE_M) &
                (df['age'] <= FERTILITY_MAX_AGE_M) &
                live_mask
            ]['id'].values
            
            if len(eligible_men_ids) == 0: return

            men_data = df.loc[df['id'].isin(eligible_men_ids)].copy().set_index('id')
            
            # Policy Strictness
            strictness = state.globals.get('policy_mating_strictness', 0.5)
            
            valid_pregnancies = []
            final_partners = []
            
            # Iterate interested women
            for w_idx in women_indices:
                woman = df.loc[w_idx]
                
                # 0. Spatial Check (Love in the vicinity)
                # Only consider men within range (e.g. 20 units)
                nearby_men_ids = eligible_men_ids
                
                if 'x' in df.columns and 'y' in df.columns:
                    wx, wy = woman['x'], woman['y']
                    # Calculate vector distance to all eligible men
                    # men_data is indexed by ID
                    mx = men_data['x']
                    my = men_data['y']
                    dists = np.sqrt((mx - wx)**2 + (my - wy)**2)
                    
                    # Filter
                    nearby_men_ids = dists[dists < 20.0].index.values
                    
                if len(nearby_men_ids) == 0: continue

                # 1. Pick Candidates (Sample 3 men to evaluate)
                # "The Dating Scene"
                sample_size = min(3, len(nearby_men_ids))
                candidates_ids = np.random.choice(nearby_men_ids, size=sample_size, replace=False)
                
                best_partner = None
                best_score = -1.0
                
                for m_id in candidates_ids:
                    man = men_data.loc[m_id]
                    
                    # --- ATTRACTION ALGORITHM ---
                    
                    # A. Physical (40%)
                    # 1. Genetic Compatibility (Low Vulnerability is attractive)
                    # 2. Health (HP/Stamina)
                    # 3. Attractiveness Stat (Face/Body)
                    # 4. Skin Tone Preference (Assortative: Similar attracts - debatable but standard model)
                    
                    w_vul = woman.get('genetic_vulnerability', 0.1)
                    m_vul = man.get('genetic_vulnerability', 0.1)
                    vul_score = 1.0 - ((w_vul + m_vul) / 2.0) # Lower vul = Higher score
                    
                    health_score = (man['hp'] / man['max_hp'])
                    attr_stat = man.get('attractiveness', 0.5)
                    
                    # Skin Tone Match (1.0 = Same, 0.0 = Opposite)
                    # Let's say 70% prefer similar, 30% random 'exotic' preference? 
                    # Simple: Just use similarity for now
                    w_skin = woman.get('skin_tone', 0.5)
                    m_skin = man.get('skin_tone', 0.5)
                    skin_sim = 1.0 - abs(w_skin - m_skin)
                    
                    physical_score = (0.2 * vul_score) + (0.3 * health_score) + (0.4 * attr_stat) + (0.1 * skin_sim)
                    
                    # B. Status (30%)
                    # Job Prestige
                    job_rank = {'Chief': 1.0, 'Healer': 0.8, 'Builder': 0.6, 'Hunter': 0.6, 'Gatherer': 0.4, 'Child': 0.0}
                    status_score = job_rank.get(man['job'], 0.4)
                    
                    # Age Penalty (Too old/Too young gaps)
                    age_diff = abs(woman['age'] - man['age'])
                    if age_diff > 15: status_score *= 0.7 # Penalty for huge gap
                    
                    # C. Chemistry (30%)
                    chemistry = random.random()
                    
                    # TOTAL
                    total_score = (0.4 * physical_score) + (0.3 * status_score) + (0.3 * chemistry)
                    
                if not interested_mask.any():
                    return
                    
                women_indices = df[interested_mask].index
                
                # Prepare Men Pool (Candidate list)
                # Optimization: Pre-fetch men data
                eligible_men_ids = df[
                    (df['gender'] == 'Male') &
                    (df['age'] >= FERTILITY_MIN_AGE_M) &
                    (df['age'] <= FERTILITY_MAX_AGE_M) &
                    live_mask
                ]['id'].values
                
                if len(eligible_men_ids) == 0: return

                # Optimization: Pre-fetch men data for O(1) lookup
                # This prevents O(N) scan inside the loop
                men_data = df.loc[df['id'].isin(eligible_men_ids)].copy().set_index('id')
                
            # Optimization: Pre-calculate partner map for O(1) lookup
            # Map woman_id -> partner_id (Spouse/Lover only)
            # This avoids filtering dataframe inside the loop
            rel_df = state.relationships
            if not rel_df.empty:
                 # Filter relevant types
                 active_rels = rel_df[rel_df['type'].isin(['Spouse', 'Lover'])]
                 # Create dictionary for fast lookups
                 # Assuming one active partner for simplicity in lookup (take last)
                 partner_map = active_rels.set_index('id_a')['id_b'].to_dict()
            else:
                 partner_map = {}

            # Iterate interested women
            # We can still loop, but make the inner logic O(1) mostly
            valid_pregnancies = []
            final_partners = []
            new_relationships = [] # Batch new links
            
            # Policy Strictness
            strictness = state.globals.get('policy_mating_strictness', 0.5)

            for w_idx in women_indices:
                woman = df.loc[w_idx]
                w_id = woman['id']
                
                best_partner = None
                best_partner_id = None
                best_score = -1.0
                
                # 1. Existing Partner Check
                existing_partner_id = partner_map.get(w_id)
                
                if existing_partner_id:
                     # Check if partner is alive and reachable
                     if existing_partner_id in men_data.index:
                         # Loyalty Check (80%)
                         if random.random() < 0.8:
                             valid_pregnancies.append(w_idx)
                             final_partners.append(existing_partner_id)
                             continue # FAST PATH EXIT

                # 2. Dating / Finding New (Slow Path)
                # Only runs for singles or cheaters
                
                sample_size = min(3, len(eligible_men_ids))
                candidates_ids = np.random.choice(eligible_men_ids, size=sample_size, replace=False)
                
                for m_id in candidates_ids:
                    man = men_data.loc[m_id]
                    
                    # --- ATTRACTION ALGORITHM ---
                    w_vul = woman.get('genetic_vulnerability', 0.1)
                    m_vul = man.get('genetic_vulnerability', 0.1)
                    vul_score = 1.0 - ((w_vul + m_vul) / 2.0)
                    
                    # Validate max_hp to prevent division by zero
                    man_max_hp = man.get('max_hp', 100.0)
                    if man_max_hp <= 0:
                        man_max_hp = 100.0
                    
                    health_score = (man['hp'] / man_max_hp)
                    attr_stat = man.get('attractiveness', 0.5)
                    w_skin = woman.get('skin_tone', 0.5)
                    m_skin = man.get('skin_tone', 0.5)
                    skin_sim = 1.0 - abs(w_skin - m_skin)
                    
                    physical_score = (0.2 * vul_score) + (0.3 * health_score) + (0.4 * attr_stat) + (0.1 * skin_sim)

                    job_rank = {'Chief': 1.0, 'Healer': 0.8, 'Builder': 0.6, 'Hunter': 0.6, 'Gatherer': 0.4}
                    status_score = job_rank.get(man['job'], 0.4)
                    
                    age_diff = abs(woman['age'] - man['age'])
                    if age_diff > 15: status_score *= 0.7 
                    
                    chemistry = random.random()
                    total_score = (0.4 * physical_score) + (0.3 * status_score) + (0.3 * chemistry)
                    
                    if total_score > best_score:
                        best_score = total_score
                        best_partner = man
                        best_partner_id = m_id
                
                if best_partner is not None:
                    threshold = 0.6 - (woman.get('libido', 0.5) * 0.2) 
                    
                    approved = False
                    if best_score > threshold:
                        approved = True
                        
                        # Incest Check
                        w_mom = woman['mother_id']
                        w_dad = woman['father_id']
                        p_mom = best_partner['mother_id']
                        p_dad = best_partner['father_id']
                        
                        if (w_mom is not None and w_mom == p_mom) or \
                           (w_dad is not None and w_dad == p_dad):
                            approved = False
                        
                        if w_mom == best_partner_id or w_dad == best_partner_id or \
                           p_mom == w_id or p_dad == w_id:
                            approved = False

                        # Policy Check
                        if approved:
                            policy_reject = False
                            if strictness > 0.8 and best_partner.get('genetic_vulnerability', 0) > 0.4:
                                 policy_reject = True
                            
                            if policy_reject:
                                avg_libido = (woman.get('libido', 0.5) + best_partner.get('libido', 0.5)) / 2
                                if best_score > 0.8 and avg_libido > strictness:
                                    pass # Elopement
                                else:
                                    approved = False

                    if approved:
                        valid_pregnancies.append(w_idx)
                        final_partners.append(best_partner_id)
                        
                        # Batch new relationship creation
                        # Check exist via partner_map is not enough because map is old state
                        # But for speed we assume new link if not in map
                        if partner_map.get(w_id) != best_partner_id:
                             new_relationships.append((w_id, best_partner_id))

            # Apply Logic
            if valid_pregnancies:
                df.loc[valid_pregnancies, 'is_pregnant'] = True
                df.loc[valid_pregnancies, 'pregnancy_days'] = 0
                if 'pregnancy_father_id' not in df.columns: df['pregnancy_father_id'] = None
                df.loc[valid_pregnancies, 'pregnancy_father_id'] = final_partners
            
            # Batch Update Relationships
            if new_relationships:
                init_affection = 0.8
                rows = []
                for p1, p2 in new_relationships:
                    # Double directional
                    rows.append({'id_a': p1, 'id_b': p2, 'type': 'Lover', 'commitment': 0.1, 'affection': init_affection, 'start_day': state.day})
                    rows.append({'id_a': p2, 'id_b': p1, 'type': 'Lover', 'commitment': 0.1, 'affection': init_affection, 'start_day': state.day})
                
                if rows:
                    state.relationships = pd.concat([state.relationships, pd.DataFrame(rows)], ignore_index=True)

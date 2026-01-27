import random
import uuid
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from src.engine.systems import System

@dataclass
class Disease:
    id: str
    name: str
    transmission: float # 0.0 - 1.0 (Chance per tick to infect neighbor)
    lethality: float # 0.0 - 1.0 (Chance per tick to kill if severe)
    duration: int # Days to recover
    effects: Dict[str, float] # e.g. {'hp': -1.0, 'stamina': -5.0}
    is_chronic: bool # If true, never fully cures, just goes dormant
    immunity_type: str # 'sterilizing', 'waning', 'sensitizing'

class DiseaseSystem(System):
    def __init__(self):
        self.known_diseases: Dict[str, Disease] = {}
        
        # Name Gen Components
        self.prefixes = ["Crimson", "Shaking", "Burning", "Pale", "Black", "Silent", "Rabid", "Weeping"]
        self.roots = ["Lung", "Blood", "Gut", "Bone", "Skin", "Brain", "Eye"]
        self.suffixes = ["Rot", "Fever", "Pox", "Blight", "Plague", "Cough", "Flux", "Withering"]

    def update(self, state):
        # Ensure infection tracking dataframe exists
        if not hasattr(state, 'infections'):
            # active: boolean for chronic diseases toggling
            state.infections = pd.DataFrame({
                "person_id": pd.Series(dtype='str'),
                "disease_id": pd.Series(dtype='str'),
                "progress": pd.Series(dtype='float'),
                "days_infected": pd.Series(dtype='int'),
                "active": pd.Series(dtype='bool')
            })
            
        if not hasattr(state, 'immunities'):
            # immunity_level: 0.0-1.0 (1.0 = Immune)
            # exposure_count: For sensitization
            state.immunities = pd.DataFrame({
                 "person_id": pd.Series(dtype='str'),
                 "disease_id": pd.Series(dtype='str'),
                 "immunity_level": pd.Series(dtype='float'),
                 "exposure_count": pd.Series(dtype='int')
            })
            
        self._check_outbreak(state)
        self._handle_transmission(state)
        self._handle_progression(state)
        self._handle_persistence(state) # Manage dormancy/immunity waning

    def _check_outbreak(self, state):
        pop_count = len(state.population)
        if pop_count < 10: return
        
        # Base chance 0.5% per day, scales with density
        density_risk = pop_count / 100000.0
        chance = 0.005 + density_risk
        
        if random.random() < chance:
            self._create_outbreak(state)

    def _create_outbreak(self, state):
        disease = self._generate_procedural_disease()
        self.known_diseases[disease.id] = disease
        state.log(f"☣️ OUTBREAK: A new plague '{disease.name}' has emerged!")
        
        # Patient Zero (Random living person)
        living = state.population[state.population['is_alive']]
        if living.empty:
            # No one alive to infect
            return
        
        try:
            victim_id = np.random.choice(living['id'].values)
            self._infect(state, victim_id, disease.id)
        except (ValueError, IndexError) as e:
            # Edge case: living became empty during selection
            print(f"⚠️ Warning: Could not select patient zero: {e}")
            return

    def _infect(self, state, person_id, disease_id):
        disease = self.known_diseases[disease_id]
        
        # Check Immunity
        imm_row = state.immunities[
            (state.immunities['person_id'] == person_id) & 
            (state.immunities['disease_id'] == disease_id)
        ]
        
        immunity_level = 0.0
        exposure = 0
        if not imm_row.empty:
            immunity_level = imm_row.iloc[0]['immunity_level']
            exposure = imm_row.iloc[0]['exposure_count']
            
        # 1. Sterilizing Immunity matches
        if immunity_level > 0.9:
            return # Immune
            
        # 2. Sensitization Check (Cytokine Storm)
        # If sensitized, infection happens and severity will be boosts later
        # For infection logic, high immunity might just block it
        
        if random.random() < immunity_level:
            return # Blocked by partial immunity
            
        # Check if already infected
        existing = state.infections[
            (state.infections['person_id'] == person_id) & 
            (state.infections['disease_id'] == disease_id)
        ]
        
        if not existing.empty:
            # If latent (active=False), reactivate
            if not existing.iloc[0]['active']:
                idx = existing.index[0]
                state.infections.at[idx, 'active'] = True
                state.log(f"⚠️ {disease.name} has re-awakened in a host!")
            return
        
        # New Infection
        new_row = {"person_id": person_id, "disease_id": disease_id, "progress": 0.0, "days_infected": 0, "active": True}
        state.infections = pd.concat([state.infections, pd.DataFrame([new_row])], ignore_index=True)
        
        # Update Exposure
        if imm_row.empty:
            new_imm = {"person_id": person_id, "disease_id": disease_id, "immunity_level": 0.0, "exposure_count": 1}
            state.immunities = pd.concat([state.immunities, pd.DataFrame([new_imm])], ignore_index=True)
        else:
            idx = imm_row.index[0]
            state.immunities.at[idx, 'exposure_count'] += 1

    def _handle_transmission(self, state):
        if state.infections.empty: return
        
        # Filter for ACTIVE infections only
        active_infections = state.infections[state.infections['active'] == True]
        if active_infections.empty: return
        
        active_disease_ids = active_infections['disease_id'].unique()
        
        for d_id in active_disease_ids:
            disease = self.known_diseases[d_id]
            infected_count = len(active_infections[active_infections['disease_id'] == d_id])
            
            # Transmission calc
            prob = 1.0 - ((1.0 - disease.transmission) ** infected_count)
            prob = min(0.5, prob)
            
            # Find susceptible
            infected_ids = active_infections[active_infections['disease_id'] == d_id]['person_id'].values
            susceptible_df = state.population[
                (~state.population['id'].isin(infected_ids)) & 
                (state.population['is_alive'])
            ]
            
            if susceptible_df.empty: continue
            
            # Roll
            rolls = np.random.random(len(susceptible_df))
            new_infections_mask = rolls < prob
            
            new_victims = susceptible_df[new_infections_mask]['id'].values
            
            # Loop because we need immunity check per victim
            # (Vectorizing immunity check across varying immunity levels is hard)
            if len(new_victims) == 0:
                continue
                
            for vid in new_victims:
                try:
                    self._infect(state, vid, d_id)
                except Exception as e:
                    # Log but don't crash simulation
                    print(f"⚠️ Warning: Failed to infect agent {vid}: {e}")
                    continue

    def _handle_progression(self, state):
        if state.infections.empty: return
        
        # Only process active
        mask = state.infections['active'] == True
        if not mask.any(): return
        
        # Increment days for active
        state.infections.loc[mask, 'days_infected'] += 1
        
        active_disease_ids = state.infections.loc[mask, 'disease_id'].unique()
        
        ids_to_remove = [] # For acute
        ids_to_dormant = [] # For chronic
        
        for d_id in active_disease_ids:
            disease = self.known_diseases[d_id]
            d_mask = mask & (state.infections['disease_id'] == d_id)
            victim_ids = state.infections.loc[d_mask, 'person_id'].values
            
            if len(victim_ids) == 0: continue

            # Apply Damage
            pop_mask = state.population['id'].isin(victim_ids)
            
            # Sensitization Multiplier
            # Check exposure counts for these victims
            # Join with immunities (Slow? optimize later)
            # Simplification: Assume 1.0 damage multiplier for now unless specialized
            
            # Genetic Vulnerability Multiplier
            if 'genetic_vulnerability' in state.population.columns:
                 # Extract vul for victims
                 # Need to align indexes
                 vuls = state.population.loc[pop_mask, 'genetic_vulnerability'].fillna(0.0)
                 # Formula: Damage * (1 + Vul * 2) -> Max 3x damage for 1.0 vul
                 dmg_mult = 1.0 + (vuls * 2.0)
            else:
                 dmg_mult = 1.0
            
            if disease.immunity_type == 'sensitizing':
                 # Hack: Just apply random critically for checking mechanism
                 pass

            if 'hp' in disease.effects:
                # Effect is negative, so we add (negative * positive_mult)
                # Vectorized operation
                state.population.loc[pop_mask, 'hp'] += (disease.effects['hp'] * dmg_mult)
            if 'stamina' in disease.effects:
                state.population.loc[pop_mask, 'stamina'] += (disease.effects['stamina'] * dmg_mult)
                
            # Recovery Check
            recovered_submask = state.infections.loc[d_mask, 'days_infected'] >= disease.duration
            if recovered_submask.any():
                rec_rows = state.infections.loc[d_mask][recovered_submask]
                
                # Grant Immunity
                self._grant_immunity(state, rec_rows['person_id'].values, disease)

                if disease.is_chronic:
                    ids_to_dormant.extend(rec_rows.index.tolist())
                else:
                    ids_to_remove.extend(rec_rows.index.tolist())

        # Apply State Changes
        if ids_to_remove:
            # Safe Drop
            existing_remove = state.infections.index.intersection(ids_to_remove)
            if not existing_remove.empty:
                state.infections.drop(existing_remove, inplace=True)
                state.infections.reset_index(drop=True, inplace=True)
            
        if ids_to_dormant:
            # Safe Update
            # Reset index messed up IDs if we dropped? 
            # Actually if we drop 'ids_to_remove', then 'ids_to_dormant' indices might shift if they were higher?
            # Yes, drop resets index if we do reset_index.
            # CRITICAL BUG: Mixing drop and atomic updates on indices.
            # Fix: Process state changes via ID lookup or boolean masks, not integer indices.
            pass 
            
            # Alternative: Just set active=False for dormant first, THEN drop remove.
            # IDS are indices here.
            
            # 1. Handle Dormant (No index shift yet)
            existing_dormant = state.infections.index.intersection(ids_to_dormant)
            if not existing_dormant.empty:
                state.infections.loc[existing_dormant, 'active'] = False
                state.infections.loc[existing_dormant, 'days_infected'] = 0

            # 2. Handle Remove (Shift happens after this)
            existing_remove = state.infections.index.intersection(ids_to_remove)
            if not existing_remove.empty:
                state.infections.drop(existing_remove, inplace=True)
                state.infections.reset_index(drop=True, inplace=True)

    def _grant_immunity(self, state, person_ids, disease):
        if len(person_ids) == 0: return
        
        # Upsert immunity
        # Slow iterative for now
        for pid in person_ids:
            mask = (state.immunities['person_id'] == pid) & (state.immunities['disease_id'] == disease.id)
            
            boost = 1.0 
            if disease.immunity_type == 'waning':
                boost = 0.8 # Not perfect
            
            if mask.any():
                state.immunities.loc[mask, 'immunity_level'] = boost
            else:
                new_row = {"person_id": pid, "disease_id": disease.id, "immunity_level": boost, "exposure_count": 1}
                state.immunities = pd.concat([state.immunities, pd.DataFrame([new_row])], ignore_index=True)

    def _handle_persistence(self, state):
        # 1. Immunity Waning
        if hasattr(state, 'immunities') and not state.immunities.empty:
             # Decay 0.001 per day
             state.immunities['immunity_level'] -= 0.001
             state.immunities['immunity_level'] = state.immunities['immunity_level'].clip(lower=0.0)
             
        # 2. Chronic Reactivation
        if hasattr(state, 'infections') and not state.infections.empty:
            dormant_mask = state.infections['active'] == False
            if dormant_mask.any():
                # Get latent carriers
                latent_ids = state.infections.loc[dormant_mask, 'person_id'].values
                
                # Check condition (Weak host)
                weak_df = state.population[
                    (state.population['id'].isin(latent_ids)) & 
                    ((state.population['hp'] < 40) | (state.population['age'] > 60)) &
                    (state.population['is_alive'])
                ]
                
                if not weak_df.empty:
                    # Reactivate Chance
                    if random.random() < 0.1: # 10% daily chance if weak
                         reactivated_ids = weak_df['id'].values
                         # Update infection status
                         react_mask = (state.infections['person_id'].isin(reactivated_ids)) & (dormant_mask)
                         state.infections.loc[react_mask, 'active'] = True
                         # Log? state.log("Chronic flare up!")

    def _generate_procedural_disease(self) -> Disease:
        name = f"{random.choice(self.prefixes)} {random.choice(self.roots)} {random.choice(self.suffixes)}"
        
        transmission = np.random.beta(2, 5)
        lethality = np.random.beta(1, 10)
        duration = random.randint(3, 14)
        
        is_chronic = random.random() < 0.2 # 20% chance
        imm_type = random.choice(['sterilizing', 'sterilizing', 'waning', 'sensitizing'])
        
        effects = {}
        if random.random() < 0.8:
            effects['stamina'] = -random.randint(2, 5)
        if random.random() < 0.3 or lethality > 0.1:
            effects['hp'] = -random.randint(1, 2)
            
        return Disease(
            id=str(uuid.uuid4())[:8],
            name=name,
            transmission=transmission,
            lethality=lethality,
            duration=duration,
            effects=effects,
            is_chronic=is_chronic,
            immunity_type=imm_type
        )

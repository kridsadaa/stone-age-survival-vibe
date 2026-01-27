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
            state.infections = pd.DataFrame(columns=["person_id", "disease_id", "progress", "days_infected"])
            
        self._check_outbreak(state)
        self._handle_transmission(state)
        self._handle_progression(state)

    def _check_outbreak(self, state):
        pop_count = len(state.population)
        if pop_count < 10: return
        
        # Base chance 0.5% per day, scales with density
        density_risk = pop_count / 1000.0
        chance = 0.005 + density_risk
        
        if random.random() < chance:
            self._create_outbreak(state)

    def _create_outbreak(self, state):
        disease = self._generate_procedural_disease()
        self.known_diseases[disease.id] = disease
        state.log(f"☣️ OUTBREAK: A new plague '{disease.name}' has emerged!")
        
        # Patient Zero (Random living person)
        living = state.population[state.population['is_alive']]
        if not living.empty:
            victim_id = np.random.choice(living['id'].values) # Use ID instead of index
            self._infect(state, victim_id, disease.id)

    def _infect(self, state, person_id, disease_id):
        # Check if already infected
        existing = state.infections[
            (state.infections['person_id'] == person_id) & 
            (state.infections['disease_id'] == disease_id)
        ]
        if not existing.empty: return
        
        # Add record
        new_row = {"person_id": person_id, "disease_id": disease_id, "progress": 0.0, "days_infected": 0}
        state.infections = pd.concat([state.infections, pd.DataFrame([new_row])], ignore_index=True)

    def _handle_transmission(self, state):
        if state.infections.empty: return
        
        # For every infected person, chance to spread
        # Simplified Model: Random Spread
        # In a spatial map, we would check neighbors. here we assume random mixing.
        
        # Get active disease IDs
        active_disease_ids = state.infections['disease_id'].unique()
        
        for d_id in active_disease_ids:
            disease = self.known_diseases[d_id]
            infected_count = len(state.infections[state.infections['disease_id'] == d_id])
            
            # Transmission logic:
            # New Infections = Current * R0 (Transmission Rate)
            # But specific to uninfected people
            
            # Simple approach: Each infected person tries to infect X random people
            contacts = 2 # Daily contacts
            
            # Vectorized spread is hard without spatial matrix.
            # Let's do a probabilistic bulk spread:
            # Prob of getting infected = 1 - (1 - transmission)^infected_count
            # Valid for small populations
            
            prob = 1.0 - ((1.0 - disease.transmission) ** infected_count)
            # Cap at some reasonable limit to prevent instant wipe
            prob = min(0.5, prob)
            
            # Roll for all susceptible population
            # Filter those NOT already infected with THIS disease
            infected_ids = state.infections[state.infections['disease_id'] == d_id]['person_id'].values
            susceptible_df = state.population[
                (~state.population['id'].isin(infected_ids)) & 
                (state.population['is_alive'])
            ]
            
            if susceptible_df.empty: continue
            
            # Roll
            rolls = np.random.random(len(susceptible_df))
            new_infections_mask = rolls < prob
            
            new_victims = susceptible_df[new_infections_mask]['id'].values
            
            # Bulk add
            if len(new_victims) > 0:
                new_rows = pd.DataFrame({
                    "person_id": new_victims,
                    "disease_id": [d_id] * len(new_victims),
                    "progress": 0.0,
                    "days_infected": 0
                })
                state.infections = pd.concat([state.infections, new_rows], ignore_index=True)

    def _handle_progression(self, state):
        if state.infections.empty: return
        
        # Increment days
        state.infections['days_infected'] += 1
        
        # Apply Effects & Recovery
        # Group by disease for batch processing
        active_disease_ids = state.infections['disease_id'].unique()
        
        ids_to_remove = []
        
        for d_id in active_disease_ids:
            disease = self.known_diseases[d_id]
            
            # Get victims
            mask = state.infections['disease_id'] == d_id
            victim_ids = state.infections.loc[mask, 'person_id'].values
            
            # Apply Damage to Population DataFrame
            # Map ID to Index
            pop_mask = state.population['id'].isin(victim_ids)
            
            if 'hp' in disease.effects:
                state.population.loc[pop_mask, 'hp'] += disease.effects['hp'] # Effect is negative
            if 'stamina' in disease.effects:
                state.population.loc[pop_mask, 'stamina'] += disease.effects['stamina']
                
            # Recovery Check
            # Simple: Recover after Duration
            recovered_mask = state.infections.loc[mask, 'days_infected'] >= disease.duration
            if recovered_mask.any():
                # Indices in infections DF
                rec_idx = state.infections.loc[mask][recovered_mask].index
                ids_to_remove.extend(rec_idx.tolist())
                
        # Bulk remove recovered
        if ids_to_remove:
            state.infections.drop(ids_to_remove, inplace=True)
            state.infections.reset_index(drop=True, inplace=True)

    def _generate_procedural_disease(self) -> Disease:
        name = f"{random.choice(self.prefixes)} {random.choice(self.roots)} {random.choice(self.suffixes)}"
        
        # Randomized Stats
        transmission = np.random.beta(2, 5) # Skewed low (0.1 - 0.4 avg)
        lethality = np.random.beta(1, 10) # Skewed very low (0.0 - 0.2)
        duration = random.randint(3, 14)
        
        effects = {}
        if random.random() < 0.8:
            effects['stamina'] = -random.randint(5, 20)
        if random.random() < 0.3 or lethality > 0.1:
            effects['hp'] = -random.randint(1, 5)
            
        return Disease(
            id=str(uuid.uuid4())[:8],
            name=name,
            transmission=transmission,
            lethality=lethality,
            duration=duration,
            effects=effects
        )

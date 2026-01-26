import pandas as pd
import random
from typing import Dict, List, Optional
import uuid

class Human:
    def __init__(self, 
                 gender: str = None, 
                 age: int = None, 
                 parents: List['Human'] = None,
                 traits_pool: pd.DataFrame = None):
        
        self.id = f"HMN-{random.randint(2026, 3000)}-{str(uuid.uuid4())[:8]}"
        self.gender = gender if gender else random.choice(['Male', 'Female'])
        self.age = age if age is not None else random.randint(0, 50)
        
        # Physicals
        self.height = random.randint(150, 200) if self.gender == 'Male' else random.randint(140, 180)
        self.weight = random.randint(60, 100) if self.gender == 'Male' else random.randint(45, 80)
        self.max_hp = 100
        self.current_hp = 100
        self.stamina = 100
        
        # Psychology (Simple MBTI-like)
        self.personality = {
            "Aggression": random.random(),
            "Cooperation": random.random(),
            "Curiosity": random.random()
        }
        
        # Genetics & Traits
        self.traits = []
        self.genetic_vulnerability = random.random() # 0.0 to 1.0 (higher is worse)
        
        if traits_pool is not None and not traits_pool.empty:
            self._inherit_or_generate_traits(traits_pool)
            
        # Status
        self.is_alive = True
        self.infected_diseases = [] # List of disease IDs
        self.cause_of_death = None

    def _inherit_or_generate_traits(self, traits_df):
        # Simplification: Randomly assign traits based on probability
        # In a real inheritance system, we'd look at parents.
        for _, row in traits_df.iterrows():
            if random.random() < row['genetic_probability']:
                self.traits.append({
                    "name": row['trait_name'],
                    "bonus": row['survival_bonus']
                })
                self._apply_trait_bonus(row['survival_bonus'])

    def _apply_trait_bonus(self, bonus: Dict):
        if "hp" in bonus:
            self.max_hp += bonus["hp"]
            self.current_hp += bonus["hp"]
        # Add other logic here

    def update(self, food_available: bool, disease_data: List[Dict]):
        if not self.is_alive:
            return

        # Aging
        # We can say 1 tick = 1 day. 365 ticks = 1 year.
        # For simulation speed, maybe 1 tick = 1 month? Let's stick to 1 tick = 1 day for now.
        
        # Metabolic Cost
        cost = 5
        if not food_available:
            cost *= 2 
            self.current_hp -= 5 # Starvation damage
        
        self.stamina = max(0, self.stamina - cost)
        
        # Recovery if fed
        if food_available and self.current_hp < self.max_hp:
            self.current_hp += 1
            self.stamina = min(100, self.stamina + 10)

        # Disease Progression
        for d_id in self.infected_diseases:
            disease = next((d for d in disease_data if d['id'] == d_id), None)
            if disease:
                # Apply symptoms
                impact = disease.get('symptoms_impact', {})
                if 'hp' in impact:
                    self.current_hp += impact['hp'] # Usually negative
                if 'stamina' in impact:
                    self.stamina += impact['stamina']

        # Death Check
        if self.current_hp <= 0:
            self.die("Health Depletion / Starvation / Disease")
        elif self.age > 80 and random.random() < 0.01: # Old age chance
             self.die("Old Age")

    def die(self, cause):
        self.is_alive = False
        self.cause_of_death = cause

    def infect(self, disease_id):
        if disease_id not in self.infected_diseases:
            self.infected_diseases.append(disease_id)
            

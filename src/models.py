import pandas as pd
import random
from typing import Dict, List, Optional
import uuid

class Human:
    def __init__(self, 
                 gender: str = None, 
                 age: int = 0, # Default to baby if not specified
                 parents: List['Human'] = None,
                 traits_pool: pd.DataFrame = None,
                 family_id: str = None):
        
        self.id = f"HMN-{random.randint(2026, 3000)}-{str(uuid.uuid4())[:8]}"
        self.gender = gender if gender else random.choice(['Male', 'Female'])
        self.age = age
        
        # Lineage
        self.parents = parents if parents else []
        if family_id:
            self.family_id = family_id
        elif parents and parents[0].family_id:
            self.family_id = parents[0].family_id # Inherit from first parent (Father usually)
        else:
            self.family_id = str(uuid.uuid4())[:8] # New Lineage
            
        # Reproduction State
        self.is_pregnant = False
        self.pregnancy_days = 0
        self.partner_id = None # Father of the unborn child
        
        # Physicals
        if parents:
            # Genetics from parents
            self.height = (parents[0].height + parents[1].height) // 2 + random.randint(-5, 5)
            self.weight = (parents[0].weight + parents[1].weight) // 2 + random.randint(-5, 5)
        else:
            # Random generation
            self.height = random.randint(150, 200) if self.gender == 'Male' else random.randint(140, 180)
            self.weight = random.randint(60, 100) if self.gender == 'Male' else random.randint(45, 80)
            
        self.max_hp = 100
        self.current_hp = 100
        self.stamina = 100
        
        # Psychology (Simple MBTI-like)
        if parents:
            self.personality = {
                "Aggression": (parents[0].personality["Aggression"] + parents[1].personality["Aggression"]) / 2 + random.uniform(-0.1, 0.1),
                "Cooperation": (parents[0].personality["Cooperation"] + parents[1].personality["Cooperation"]) / 2 + random.uniform(-0.1, 0.1),
                "Curiosity": (parents[0].personality["Curiosity"] + parents[1].personality["Curiosity"]) / 2 + random.uniform(-0.1, 0.1)
            }
        else:
            self.personality = {
                "Aggression": random.random(),
                "Cooperation": random.random(),
                "Curiosity": random.random()
            }
        
        # Genetics & Traits
        self.traits = []
        # Vulnerability inheritance
        if parents:
            self.genetic_vulnerability = (parents[0].genetic_vulnerability + parents[1].genetic_vulnerability) / 2 + random.uniform(-0.05, 0.05)
        else:
            self.genetic_vulnerability = random.random()
            
        self.genetic_vulnerability = max(0.0, min(1.0, self.genetic_vulnerability))
        
        if traits_pool is not None and not traits_pool.empty:
            if parents:
                self._inherit_traits(parents, traits_pool)
            else:
                self._generate_random_traits(traits_pool)
            
        # Status
        self.is_alive = True
        self.infected_diseases = [] # List of disease IDs
        self.cause_of_death = None

    def _generate_random_traits(self, traits_df):
        for _, row in traits_df.iterrows():
            if random.random() < row['genetic_probability']:
                self._add_trait(row)

    def _inherit_traits(self, parents, traits_df):
        # 50% chance to inherit trait from each parent
        parent_traits = set()
        for p in parents:
            for t in p.traits:
                parent_traits.add(t['name'])
        
        for t_name in parent_traits:
            if random.random() < 0.5:
                # Find trait info
                row = traits_df[traits_df['trait_name'] == t_name].iloc[0]
                self._add_trait(row)
        
        # Small chance of random mutation (new trait)
        if random.random() < 0.05:
            random_trait = traits_df.sample(1).iloc[0]
            if random_trait['trait_name'] not in [t['name'] for t in self.traits]:
                self._add_trait(random_trait)

    def _add_trait(self, row):
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
        # We can say 1 tick = 1 month (approx) for faster repro? 
        # Or just keep it as "days" but have pregnancy lasts 9 days for simulation speed.
        # Let's say 1 tick = 1 unit of time.
        # If we want babies to grow up, we need faster aging or long simulation.
        # Let's keep age as generic time units.
        self.age += 1 # Age in 'ticks' now? Or keep as years?
        # User requested realistic aging regarding "0 years old" issue.
        # Let's assume input Age was years. We should track age_days.
        
        # Metabolic Cost
        cost = 5
        if self.is_pregnant:
            cost += 5 # Eating for two
            
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
                impact = disease.get('symptoms_impact', {})
                if 'hp' in impact:
                    self.current_hp += impact['hp']
                if 'stamina' in impact:
                    self.stamina += impact['stamina']

        # Death Check
        if self.current_hp <= 0:
            self.die("Health Depletion / Starvation / Disease")
        elif self.age > (80 * 365) and random.random() < 0.01: # Assuming age is days now? Let's fix age units in Simulation
             self.die("Old Age")

    def die(self, cause):
        self.is_alive = False
        self.cause_of_death = cause

    def infect(self, disease_id):
        if disease_id not in self.infected_diseases:
            self.infected_diseases.append(disease_id)
            
    def get_pregnant(self, partner_id):
        if self.gender == 'Female' and not self.is_pregnant:
            self.is_pregnant = True
            self.pregnancy_days = 0
            self.partner_id = partner_id
            return True
        return False
        
    def advance_pregnancy(self) -> Optional['Human']:
        if not self.is_pregnant:
            return None
            
        self.pregnancy_days += 1
        # 9 Days pregnancy for simulation speed (instead of 9 months)
        if self.pregnancy_days >= 9:
            self.is_pregnant = False
            return True # Signal that baby is born (Simulation class handles creation to pass parents)
        return False
            

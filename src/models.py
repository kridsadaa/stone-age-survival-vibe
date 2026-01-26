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
        
        # Psychology (Big Five - OCEAN)
        # Scale 0.0 to 1.0
        if parents:
            self.personality = {
                "Openness": (parents[0].personality["Openness"] + parents[1].personality["Openness"]) / 2 + random.uniform(-0.1, 0.1),
                "Conscientiousness": (parents[0].personality["Conscientiousness"] + parents[1].personality["Conscientiousness"]) / 2 + random.uniform(-0.1, 0.1),
                "Extraversion": (parents[0].personality["Extraversion"] + parents[1].personality["Extraversion"]) / 2 + random.uniform(-0.1, 0.1),
                "Agreeableness": (parents[0].personality["Agreeableness"] + parents[1].personality["Agreeableness"]) / 2 + random.uniform(-0.1, 0.1),
                "Neuroticism": (parents[0].personality["Neuroticism"] + parents[1].personality["Neuroticism"]) / 2 + random.uniform(-0.1, 0.1)
            }
            # Clamp values
            for k in self.personality:
                self.personality[k] = max(0.0, min(1.0, self.personality[k]))
        else:
            self.personality = {
                "Openness": random.random(),
                "Conscientiousness": random.random(),
                "Extraversion": random.random(),
                "Agreeableness": random.random(),
                "Neuroticism": random.random()
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
        self.infected_diseases = {} # Dict {disease_id: recovery_progress}
        self.immunities = [] # List of disease IDs
        self.cause_of_death = None
        
        # Profession
        self.job = "Gatherer"
    
    def set_job(self, job_name: str):
        self.job = job_name

    def get_gathering_efficiency(self, season: str = "Spring") -> float:
        # Base efficiency
        eff = 1.0
        
        # Conscientiousness: Hard work (0.0 to 1.0 -> +0% to +20%)
        eff += (self.personality["Conscientiousness"] * 0.2)
        
        # Openness: Adaptability in extreme seasons
        if season in ["Winter", "Summer"]:
            # High Openness helps find novel food sources
            eff += (self.personality["Openness"] * 0.15)
            
        return eff

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

    def update(self, food_available: bool, disease_data: List[Dict], healer_bonus: float = 0.0, metabolic_cost_modifier: int = 0):
        if not self.is_alive:
            return

        # Aging: 1 Tick = 1 Day
        self.age += (1/365.0) 
        
        # Metabolic Cost
        # Base = 5
        base_cost = 5 + metabolic_cost_modifier
        
        # Extraversion: Higher energy burn (Socializing)
        # 0.0 -> 0, 1.0 -> +1.5
        base_cost += (self.personality["Extraversion"] * 1.5)
        
        cost = base_cost
        damage_sources = [] # Track what hurts us this turn
        
        if self.is_pregnant:
            cost += 5 # Eating for two
            
            # Dynamic Risk Calculation
            # We use the inverse of fertility as "Risk Factor"
            # Low Fertility (Old/Sick/Starving) = High Risk
            fertility = self.calculate_fertility_score()
            risk_factor = 1.0 - fertility 
            
            if risk_factor > 0.5: # Consider "High Risk"
                # Extra Metabolic Tax
                cost += (risk_factor * 20) 
                
                # Daily Risk Check (Scaled down from annual)
                risk_roll = random.random()
                
                # Probabilities (Daily)
                # target roughly 10% annual mortality -> 0.1 / 270 days ~= 0.0004
                # target roughly 80% annual miscarriage -> 0.8 / 270 days ~= 0.003
                
                death_prob = risk_factor * 0.0005 
                miscarriage_prob = risk_factor * 0.005
                
                if risk_roll < death_prob: 
                    self.die("Childbirth Complications")
                    return # Dead
                elif risk_roll < (death_prob + miscarriage_prob):
                    self.is_pregnant = False
                    damage = 20 * risk_factor
                    self.current_hp -= damage
                    damage_sources.append(f"Miscarriage Trauma (-{int(damage)})")
                    # Logically, if simulation supported events, we'd log miscarriage here
                    
        if not food_available:
            cost *= 2 
            self.current_hp -= 5 # Starvation damage
            damage_sources.append("Starvation")
        
        self.stamina = max(0, self.stamina - cost)
        
        # Recovery if fed
        if food_available:
            self.stamina = min(100, self.stamina + 10)
            if self.current_hp < self.max_hp:
                self.current_hp += 1

        # Disease Progression
        # Iterate over keys copy to allow modification
        for d_id in list(self.infected_diseases.keys()): 
            disease = next((d for d in disease_data if d['id'] == d_id), None)
            if disease:
                # Age Group
                age_group = "adult"
                if self.age < 15: age_group = "child"
                elif self.age > 50: age_group = "elder"
                
                factors = disease.get('age_factors', {}).get(age_group, {'severity': 1.0})
                severity = factors.get('severity', 1.0)
                
                impact = disease.get('symptoms_impact', {})
                if 'hp' in impact:
                    dmg = impact['hp'] * severity
                    self.current_hp += dmg # Impact is negative
                    damage_sources.append(f"{disease['name']}")
                if 'stamina' in impact:
                    dmg_s = impact['stamina'] * severity
                    self.stamina += dmg_s
                
                # Recovery Progress System
                threshold = disease.get('recovery_threshold', 100)
                progress_gain = 10 # Base gain (10 days avg)
                
                # Modifiers
                if self.stamina > 80: progress_gain += 5
                elif self.stamina < 20: progress_gain -= 5
                
                if self.current_hp > 80: progress_gain += 5
                
                # Neuroticism: Stress hinders healing
                # High Neuroticism (1.0) -> -3 points
                progress_gain -= (self.personality["Neuroticism"] * 3)
                
                # Healer Bonus (Convert float bonus to points, approx +5 per healer)
                progress_gain += (healer_bonus * 100)
                
                # Random variation
                progress_gain += random.randint(-2, 5)
                
                self.infected_diseases[d_id] += progress_gain
                
                if self.infected_diseases[d_id] >= threshold:
                    # Recovered
                    del self.infected_diseases[d_id]
                    if disease.get('confers_immunity', False):
                        self.immunities.append(d_id)

        # Death Check
        if self.current_hp <= 0:
            if not damage_sources: damage_sources.append("Unknown Causes")
            self.die(f"Health Failure ({', '.join(damage_sources)})")
        elif self.age > 80: 
             # Daily death chance for elderly
             # Annual chance approx 10%
             # Daily chance approx 0.10 / 365 = 0.00027
             chance = (0.10 + ((self.age - 80) * 0.02)) / 365.0
             if random.random() < chance:
                 self.die("Old Age")

    def die(self, cause):
        self.is_alive = False
        self.cause_of_death = cause

    def infect(self, disease_id):
        if disease_id in self.immunities:
            return
            
        if disease_id not in self.infected_diseases:
            self.infected_diseases[disease_id] = 0.0
            
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
        # 9 Months (270 Days)
        if self.pregnancy_days >= 270:
            self.is_pregnant = False
            return True # Signal that baby is born (Simulation class handles creation to pass parents)
        return False
        
    def calculate_fertility_score(self) -> float:
        """
        Calculates a score between 0.0 and 1.0 represented ability to conceive.
        Factors: Age, Health (HP), Nutrition (Stamina), Genetics (Traits).
        """
        if self.gender != 'Female': return 0.0
        
        # 1. Age Factor (The Curve)
        age = self.age
        age_score = 0.0
        
        if age < 16:
            age_score = 0.0
        elif 16 <= age < 20:
            age_score = 0.6 + ((age - 16) * 0.075) # Ramp up to ~0.9
        elif 20 <= age <= 32:
            age_score = 1.0 # Peak
        elif 33 <= age <= 40:
            age_score = 1.0 - ((age - 32) * 0.05) # Gradual decline to 0.6
        elif 41 <= age <= 45:
            age_score = 0.6 - ((age - 40) * 0.08) # Steep decline to 0.2
        elif 46 <= age <= 50:
            age_score = 0.2 - ((age - 45) * 0.038) # Near zero (0.01)
        else:
            age_score = 0.001 # Miracle
            
        age_score = max(0.001, age_score) # Minimum viable
        
        # 2. Biological Status
        bio_multiplier = 1.0
        
        # Personality: Extraversion increases mating opportunities
        bio_multiplier += (self.personality["Extraversion"] * 0.3)
        
        # Health
        if self.current_hp < 20:
            bio_multiplier *= 0.0 # Too critical
        elif self.current_hp < 50:
            bio_multiplier *= 0.5
            
        # Nutrition
        if self.stamina < 20:
            return 0.0 # Body shuts down reproduction
        elif self.stamina < 50:
            bio_multiplier *= 0.5
            
        # 3. Genetics (Traits)
        trait_multiplier = 1.0
        trait_names = [t['name'] for t in self.traits]
        
        if "Fertile" in trait_names: trait_multiplier *= 1.2
        if "Robust" in trait_names: trait_multiplier *= 1.1
        if "Barren" in trait_names: trait_multiplier *= 0.5
        if "Frail" in trait_names: trait_multiplier *= 0.8
        
        final_score = age_score * bio_multiplier * trait_multiplier
        return max(0.0, min(1.0, final_score))

from typing import List, Dict
import random
from src.models import Human
from src.loaders import load_diseases, load_traits

class World:
    def __init__(self, 
                 diseases_path='data/diseases.json', 
                 traits_path='data/traits.csv', 
                 initial_pop=50):
        
        self.day = 0
        self.population: List[Human] = []
        self.chronicle: List[str] = []
        self.resources = 1000 # Example shared food store
        
        # Load Data
        self.diseases = load_diseases(diseases_path)
        self.traits_df = load_traits(traits_path)
        
        # Init Population
        for _ in range(initial_pop):
            h = Human(traits_pool=self.traits_df)
            self.population.append(h)
            
        self.log(f"world created with {initial_pop} agents.")

    def log(self, message: str):
        entry = f"Day {self.day}: {message}"
        self.chronicle.insert(0, entry) # Newest first

    def tick(self):
        self.day += 1
        
        # 1. Resource Gathering (Simplified)
        # Total foraging power
        gathered = 0
        living_pop = [p for p in self.population if p.is_alive]
        
        for p in living_pop:
            # Check for traits
            bonus = 0
            for t in p.traits:
                if 'foraging' in t['bonus']:
                    bonus += t['bonus']['foraging']
            
            gathered += (10 + bonus)
            
        self.resources += gathered
        
        # 2. Consumption & Bio Updates
        # Sort by age (weakest/oldest eat last? or first? User said: "If food is scarce, older or weaker agents die first.")
        # So we feed strong/young first.
        # Let's sort by HP desc for "strength"
        living_pop.sort(key=lambda x: x.current_hp, reverse=True)
        
        deaths_today = 0
        
        for p in living_pop:
            food_needed = 10
            fed = False
            if self.resources >= food_needed:
                self.resources -= food_needed
                fed = True
            
            p.update(food_available=fed, disease_data=self.diseases)
            
            if not p.is_alive and p.cause_of_death != "Already Dead": 
                # He might have died in update()
                deaths_today += 1
                self.log(f"{p.id} died of {p.cause_of_death}")

        # 3. Disease Outbreak & Spread
        self._handle_disease(living_pop)
        
        # 4. Reproduction (Optional for now, but good for sustained sim)
        # Simple random birth if pop < cap
        if len(living_pop) < 200 and random.random() < 0.2:
            new_baby = Human(age=0, traits_pool=self.traits_df)
            self.population.append(new_baby)
            self.log(f"A new baby was born! ID: {new_baby.id}")

    def _handle_disease(self, living_pop):
        # Spontaneous Outbreak (Patient Zero)
        # Higher density = higher chance
        density_risk = len(living_pop) / 100.0
        if random.random() < (0.05 * density_risk):
            # Select random disease
            if not self.diseases: return
            
            disease = random.choice(self.diseases)
            victim = random.choice(living_pop)
            victim.infect(disease['id'])
            self.log(f"OUTBREAK: {disease['name']} detected in {victim.id}")

        # Spread
        # For each infected person, they can infect others nearby (random sample)
        for p in living_pop:
            if not p.infected_diseases:
                continue
            
            for d_id in p.infected_diseases:
                d_info = next((d for d in self.diseases if d['id'] == d_id), None)
                if not d_info: continue
                
                # Check transmission
                # Try to infect k random neighbors
                contacts = random.sample(living_pop, min(len(living_pop), 5))
                for contact in contacts:
                    if contact.id == p.id: continue
                    
                    # Chance = Base Rate - Genetic Resistance + Vulnerability
                    chance = d_info['transmission_rate'] + (contact.genetic_vulnerability * 0.1)
                    # Check immune traits? (Not implemented deep yet)
                    
                    if random.random() < chance:
                        contact.infect(d_id)

from typing import List, Dict
import random
from src.models import Human
from src.loaders import load_diseases, load_traits
from src.ai import QAgent
from src.tech import TechTree
from src.map import WorldMap

class World:
    def __init__(self, 
                 diseases_path='data/diseases.json', 
                 traits_path='data/traits.csv', 
                 initial_pop=50,
                 existing_ai=None):
        
        self.day = 0
        self.era = "Stone Age" # Evolution State
        
        # AI Persistence
        if existing_ai:
            self.ai = existing_ai
        else:
            self.ai = QAgent()
            
        self.ai_action = 1 # Default Balanced
        self.population: List[Human] = []
        self.chronicle: List[str] = []
        self.resources = 1000 # Example shared food store
        
        # Tech & Resources
        self.inventory = {"Wood": 0, "Stone": 0}
        self.idea_points = 0.0
        self.tech_tree = TechTree()
        self.map = WorldMap()
        
        # Load Data
        self.diseases = load_diseases(diseases_path)
        self.traits_df = load_traits(traits_path)
        
        # Init Population
        self._generate_initial_population(initial_pop)
        
        # Initial Job Assignment (Ensure at least 1 Healer)
        if self.population:
            # Pick a random adult to be the shaman
            adults = [p for p in self.population if p.age >= 16]
            if adults:
                shaman = random.choice(adults)
                shaman.set_job("Healer")
            
        self.log(f"world created with {len(self.population)} agents (Target: {initial_pop}).")

    @property
    def current_season(self):
        day_of_year = self.day % 365
        if day_of_year < 90: return "Spring"
        elif day_of_year < 180: return "Summer"
        elif day_of_year < 270: return "Autumn"
        else: return "Winter"

    def _generate_initial_population(self, target_pop: int):
        while len(self.population) < target_pop:
            # 70% chance to spawn a family, 30% loner
            if random.random() < 0.7:
                # Family Unit
                family_id = f"FAM-{random.randint(1000, 9999)}"
                
                # Father
                father = Human(gender='Male', age=random.randint(18, 50), traits_pool=self.traits_df, family_id=family_id)
                self.population.append(father)
                
                # Mother
                mother = Human(gender='Female', age=random.randint(18, 50), traits_pool=self.traits_df, family_id=family_id)
                # Small chance they are parents of the kids
                mother.partner_id = father.id # Initial pair
                self.population.append(mother)
                
                # Children (0-3 kids)
                num_kids = random.randint(0, 3)
                for _ in range(num_kids):
                    # Age must be reasonable (Mother age - 16 >= Kid age)
                    max_kid_age = min(15, mother.age - 16)
                    if max_kid_age < 0: max_kid_age = 0
                    
                    kid_age = random.randint(0, max_kid_age)
                    kid = Human(age=kid_age, parents=[father, mother], traits_pool=self.traits_df, family_id=family_id)
                    self.population.append(kid)
            else:
                # Loner
                age = random.randint(16, 60)
                loner = Human(age=age, traits_pool=self.traits_df)
                self.population.append(loner)

    def log(self, message: str):
        entry = f"Day {self.day}: {message}"
        self.chronicle.insert(0, entry) # Newest first

    def tick(self):
        self.day += 1

        # 0. AI Decision & Job Assignment
        living_pop = [p for p in self.population if p.is_alive]
        total_pop = len(living_pop)
        infected_count = sum(1 for p in living_pop if p.infected_diseases)
        
        # A. Learn from previous day
        # Reward Logic:
        # Survival is key. Growth is good. Death is bad.
        # Simple Reward: +1 per pop (alive), -10 per death (calculated later), +0.1 per food surplus
        # For simplicity in this step, we'll calculate "Day Reward" at the END of the tick loop or estimate here.
        # Let's estimate strictly based on current state vs previous expectation?
        # Actually, let's learn at the START of the tick based on what happened since yesterday.
        # But we don't store "yesterday's pop" easily without adding fields.
        # Let's keep it simple: State -> Action. Reward comes from *Growth* and *Food Stability*.
        
        current_state = self.ai.get_state_key(self.current_season, self.resources, total_pop, infected_count)
        
        # Calculate Reward (Pop * 1 + Resources * 0.01) - Penalty in death logic
        reward = len(living_pop) 
        if self.resources < len(living_pop) * 10: reward -= 50 # Starvation penalty
        
        # Check Scout Deaths from LAST turn (Since we learn at start of tick for previous day)
        # We need to store 'last_turn_dead_scouts' in World class. 
        # For this prototype, let's just use 'scout_deaths' if it persists, but tick() vars are local.
        # Let's attach it to self
        if hasattr(self, 'last_turn_scout_deaths'):
             reward -= (self.last_turn_scout_deaths * 50) # Heavy penalty
             
        self.ai.learn(reward, current_state)
        
        # B. Choose Action
        action = self.ai.choose_action(current_state)
        self.ai_action = action
        # Actions: 0-2 (Jobs), 3-5 (Scouting)
        
        # Mapping Actions to Policies
        # Actions 0-2 control Job Ratio. 3-5 might implicitly mean "Balance Job" + "Scout Mode"
        # Since we use a single integer action, let's map them:
        # 0: Eco (Gather Focus) + No Scout
        # 1: Balance + No Scout
        # 2: Heal Focus + No Scout
        # 3: Balance + Patrol (Small Risk)
        # 4: Balance + Expedition (Large Safe)
        # 5: Stop Scouting (Safe Mode)
        # 6: Policy: Strict Mating
        # 7: Policy: Open Mating
        # 8: Policy: Communal Rationing
        # 9: Policy: Merit Rationing

        # Process Policy Actions (Stateful)
        if action == 6:
            if self.engine.state.globals.get('policy_mating') != "Strict":
                self.engine.state.globals['policy_mating'] = "Strict"
                self.log("📜 Chief enforces Strict Mating Policy (Reproduction Focus).")
        elif action == 7:
             if self.engine.state.globals.get('policy_mating') != "Open":
                self.engine.state.globals['policy_mating'] = "Open"
                self.log("📜 Chief enforces Open Mating Policy (Happiness Focus).")
        elif action == 8:
             if self.engine.state.globals.get('policy_rationing') != "Communal":
                self.engine.state.globals['policy_rationing'] = "Communal"
                self.log("📜 Chief enforces Communal Rationing.")
        elif action == 9:
             if self.engine.state.globals.get('policy_rationing') != "Meritocracy":
                self.engine.state.globals['policy_rationing'] = "Meritocracy"
                self.log("📜 Chief enforces Meritocracy Rationing (Work First).")

        
        # Actually, let's decouple? No, Q-Table assumes discrete actions.
        # Let's say:
        # 0: GatherFocus
        # 1: Balance
        # 2: HealFocus
        # 3: Scout Patrol (Balance Job)
        # 4: Scout Expedition (Balance Job)
        # 5: Extreme Safety (Heal Focus + No Scout)
        
        healer_ratio = 20 # Default
        if action == 0: healer_ratio = 50 # Few healers
        elif action == 2 or action == 5: healer_ratio = 10 # Many healers
        elif action >= 3: healer_ratio = 20 # Balance
        
        # Healer Ratio: 1 per X pop
        target_healers = max(1, total_pop // healer_ratio)
        current_healers = sum(1 for p in living_pop if p.job == "Healer")
        
        if current_healers < target_healers:
            # Promote random Gatherer
            candidates = [p for p in living_pop if p.job == "Gatherer" and p.age >= 16]
            if candidates:
                new_healer = random.choice(candidates)
                new_healer.set_job("Healer")
                self.log(f"AI: Promoted {new_healer.id} to Healer")
                current_healers += 1
        elif current_healers > target_healers:
             # Demote to Gatherer
             healers = [p for p in living_pop if p.job == "Healer"]
             if healers:
                 fired = random.choice(healers)
                 fired.set_job("Gatherer")
                 self.log(f"AI: {fired.id} assigned to Gathering")
        
        # 1. Resource Gathering
        gathered = 0
        
        # Seasonal Modifiers
        season = self.current_season
        food_modifier = 1.0
        metabolic_modifier = 0
        
        if season == "Summer":
            food_modifier = 1.2 # Abundance
        elif season == "Winter":
            food_modifier = 0.5 # Scarcity
            metabolic_modifier = 2 # Cold requires more energy
        
        # Global Healer Bonus calculation
        # Each healer adds +5% recovery chance
        global_healer_bonus = current_healers * 0.05
        
        for p in living_pop:
            # Check for traits
            bonus = 0
            for t in p.traits:
                if 'foraging' in t['bonus']:
                    bonus += t['bonus']['foraging']
            
            # Base Production by Job
            production = 10
            if p.job == "Healer":
                production = 5 # Healers gather less
            # elif p.job == "Farmer": production = 20 (Future)
            
            # Use Personality Efficiency (Conscientiousness/Openness)
            efficiency = p.get_gathering_efficiency(season)
            
            gathered += ((production + bonus) * food_modifier * efficiency)
            
        # Hunting Event (Sustainable Buff)
        # Occasional Big Game Hunt to prevent total starvation spiral
        if self.resources < len(living_pop) * 5: # If low on food
            if random.random() < 0.1: # 10% chance per day when hungry
                 hunt_yield = len(living_pop) * 5
                 gathered += hunt_yield
                 self.log(f"EVENT: The tribe successfully hunted a Mammoth! (+{hunt_yield} Food)")
            
        self.resources += gathered
        
        # --- Innovation & Tech Tick ---
        # 1. Generate Ideas (Based on Openness)
        daily_ideas = 0
        for p in living_pop:
            daily_ideas += (p.personality["Openness"] * 0.2) # Base 0.2 per person
        
        # Eureka Chance
        if random.random() < 0.001: # 0.1% chance
            bonus_ideas = 500
            daily_ideas += bonus_ideas
            self.log("EVENT: EUREKA! A sudden flash of inspiration hits the tribe!")
            
        self.idea_points += daily_ideas
        
        # 2. Check Unlocks
        new_techs = self.tech_tree.check_unlocks(self.idea_points)
        for t_name in new_techs:
            self.log(f"DISCOVERY: The tribe has mastered **{t_name}**!")
            
        # 3. Scouting & Exploration (AI Controlled)
        # Determine Scout Party Size based on AI Action
        # Actions: 0-2 (Eco), 3 (Patrol), 4 (Expedition), 5 (No Scout)
        scout_party_size = 0
        if self.ai_action == 3: 
            scout_party_size = random.randint(2, 4) # Small Patrol
        elif self.ai_action == 4:
            scout_party_size = random.randint(10, 15) # Major Expedition
        
        # Limit by population (can't send more than 20% of pop)
        scout_party_size = min(scout_party_size, int(len(living_pop) * 0.2))
        
        # Execute Exploration
        scout_deaths = 0
        if scout_party_size > 0:
            # Pick target
            dist = 2 if self.ai_action == 4 else 1
            cx = self.map.village_x + random.randint(-dist, dist)
            cy = self.map.village_y + random.randint(-dist, dist)
            
            # Explore
            new_tiles = self.map.explore(cx, cy, radius=1)
            
            # 1. Check tile danger for the target area (simplified: center tile)
            # Ensure bounds
            tx = max(0, min(self.map.width-1, cx))
            ty = max(0, min(self.map.height-1, cy))
            target_tile = self.map.grid[ty][tx]
            
            if target_tile.danger_level > 0:
                # Combat Logic
                # Risk = Danger / (Party Size * Tech)
                tech_multiplier = 1.0
                if self.tech_tree.techs["spears"].unlocked: tech_multiplier = 2.0
                
                risk_factor = target_tile.danger_level / (scout_party_size * 0.5 * tech_multiplier)
                risk_factor = min(0.8, risk_factor) # Cap risk
                
                # Roll for incident
                if random.random() < risk_factor:
                    # Casualty!
                    num_dead = 1
                    if target_tile.danger_level > 0.5 and scout_party_size < 5:
                         num_dead = min(scout_party_size, random.randint(1, 3)) # Ambush kills more if small party
                    
                    scout_deaths = num_dead
                    self.log(f"⚠️ DANGER: Scouts ambushed at {target_tile.biome}! {num_dead} died. (Party: {scout_party_size})")
                    
                    # Kill random people (Assumed scouts are random adults)
                    victims = [p for p in living_pop if p.age > 15 and p.is_alive][:num_dead]
                    for v in victims:
                        v.is_alive = False
                        v.cause_of_death = f"Killed by predator in {target_tile.biome}"
            
            if new_tiles > 0:
                 self.log(f"EXPLORATION: Party of {scout_party_size} revealed {new_tiles} areas.")

        # 4. Material Gathering (Dependent on Map)
        if self.tech_tree.techs["primitive_tools"].unlocked:
            # Check Map Resources
            map_stats, _ = self.map.get_stats()
            
            # Wood requires Forests
            forest_mod = min(5.0, map_stats["Forest"] * 0.5) # More forests = easier to find wood. Cap at 5x
            # Stone requires Mountains
            mountain_mod = min(5.0, map_stats["Mountain"] * 0.5)
            
            # Passive gathering of Wood/Stone by idle population or dedicated portion
            num_gatherers = len([p for p in living_pop if p.job == "Gatherer"])
            
            # Efficiency modifiers
            tool_bonus = 1.0
            if self.tech_tree.techs["composite_tools"].unlocked: tool_bonus = 1.5
            
            # If no forest discovered, can't gather wood effectively (driftwood only)
            wood_yield_base = 0.01 if map_stats["Forest"] == 0 else 0.1
            stone_yield_base = 0.01 if map_stats["Mountain"] == 0 else 0.05
            
            wood_gain = num_gatherers * wood_yield_base * tool_bonus * forest_mod
            stone_gain = num_gatherers * stone_yield_base * tool_bonus * mountain_mod
            
            self.inventory["Wood"] += wood_gain
            self.inventory["Stone"] += stone_gain

        # 5. Tech Effects (Fire)
        if self.tech_tree.techs["fire"].unlocked and season == "Winter":
            # Fire reduces metabolic cost in winter
            metabolic_modifier = max(0, metabolic_modifier - 1) # Reduce form 2->1 or 1->0
        
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
            
            p.update(food_available=fed, disease_data=self.diseases, healer_bonus=global_healer_bonus, metabolic_cost_modifier=metabolic_modifier)
            
            # Check for Births
            if p.gender == 'Female' and p.is_pregnant:
                if p.advance_pregnancy():
                    # Baby Born!
                    father = next((f for f in self.population if f.id == p.partner_id), None)
                    # Even if father dead, genetics pass
                    parents = [p]
                    if father: parents.append(father)
                    
                    baby = Human(age=0, parents=parents, traits_pool=self.traits_df)
                    self.population.append(baby)
                    
                    father_name = father.id if father else "Unknown"
                    self.log(f"BIRTH: {p.id} gave birth to {baby.id} (Father: {father_name}, Family: {baby.family_id})")

            if not p.is_alive and p.cause_of_death != "Already Dead": 
                # He might have died in update()
                deaths_today += 1
                self.log(f"{p.id} died of {p.cause_of_death}")

        # 3. Disease Outbreak & Spread
        self._handle_disease(living_pop)
        
        # 4. Reproduction (Mating)
        self._handle_reproduction(living_pop)

    def _handle_reproduction(self, living_pop):
        pop_size = len(living_pop)
        if pop_size >= 250: return # Hard Cap slightly higher
        
        # Density Dependent Fertility (Carrying Capacity)
        density_modifier = 1.0
        if pop_size > 150:
             density_modifier = 0.2 # Drastic reduction
        elif pop_size > 100:
             density_modifier = 0.5 # Soft brake
        
        # Find potential couples
        males = [p for p in living_pop if p.gender == 'Male' and p.age >= 16] # Assuming Age is years again or huge tick number? Let's use 16 for now assuming initial gen is >16
        females = [p for p in living_pop if p.gender == 'Female' and p.age >= 16 and not p.is_pregnant]
        
        random.shuffle(males)
        random.shuffle(females)
        
        # Simple Pair Matching
        for m in males:
            if not females: break
            
            # find a partner not in same family (simple incest check)
            partner = None
            for f in females:
                if f.family_id != m.family_id:
                     partner = f
                     break
            
            if partner:
                females.remove(partner)

                # Use Fertility Score
                fertility_score = partner.calculate_fertility_score()
                
                # Base chance multiplier (daily)
                # If Score is 1.0 (Peak), Annual chance ~10% -> Daily chance ~0.03%
                # That's too low for simulation fun. Let's aim for annual chance ~50% for couples?
                # Daily chance ~0.2%
                
                final_chance = fertility_score * 0.005 # 0.5% chance per day if peak fertility
                
                # Apply Density/Carrying Capacity Brake
                final_chance *= density_modifier
                    
                if random.random() < final_chance:
                    if partner.get_pregnant(m.id):
                         # self.log(f"{partner.id} became pregnant with {m.id}") # Optional detailed log
                        pass

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
                    
                    # Age Susceptibility
                    age_group = "adult"
                    if contact.age < 15: age_group = "child"
                    elif contact.age > 50: age_group = "elder"
                    
                    susceptibility = d_info.get('age_factors', {}).get(age_group, {}).get('susceptibility', 1.0)
                    
                    # Chance = (Base Rate * Susceptibility) - Genetic Resistance
                    chance = (d_info['transmission_rate'] * susceptibility) + (contact.genetic_vulnerability * 0.1)
                    # Check immune traits? (Not implemented deep yet)
                    
                    if random.random() < chance:
                        contact.infect(d_id)

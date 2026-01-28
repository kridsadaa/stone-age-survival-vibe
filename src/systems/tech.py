from src.engine.systems import System
import random
import pandas as pd

class TechSystem(System):
    """
    Manages Civilization Progress (Eras & Technology).
    Global 'evo_score' determines Era progression.
    Eras: Paleolithic -> Mesolithic -> Neolithic -> Bronze Age
    """
    def update(self, state):
        # 1. Calculate Evo Score
        self._calculate_evo_score(state)
        
        # 2. Check Era Progression
        self._check_era_advancement(state)
        
    def _calculate_evo_score(self, state):
        df = state.population
        live_mask = df['is_alive'] == True
        living = df[live_mask]
        
        if len(living) == 0: return

        # Factors
        # A. Population Size (Social Complexity)
        pop_score = len(living) * 0.5
        
        # B. Surplus Resources (Economy)
        # Base: 1000. Surplus is anything above (Pop * 5)
        needed = len(living) * 5
        
        # Realism Phase 5 Compat: 'resources' is now a dict {'wood', 'stone', 'food'}
        res = state.globals['resources']
        total_res = 0
        if isinstance(res, dict):
            total_res = res.get('food', 0) + res.get('wood', 0) + res.get('stone', 0)
        else:
            total_res = res
            
        surplus = max(0, total_res - needed)
        econ_score = surplus * 0.1
        
        # C. Intelligence (Innovation Potential)
        # Using Openness/Conscientiousness/Neuroticism as proxies?
        # Or trait_openness (Curiosity)
        avg_intel = living['trait_openness'].mean() * 100.0
        intel_score = avg_intel * 2.0
        
        # Total
        total_score = pop_score + econ_score + intel_score
        
        # Decay/Fluctuation? No, just raw score mechanism
        state.globals['evo_score'] = total_score
        
        # Log periodically
        if state.day % 30 == 0:
            # print(f"Evo Score: {total_score:.1f} (Pop: {pop_score:.1f}, Econ: {econ_score:.1f}, Intel: {intel_score:.1f})")
            pass

    def _check_era_advancement(self, state):
        score = state.globals.get('evo_score', 0)
        current_era = state.globals.get('era', 'Paleolithic')
        
        # Era Thresholds
        thresholds = {
            'Paleolithic': 0,
            'Mesolithic': 500,   # Tools, Bows
            'Neolithic': 1500,   # Farming, Pottery
            'Bronze Age': 5000   # Metal, Cities
        }
        
        # Logic
        next_era = None
        if current_era == 'Paleolithic' and score > thresholds['Mesolithic']:
            next_era = 'Mesolithic'
        elif current_era == 'Mesolithic' and score > thresholds['Neolithic']:
            next_era = 'Neolithic'
        elif current_era == 'Neolithic' and score > thresholds['Bronze Age']:
            next_era = 'Bronze Age'
            
        if next_era:
            # Innovation Event Check (Random chance to breakthrough)
            # Higher intelligence = Higher chance
            chance = 0.05 # 5% per day once threshold met
            if random.random() < chance:
                state.globals['era'] = next_era
                state.log(f"🚀 ERA ADVANCEMENT! The tribe has entered the {next_era}!")
                
                # Era Benefits
                if next_era == 'Neolithic':
                    state.globals['policy_rationing_strictness'] = 0.3 # Easier food
                elif next_era == 'Bronze Age':
                    pass

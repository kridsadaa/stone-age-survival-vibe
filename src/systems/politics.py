from src.engine.systems import System
import random
import pandas as pd
import numpy as np

class PoliticalSystem(System):
    """
    Manages the Chief and Political stability.
    The Chief acts as the Avatar for the AI.
    """
    def update(self, state):
        df = state.population
        if len(df) == 0: return

        # 1. Check Chief Status
        chief_id = state.globals.get('chief_id', None)
        
        needs_election = False
        if chief_id is None:
            needs_election = True
        else:
            # Check if alive
            chief_row = df[df['id'] == chief_id]
            if chief_row.empty or not chief_row.iloc[0]['is_alive']:
                state.log(f"👑 The Chief has fallen! The tribe mourns.")
                needs_election = True
                
        if needs_election:
            self._elect_new_chief(state)
            
        # 2. Apply Chief Bias to AI Policies
        # Chief Personality influences policy drift
        self._apply_chief_bias(state)
        
    def _elect_new_chief(self, state):
        df = state.population
        live_mask = df['is_alive'] == True
        living = df[live_mask]
        
        if living.empty: return
        
        # Criteria: Oldest (Wisdom) + Respected (if Social System existed fully)
        # For now: Weighted random by Age + High Conscientiousness
        
        candidates = living[living['age'] > 30]
        if candidates.empty:
            candidates = living # Take anyone
            
        # Score = Age * Conscientiousness
        # Explicit copy to allow modification
        scores = candidates['age'].copy()
        if 'trait_conscientiousness' in candidates.columns:
            scores *= (0.5 + candidates['trait_conscientiousness'])
            
        winner_idx = scores.idxmax()
        winner = df.loc[winner_idx]
        
        state.globals['chief_id'] = winner['id']
        state.log(f"🗳️ NEW CHIEF ELECTED: {winner['id']} (Age {winner['age']:.1f})")
        
    def _apply_chief_bias(self, state):
        # AI Sliders are 0.0 - 1.0 in state.globals
        # Chief personality pushes them
        chief_id = state.globals.get('chief_id')
        if not chief_id: return
        
        df = state.population
        chief_row = df[df['id'] == chief_id]
        if chief_row.empty: return
        chief = chief_row.iloc[0]
        
        if 'trait_openness' not in chief: return
        
        # Bias Logic
        # Openness -> Pushes Mating towards 0 (Free Love)
        # Agreeableness -> Pushes Rationing towards 0 (Share All)
        # Conscientiousness -> Pushes both towards 0.5 (Order)
        # Neuroticism -> Random Jitter
        
        # Apply strictness drift
        m_strict = state.globals.get('policy_mating_strictness', 0.5)
        r_strict = state.globals.get('policy_rationing_strictness', 0.5)
        
        drift = 0.001 # Slow daily drift
        
        # Openness vs Tradition
        if chief['trait_openness'] > 0.7:
            m_strict -= drift # More freedom
        elif chief['trait_openness'] < 0.3:
            m_strict += drift # More tradition
            
        # Agreeableness vs Pragmatism
        if chief['trait_agreeableness'] > 0.7:
            r_strict -= drift # More sharing
        elif chief['trait_agreeableness'] < 0.3:
            r_strict += drift * 2 # More selfish/strict
            
        # Neuroticism (Chaos)
        if chief['trait_neuroticism'] > 0.8:
            if random.random() < 0.1:
                state.log("😨 The Chief is paranoid! Policy fluctuates!")
                m_strict += random.uniform(-0.1, 0.1)
                r_strict += random.uniform(-0.1, 0.1)
                
        # Clamp
        state.globals['policy_mating_strictness'] = max(0.0, min(1.0, m_strict))
        state.globals['policy_rationing_strictness'] = max(0.0, min(1.0, r_strict))

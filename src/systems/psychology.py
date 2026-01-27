import pandas as pd
import numpy as np
import random
from src.engine.systems import System

class PsychologySystem(System):
    """
    Manages the mental state of the tribe (OCEAN Traits).
    Handles:
    - Happiness (0-100)
    - Rebellion (0.0-1.0)
    - Crime (Theft, Rule Breaking)
    - Exile / Exodus
    """
    def update(self, state):
        df = state.population
        if len(df) == 0: return

        live_mask = df['is_alive'] == True
        if not live_mask.any(): return
        
        # 1. Initialize Columns if missing (for old saves)
        if 'happiness' not in df.columns: df['happiness'] = 100.0
        if 'rebellion' not in df.columns: df['rebellion'] = 0.0
        if 'criminal_history' not in df.columns: df['criminal_history'] = 0
        if 'trait_openness' not in df.columns: 
            # Default mid-traits
            for t in ['trait_openness', 'trait_conscientiousness', 'trait_extraversion', 
                      'trait_agreeableness', 'trait_neuroticism']:
                df[t] = 0.5

        # 2. Happiness Decay & Restoration
        # Base Decay
        df.loc[live_mask, 'happiness'] -= 1.0
        
        # Restore if Healthy & Fed
        healthy_mask = (df['hp'] > 80) & (df['stamina'] > 50) & live_mask
        df.loc[healthy_mask, 'happiness'] += 2.0
        
        # 3. Policy Friction (The Core Mechanic)
        m_strict = state.globals.get('policy_mating_strictness', 0.5)
        r_strict = state.globals.get('policy_rationing_strictness', 0.5)
        
        # High Openness hates Strict Mating
        # If strict > 0.7, Openness > 0.7 suffers
        oppressed_m = (df['trait_openness'] > 0.7) & (m_strict > 0.7) & live_mask
        df.loc[oppressed_m, 'happiness'] -= 2.0
        
        # Low Agreeableness hates Strict Rationing (Selfish)
        # If strict > 0.6 (Not sharing), Agreeableness < 0.4 gets mad
        selfish_r = (df['trait_agreeableness'] < 0.4) & (r_strict > 0.6) & live_mask
        df.loc[selfish_r, 'happiness'] -= 3.0
        
        # High Conscientiousness LOVES Order (Bonus)
        order_lovers = (df['trait_conscientiousness'] > 0.7) & (m_strict > 0.5) & live_mask
        df.loc[order_lovers, 'happiness'] += 1.0

        # Clamp Happiness
        df.loc[live_mask, 'happiness'] = df.loc[live_mask, 'happiness'].clip(0, 100)
        
        # 4. Rebellion Calculation
        # Rebellion grows if Happiness < 30
        # Multiplied by Neuroticism (Sensitivity to stress)
        unhappy_mask = (df['happiness'] < 30) & live_mask
        
        # Vectorized Rebellion Growth
        # Rate = 0.05 * Neuroticism
        df.loc[unhappy_mask, 'rebellion'] += (0.05 * df.loc[unhappy_mask, 'trait_neuroticism'])
        
        # Rebellion Decay if Happy > 50
        happy_mask = (df['happiness'] > 50) & live_mask
        df.loc[happy_mask, 'rebellion'] -= 0.05
        
        df.loc[live_mask, 'rebellion'] = df.loc[live_mask, 'rebellion'].clip(0.0, 1.0)
        
        # 5. Crime & Punishment
        # If Rebellion > 0.8, commit crime (Steal Food)
        rebels = df[(df['rebellion'] > 0.8) & live_mask]
        
        if len(rebels) > 0:
            # Crime: Theft (Eat extra food, ignore rationing)
            # Logic: If resource > 0, they take 5 units
            steal_amt = len(rebels) * 5.0
            if state.globals['resources'] > steal_amt:
                state.globals['resources'] -= steal_amt
                df.loc[rebels.index, 'stamina'] += 10 # Thieves get full
                df.loc[rebels.index, 'criminal_history'] += 1
                state.log(f"⚠️ {len(rebels)} rebels stole food!")
                
            # Punish (Exile)
            # If AI Punishment Slider (Need to add this too? For now Check Ratio)
            # Let's say default justice for now
            # If criminal_history > 5, EXILE
            criminals = df[(df['criminal_history'] > 5) & live_mask]
            if len(criminals) > 0:
                # Exile logic: Kill them? Or just mark is_alive=False with cause "Exiled"
                state.log(f"⚖️ {len(criminals)} criminals were EXILED from the tribe.")
                df.loc[criminals.index, 'is_alive'] = False
                df.loc[criminals.index, 'cause_of_death'] = "Exiled"
                df.loc[criminals.index, 'hp'] = 0

        # 6. Mass Exodus (Game Over)
        # If avg happiness < 20, people leave
        avg_happy = df.loc[live_mask, 'happiness'].mean()
        if avg_happy < 20:
            state.log("🔥 THE TRIBE IS RIOTING! Mass Exodus imminent!")
            # 10% Chance per tick to lose 20% of pop
            if random.random() < 0.1:
                leavers = df[live_mask].sample(frac=0.2).index
                df.loc[leavers, 'is_alive'] = False
                df.loc[leavers, 'cause_of_death'] = "Left Tribe"
                state.log(f"🏃 {len(leavers)} people fled the tribe due to unhappiness!")

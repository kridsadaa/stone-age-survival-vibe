import pandas as pd
import numpy as np
import random
from src.engine.systems import System

class GeneticsSystem(System):
    """
    Handles Genetics, Inheritance, and Evolution.
    - Assigns Genomes to new agents.
    - Calculates Genetic Vulnerability (Inbreeding).
    """
    def __init__(self):
        self.GENOME_LENGTH = 32
        self.BASES = ['A', 'C', 'G', 'T']
    
    def update(self, state):
        df = state.population
        
        # 1. Initialize Genome for those who lack it (Initial Pop or New Mutations)
        # Check if column exists, if not create
        if 'genome' not in df.columns:
            df['genome'] = None
            
        if 'genetic_vulnerability' not in df.columns:
            df['genetic_vulnerability'] = 0.0
            
        # Find agents without genome
        no_genome_mask = df['genome'].isnull()
        if no_genome_mask.any():
            missing_indices = df[no_genome_mask].index
            
            for idx in missing_indices:
                person = df.loc[idx]
                
                # Check if parents exist in population (Inheritance)
                # We need columns 'mother_id' and 'father_id' ideally.
                # Currently BiologySystem only passed 'family_id' and 'partner_id' helps find father but child row needs explicit parent links.
                # Assuming BiologySystem adds 'mother_id' and 'father_id' to `new_babies`.
                
                mom_id = person.get('mother_id')
                dad_id = person.get('father_id')
                
                if mom_id and dad_id:
                    self._inherit_genome(state, idx, mom_id, dad_id)
                else:
                    self._generate_random_genome(state, idx)
                    
    def _generate_random_genome(self, state, idx):
        # Random sequence
        genome = "".join(random.choices(self.BASES, k=self.GENOME_LENGTH))
        state.population.at[idx, 'genome'] = genome
        # Base vulnerability for randoms is low (diverse)
        state.population.at[idx, 'genetic_vulnerability'] = random.uniform(0.0, 0.1)

    def _inherit_genome(self, state, child_idx, mom_id, dad_id):
        df = state.population
        
        # Retrieve parents
        # This search might be slow if pop is huge, but usually number of babies per tick is low.
        mom = df[df['id'] == mom_id]
        dad = df[df['id'] == dad_id]
        
        if mom.empty or dad.empty:
            # Fallback if parents died/gone
            self._generate_random_genome(state, child_idx)
            return
            
        mom_genome = mom.iloc[0]['genome']
        dad_genome = dad.iloc[0]['genome']
        
        if not mom_genome or not dad_genome:
             self._generate_random_genome(state, child_idx)
             return
             
        # Crossover (50/50 split per base)
        # Vectorized string ops is hard, do list comprehension
        child_bases = []
        similarity_hits = 0
        
        for i in range(self.GENOME_LENGTH):
            m_base = mom_genome[i]
            d_base = dad_genome[i]
            
            if m_base == d_base:
                similarity_hits += 1
            
            # 50% chance
            if random.random() < 0.5:
                child_bases.append(m_base)
            else:
                child_bases.append(d_base)
                
        # Mutation (1% chance per base)
        for i in range(self.GENOME_LENGTH):
            if random.random() < 0.01:
                child_bases[i] = random.choice(self.BASES)
                
        child_genome = "".join(child_bases)
        
        # Inbreeding Calculation
        # Similarity = Hits / Length
        similarity = similarity_hits / self.GENOME_LENGTH
        
        # Vulnerability Mapping
        # < 0.5: Healthy Diversity
        # 0.5 - 0.7: Moderate
        # > 0.8: High Risk (Inbreeding)
        # Power curve: vul = similarity ^ 4
        # e.g. 0.5^4 = 0.06 (Low)
        # e.g. 0.8^4 = 0.40 (High)
        # e.g. 0.9^4 = 0.65 (Very High)
        
        vul = similarity ** 4.0
        
        # Cap
        vul = min(1.0, vul)
        
        state.population.at[child_idx, 'genome'] = child_genome
        vul = similarity ** 4.0
        
        # Cap
        vul = min(1.0, vul)
        
        state.population.at[child_idx, 'genome'] = child_genome
        state.population.at[child_idx, 'genetic_vulnerability'] = vul
        
        # --- Deep Psychology: Nature vs Nurture ---
        # 50% Parents (Avg), 50% Experience (Random)
        traits = ['trait_openness', 'trait_conscientiousness', 'trait_extraversion', 
                  'trait_agreeableness', 'trait_neuroticism', 'libido', 'attractiveness', 'skin_tone']
        
        for t in traits:
            # Check if parents have this trait (compatibility)
            if t in mom and t in dad:
                m_val = mom.iloc[0].get(t, 0.5)
                d_val = dad.iloc[0].get(t, 0.5)
                
                avg_parent = (m_val + d_val) / 2.0
                experience = random.random() # Random noise
                # For Attractiveness, skew slightly higher if healthy parents? 
                if t == 'attractiveness':
                     experience = random.gauss(0.5, 0.15)
                elif t == 'libido':
                     experience = random.betavariate(2, 5)
                     
                # 50/50 Mix
                final_val = (0.5 * avg_parent) + (0.5 * experience)
                
                # Mutation / Drift
                final_val += random.gauss(0, 0.05)
                
                # Clip
                final_val = max(0.0, min(1.0, final_val))
                
                state.population.at[child_idx, t] = final_val

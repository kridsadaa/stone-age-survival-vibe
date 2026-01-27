from src.engine.systems import System
import random
import pandas as pd
import numpy as np

class KnowledgeSystem(System):
    """
    Manages Memetic Knowledge (Viral Skills).
    Skills spread like viruses:
    - Vertical: Parent -> Child
    - Horizontal: Spouse -> Spouse
    - Diffusion: Random contact
    
    Data: state.skills DataFrame (agent_id, skill_name, level)
    """
    def update(self, state):
        # 1. Initialize if needed
        if not hasattr(state, 'skills'):
            state.skills = pd.DataFrame(columns=['agent_id', 'skill', 'level'])
            
        # 2. Random Discovery (Mutation)
        # Smart people invent things
        if state.day % 30 == 0:
            self._handle_discovery(state)
            
        # 3. Transmission (Viral Spread)
        if state.day % 7 == 0:
            self._handle_transmission(state)
            
    def _handle_discovery(self, state):
        df = state.population
        live_mask = df['is_alive'] == True
        
        # High Intel Agents (Openness > 0.8)
        inventors = df[live_mask & (df['trait_openness'] > 0.8)]
        
        possible_skills = ['Weaving', 'Pottery', 'Herbalism', 'Farming', 'Archery']
        
        for idx, inventor in inventors.iterrows():
            if random.random() < 0.05: # 5% chance per month
                skill = random.choice(possible_skills)
                self._learn_skill(state, inventor['id'], skill, 0.1)
                state.log(f"💡 INNOVATION! {inventor['id']} discovered {skill}!")

    def _handle_transmission(self, state):
        # A. Spouse Teaching (Horizontal)
        rels = state.relationships
        if rels.empty: return
        
        partners = rels[rels['type'].isin(['Spouse', 'Lover'])]
        
        # Iterate partners
        # Optimization: Don't loop all. Sample?
        # For now, loop all active (assuming < 1000 pairs)
        
        skills_df = state.skills
        if skills_df.empty: return
        
        # Convert skills to dict for fast lookup: {agent_id: {skill: level}}
        # This is expensive every tick. Maybe optimize later.
        
        for _, rel in partners.iterrows():
            id_a = rel['id_a']
            id_b = rel['id_b']
            
            # Get skills of A
            skills_a = skills_df[skills_df['agent_id'] == id_a]
            if not skills_a.empty:
                for _, s in skills_a.iterrows():
                    # Teach B (Chance based on affinity/intel)
                    if random.random() < 0.2:
                        self._learn_skill(state, id_b, s['skill'], s['level'] * 0.5)

    def _learn_skill(self, state, agent_id, skill, amount):
        df = state.skills
        mask = (df['agent_id'] == agent_id) & (df['skill'] == skill)
        
        if mask.any():
            # Improve
            # Logic: Diminishing returns?
            current = df.loc[mask, 'level'].values[0]
            new_level = min(1.0, current + (amount * 0.1))
            idx = df[mask].index[0]
            state.skills.at[idx, 'level'] = new_level
        else:
            # Learn New
            new_row = {'agent_id': agent_id, 'skill': skill, 'level': amount}
            state.skills = pd.concat([state.skills, pd.DataFrame([new_row])], ignore_index=True)

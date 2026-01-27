from src.engine.systems import System
import random
import pandas as pd

class SocialSystem(System):
    """
    Manages relationships between agents.
    Stored in state.globals['relationships'] = {
        'HMN-ID-A': {
            'HMN-ID-B': {'affection': 0.5, 'respect': 0.2},
            ...
        }
    }
    """
    def update(self, state):
        # 1. Init Data Structure
        if 'relationships' not in state.globals:
            state.globals['relationships'] = {}
            
        rels = state.globals['relationships']
        df = state.population
        
        live_mask = df['is_alive'] == True
        living_ids = df[live_mask]['id'].values
        
        # 2. Entropy (Decay connections)
        # Every 7 days, prune or decay
        if state.day % 7 == 0:
            self._decay_relationships(rels, state)
            
        # 3. New Events Interaction
        # A. Family Bonding (Parents love kids)
        # Scan recent births (Age < 1)
        # Optimization: Don't scan entire pop every tick.
        # Maybe check `state.birth_events` if we had event bus?
        # For now, simplistic random bonding among family members
        
        if state.day % 30 == 0:
            self._family_bonding(df, rels)
            
        # B. Work Respect
        # People with same job gain respect
        if state.day % 10 == 0:
            self._work_bonding(df, rels)
            
    def _decay_relationships(self, rels, state):
        # Remove dead people keys
        # This can be slow if map is huge.
        pass # Optimization for later
        
        # Decay and Prune logic
        # Optimization: Use list to collect keys to delete to avoid modifying dict while iterating
        
        # 1. Prune Dead Agents from Keys
        dead_ids = set(state.population[state.population['is_alive'] == False]['id'].values)
        if dead_ids:
            # Drop dead keys
             keys_to_drop = [k for k in rels if k in dead_ids]
             for k in keys_to_drop:
                 del rels[k]
                 
        # 2. Iterate and Decay
        # Limit processing per tick to avoid spikes? For now full pass but aggressive pruning.
        
        for p1 in list(rels.keys()): # List copy for safety
            if p1 not in rels: continue
            
            sub_rels = rels[p1]
            to_remove = []
            
            for p2 in sub_rels:
                # Remove if target is dead
                if p2 in dead_ids:
                    to_remove.append(p2)
                    continue
                    
                # Decay
                sub_rels[p2]['affection'] *= 0.95 # Faster decay (5% per week)
                sub_rels[p2]['respect'] *= 0.95
                
                # Prune Weak Links (Near zero)
                if abs(sub_rels[p2]['affection']) < 0.1 and abs(sub_rels[p2]['respect']) < 0.1:
                    to_remove.append(p2)
                    
            # Apply Removals
            for p2 in to_remove:
                del sub_rels[p2]
                
            # If empty, remove p1
            if not sub_rels:
                del rels[p1]
                
    def _family_bonding(self, df, rels):
        # Boost affection between parents and children
        # Iterate living people who have parents
        children = df[(df['mother_id'].notnull()) & (df['is_alive'])]
        
        # Sampling to save performance
        sample = children.sample(frac=0.1) if len(children) > 100 else children
        
        for idx, child in sample.iterrows():
             cid = child['id']
             mid = child['mother_id']
             fid = child['father_id']
             
             self._add_score(rels, cid, mid, 'affection', 0.1)
             self._add_score(rels, mid, cid, 'affection', 0.1)
             
             if fid:
                 self._add_score(rels, cid, fid, 'affection', 0.1)
                 self._add_score(rels, fid, cid, 'affection', 0.1)

    def _work_bonding(self, df, rels):
        # Find people of same job
        jobs = df['job'].unique()
        for job in jobs:
            workers = df[(df['job'] == job) & (df['is_alive'])]
            if len(workers) < 2: continue
            
            # Pair up random 5 pairs
            for _ in range(5):
                 p1 = workers.sample(1).iloc[0]['id']
                 p2 = workers.sample(1).iloc[0]['id']
                 if p1 != p2:
                     self._add_score(rels, p1, p2, 'respect', 0.05)

    def _add_score(self, rels, p1, p2, type, amount):
        if not p1 or not p2: return
        
        if p1 not in rels: rels[p1] = {}
        if p2 not in rels[p1]: rels[p1][p2] = {'affection': 0, 'respect': 0}
        
        rels[p1][p2][type] += amount
        rels[p1][p2][type] = max(-1.0, min(1.0, rels[p1][p2][type])) # Clamp -1 to 1

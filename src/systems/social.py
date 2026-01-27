from src.engine.systems import System
import random
import pandas as pd
import numpy as np

class SocialSystem(System):
    """
    Manages the Relationship Graph (DataFrame).
    Columns: id_a, id_b, type (Spouse, Lover, Friend), affection (0-1), commitment (0-1), start_day
    """
    def update(self, state):
        # 1. Decay Interactions
        # Every 7 days, decay affection slightly
        if state.day % 7 == 0:
            self._decay_relationships(state)
            
        # 2. Prune Dead Links
        # Every 30 days
        if state.day % 30 == 0:
            self._prune_dead(state)

    def add_relationship(self, state, id_a, id_b, type="Lover", affection=0.5, commitment=0.0):
        """Creates or updates a link (Undirected? No, Directed usually better for asymmetry, but Spouse is symmetric)"""
        # For simplicity, let's treat Spouse as Symmetric (2 rows)
        # Lover can be asymmetric realistically, but for game mechanics symmetric is easier to track "Couple" status.
        # Let's enforce symmetry for Spouse/Lover to avoid headaches.
        
        df = state.relationships
        
        # Check exists
        mask = ((df['id_a'] == id_a) & (df['id_b'] == id_b))
        
        if mask.any():
            # Update
            # idx = df[mask].index[0]
            # state.relationships.at[idx, 'type'] = type
            # state.relationships.at[idx, 'affection'] = affection
            # state.relationships.at[idx, 'commitment'] = commitment
            pass # Todo: Update logic
        else:
            # Add New (Both directions)
            new_rows = [
                {'id_a': id_a, 'id_b': id_b, 'type': type, 'affection': affection, 'commitment': commitment, 'start_day': state.day},
                {'id_a': id_b, 'id_b': id_a, 'type': type, 'affection': affection, 'commitment': commitment, 'start_day': state.day}
            ]
            state.relationships = pd.concat([state.relationships, pd.DataFrame(new_rows)], ignore_index=True)

    def get_partners(self, state, person_id):
        """Returns list of partner IDs (Spouse or Lover)"""
        df = state.relationships
        partners = df[
            (df['id_a'] == person_id) & 
            (df['type'].isin(['Spouse', 'Lover']))
        ]['id_b'].values
        return partners
        
    def _decay_relationships(self, state):
        # Vectorized Decay
        # Affection *= 0.99
        if len(state.relationships) > 0:
            state.relationships['affection'] *= 0.98 
            
            # If Affection < 0.1, Breakup?
            # breakup_mask = state.relationships['affection'] < 0.1
            # But we need to handle type changes (Spouse -> Ex)
            pass

    def _prune_dead(self, state):
        # Remove links where id_a or id_b is not in population or is dead
        # living_ids = set(state.population[state.population['is_alive']]['id'])
        # Actually we keep dead in history? No, for now prune active graph.
        
        live_mask = state.population['is_alive'] == True
        live_ids = set(state.population[live_mask]['id'])
        
        df = state.relationships
        valid_mask = (df['id_a'].isin(live_ids)) & (df['id_b'].isin(live_ids))
        
        if not valid_mask.all():
            state.relationships = df[valid_mask].copy()
            # Log breakups due to death?

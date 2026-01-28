from src.engine.systems import System
import random
import pandas as pd

class TribalSystem(System):
    """
    Manages Tribe Metadata and Inter-Tribal Relations.
    Tribes: Red_Tribe, Blue_Tribe, Green_Tribe
    """
    def update(self, state):
        # 1. Initialize Metadata if missing
        if not state.tribes:
            self._init_tribes(state)
            
        # 2. Assign Leaders (Headman) per Tribe
        self._assign_leaders(state)
        
        # 3. Inter-Tribal Events (War/Trade)
        pass # Todo Next

    def _assign_leaders(self, state):
        """
        Selects a 'Headman' for each tribe based on Prestige.
        Also assigns Roles (Hunter/Gatherer) based on traits if not set.
        """
        # A. Assign Basic Roles based on Gender/Traits if currently generic
        # (Simple logic: Men -> Hunter, Women -> Gatherer, or strength based)
        # Vectorized update for performance
        live_mask = state.population['is_alive'] == True
        
        # If job is 'Gatherer' (default), auto-assign
        # Men with high Conscientiousness -> Hunter
        mask_hunter = live_mask & (state.population['gender'] == 'Male') & (state.population['role'] == 'Gatherer')
        if mask_hunter.any():
            state.population.loc[mask_hunter, 'role'] = 'Hunter'
            
        # Women with high Openness -> Crafter? For now default all women to Gatherer
        
        # B. Determine Leaders
        # For each tribe, find alive member with max Prestige
        if not hasattr(state, 'tribes_leaders'):
            state.tribes_leaders = {}
            
        for t_id in state.tribes.keys():
            tribe_mask = live_mask & (state.population['tribe_id'] == t_id)
            tribe_members = state.population[tribe_mask]
            
            if len(tribe_members) > 0:
                # Calculate Prestige (if 0)
                # Prestige = Age + (Happiness * 0.1)
                # Vectorized calc for those with 0 prestige
                zero_pres = tribe_members['prestige'] == 0
                if zero_pres.any():
                    # Need global index to update state.population
                    idx_to_update = tribe_members[zero_pres].index
                    state.population.loc[idx_to_update, 'prestige'] = \
                        state.population.loc[idx_to_update, 'age'] + \
                        (state.population.loc[idx_to_update, 'happiness'] * 0.1)

                # Pick leader
                leader_idx = state.population[tribe_mask]['prestige'].idxmax()
                leader_id = state.population.at[leader_idx, 'id']
                
                # Check if changed
                current = state.tribes_leaders.get(t_id)
                if current != leader_id:
                    state.tribes_leaders[t_id] = leader_id
                    
                    # SYNC with Tribes Metadata for UI
                    if t_id in state.tribes:
                         state.tribes[t_id]['chief_id'] = leader_id
                    
                    # Update Job Role
                    state.population.at[leader_idx, 'role'] = 'Chief'
                    # Remove "Chief" role from previous leader if exists
                    if current:
                        prev_mask = state.population['id'] == current
                        if prev_mask.any():
                             state.population.loc[prev_mask, 'role'] = 'Elder' # Demote to Elder

                    name = f"Elder {leader_id[-4:]}"
                    state.log(f"👑 {t_id} has a new Headman: {name} (Prestige: {state.population.at[leader_idx, 'prestige']:.1f})")
                    
                    # Apply Leadership Buff (example)
                    # Everyone in tribe gets +5 happiness
                    state.population.loc[tribe_mask, 'happiness'] += 5.0

    def _init_tribes(self, state):
        state.tribes = {
            'Red_Tribe': {'color': '#FF4B4B', 'relations': {'Blue_Tribe': 0, 'Green_Tribe': -10}, 'policy': 'Aggressive'},
            'Blue_Tribe': {'color': '#4B4BFF', 'relations': {'Red_Tribe': 0, 'Green_Tribe': 10}, 'policy': 'Peaceful'},
            'Green_Tribe': {'color': '#4BFF4B', 'relations': {'Red_Tribe': -10, 'Blue_Tribe': 10}, 'policy': 'Neutral'}
        }
        state.log("⚔️ TRIBES ESTABLISHED: Red, Blue, Green have claimed territories.")

from src.engine.systems import System
import pandas as pd
import numpy as np
import random

class SocialSystem(System):
    """
    Manages Social Interactions beyond Biology.
    - Gossip (Opinion Propagation)
    - Reputation Building
    - Friendships/Rivalries
    """
    def update(self, state):
        # Run daily
        self._handle_gossip(state)
        
    def _handle_gossip(self, state):
        """
        Agents meet nearby neighbors and exchange opinions.
        """
        df = state.population
        living = df[df['is_alive'] == True]
        if len(living) < 2: return
        
        # Ensure 'opinions' structure exists
        # opinions = {(id_observer, id_target): score}
        if not hasattr(state, 'opinions'):
            state.opinions = {}
            
        # 1. Spatial Clustering (Find pairs)
        # Random Sample of interaction attempts (e.g. 10% of pop per day)
        interaction_count = int(len(living) * 0.1)
        
        # We need efficient neighbor lookup. 
        # For now, just pick random pairs and check distance? (O(N) vs Vectorized)
        # Vectorized Approach:
        # 1. Pick N "initiators".
        # 2. Find nearby "receivers" for each.
        
        initiators = living.sample(n=interaction_count)
        
        if 'x' not in living.columns: return
        
        # This loop is heavy if N is large. Optimization needed later.
        for idx, initiator in initiators.iterrows():
            # Find neighbors < 20.0
            ix, iy = initiator['x'], initiator['y']
            
            # Simple vector distance to all living (can optimize with KDTree later)
            dists = np.sqrt((living['x'] - ix)**2 + (living['y'] - iy)**2)
            
            # Neighbors (exclude self)
            neighbors = living[(dists < 20.0) & (living.index != idx)]
            
            if neighbors.empty: continue
            
            # Pick one neighbor to gossip with
            receiver = neighbors.sample(1).iloc[0]
            
            self._gossip_event(state, initiator, receiver)
            
    def _gossip_event(self, state, teller, listener):
        """
        Teller shares an opinion about a Target to Listener.
        """
        # 1. Teller picks a Target
        # Someone they have an opinion on (from opinions dict or relationships) Or random prominent figure (Chief)
        
        # Simplified: Teller talks about the Chief or a random person
        target_id = None
        
        # 60% Chance: Talk about Chief
        if random.random() < 0.6:
            chief_id = state.globals.get('chief_id')
            if chief_id: target_id = chief_id
            
        # 40% Chance: Talk about someone they know (Relationship)
        if not target_id:
            # Look up relationships
            # This requires scanning rel dataframe, might be slow.
            # Fallback: Talk about random neighbor
            target_id = listener['id'] # Self-talk? No.
            
        if not target_id or target_id == listener['id']: return
        
        # 2. Determine Message Content
        # Teller's Opinion of Target
        # Default 0 (Neutral)
        teller_op = state.opinions.get((teller['id'], target_id), 0.0)
        
        # If neutral, maybe form one based on Tribe?
        if teller_op == 0.0:
            # Tribal Bias: Same tribe = +10, Diff tribe = -5
            # We need target's tribe.
            # (skip for speed now, assume 0)
            pass
            
        # 3. Message: "Target is [Good/Bad]"
        message_strength = teller_op
        
        # 4. Listener Processes
        # Factors:
        # A. Trust in Teller (Friendship? Similarity?)
        # B. Listener's Personality (Agreeableness)
        # C. Listener's Existing Opinion
        
        # A. Trust (Base + Agreeableness)
        agreeableness = listener.get('trait_agreeableness', 0.5)
        trust = 0.5 + (agreeableness * 0.5) # 0.5 to 1.0
        
        # B. Apply Influence
        # New Opinion = Old + (Message * Trust * Volatility)
        old_op = state.opinions.get((listener['id'], target_id), 0.0)
        change = (message_strength - old_op) * trust * 0.2
        
        new_op = old_op + change
        new_op = max(-100, min(100, new_op)) # Clamp
        
        state.opinions[(listener['id'], target_id)] = new_op
        
        # Log significant gossip
        if abs(change) > 0.1:
            dir_str = "📈" if change > 0 else "📉"
            # Log for Listener (They changed their mind)
            state.log(f"🗣️ Heard gossip from {teller['id'][-4:]} about {str(target_id)[-4:]}: Opinion {dir_str} ({change:+.1f})", agent_id=listener['id'], category='Social')
            # Log for Teller (They talked)
            state.log(f"🗣️ Shared gossip with {listener['id'][-4:]} about {str(target_id)[-4:]}", agent_id=teller['id'], category='Social')

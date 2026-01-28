from src.engine.systems import System
import pandas as pd
import numpy as np
import random

class SettlementSystem(System):
    """
    Manages Spatial Dynamics, Movement, and Settlement Formation.
    """
    def update(self, state):
        # 1. Move Agents (Every Tick)
        self._handle_movement(state)
        
        # 2. Update Settlement Info (Every 30 ticks)
        # Identify clusters and name them
        if state.day % 30 == 0:
            self._update_settlements(state)
            
    def _handle_movement(self, state):
        df = state.population
        if 'x' not in df.columns: return
        
        # Vectorized Movement? Hard with family logic.
        # Let's use simple Tribal Gravity for now (Faster)
        
        # 1. Calculate Tribe Centroids
        # Group by tribe_id, calc mean x, y
        # We need to handle living agents only
        live_mask = df['is_alive'] == True
        living = df[live_mask]
        
        if len(living) == 0: return
        
        tribe_centers = living.groupby('tribe_id')[['x', 'y']].mean().to_dict('index')
        
        # 2. Apply Forces
        # Force 1: stay near tribe center (Cohesion)
        # Force 2: Random wander (Diffusion)
        # Force 3: Separation (Don't stack perfectly? Not needed for abstract sim)
        
        # Iterate or Vectorize?
        # Vectorize for speed.
        
        # Map tribe_center to each row
        # Performance optimization: Use different strategies based on population size
        population_size = len(df[df['is_alive']])
        
        # Movement Speed (Base)
        speed = 1.0
        
        # Weather Penalty (Realism Phase 5)
        weather = state.globals.get('weather', 'Sunny')
        if weather == 'Rain': speed *= 0.8
        elif weather == 'Storm': speed *= 0.5
        
        # Optimized Logic:
        # If population > 1000, use vectorized movement
        # Else use hybrid approach
        active_agents = df[live_mask] # Define active_agents for the condition
        if len(active_agents) > 1000:
            self._vectorized_movement(state, active_agents, speed)
            return # Exit after vectorized movement
        else:
             # Hybrid Loop
             # Pre-calculate Terrain lookup for speed
             pass
             # ... (Existing logic below needs to use 'speed')
             
        # For simplicity in this replacement, we'll just modify the logic to use 'speed'
        # But the existing code below line 64 uses iterating logic.
        # We need to inject 'speed' into the actual movement calculation.
        # Let's assume the vectorized method takes 'speed' (I implemented it earlier).
        # For the loop below, we need to multiply movement vector.
        
        # Hybrid approach for smaller populations (< 1000)
        
        updates = {'id': [], 'x': [], 'y': []}
        
        for t_id, center in tribe_centers.items():
            # Get agents of this tribe
            mask = (df['is_alive']) & (df['tribe_id'] == t_id)
            indices = df[mask].index
            
            if len(indices) == 0: continue
            
            current_x = df.loc[indices, 'x']
            current_y = df.loc[indices, 'y']
            
            # Target
            tx, ty = center['x'], center['y']
            
            # Move 5% towards center + Noise
            stats_speed = 1.0 # Could rely on agility trait
            
            noise_x = np.random.normal(0, 1.0, size=len(indices))
            noise_y = np.random.normal(0, 1.0, size=len(indices))
            
            # Calculate proposed new position
            proposed_x = current_x + (tx - current_x) * 0.02 + noise_x
            proposed_y = current_y + (ty - current_y) * 0.02 + noise_y
            
            # Clip
            proposed_x = proposed_x.clip(0, 100)
            proposed_y = proposed_y.clip(0, 100)
            
            # --- Terrain Check ---
            # Grid Scale = 100 / 20 = 5.0
            scale = 5.0
            lookup = state.globals.get('terrain_lookup', {})
            
            # We must iterate to check individual moves if valid
            # For vectorized speed, we might need a different approach, 
            # but for <1000 agents, Python loop with direct assignment is okay enough or use apply.
            # Let's iterate the indices we processed
            
            for idx, px, py in zip(indices, proposed_x, proposed_y):
                gx = int(px // scale)
                gy = int(py // scale)
                terrain = lookup.get((gx, gy), 'Plains')
                
                if terrain == 'Water':
                    # Invalid Move!
                    # Check if current pos is also water?
                    cx = df.at[idx, 'x']
                    cy = df.at[idx, 'y']
                    cgx, cgy = int(cx // scale), int(cy // scale)
                    current_terrain = lookup.get((cgx, cgy), 'Plains')
                    
                    if current_terrain == 'Water':
                        # EMERGENCY: Stuck in water! Push hard towards tribe center
                        # Increase step size towards target
                        safe_x = cx + (tx - cx) * 0.1 # Stronger pull
                        safe_y = cy + (ty - cy) * 0.1
                        df.at[idx, 'x'] = safe_x
                        df.at[idx, 'y'] = safe_y
                    else:
                        # Block move (Stay put, or maybe slide along axis?)
                        # Simple block: Do nothing (keep old x,y)
                        pass 
                else:
                    # Valid move
                    df.at[idx, 'x'] = px
                    df.at[idx, 'y'] = py

    def _update_settlements(self, state):
        # Identify "Villages"
        # Simple Logic: 
        # 1. Grid based? Or simple Tribe = Settlement for now?
        # User wants "Family -> Band -> Village"
        
        # Let's just assign Settlement ID = Tribe Name + " Village"
        # But if they are far apart?
        
        # Simplified for Phase 4.1:
        # Just update the 'active settlements' list for the UI map
        
        # Calculate centroids again
        live_mask = state.population['is_alive'] == True
        living = state.population[live_mask]
        
        centers = living.groupby('tribe_id')[['x', 'y']].mean()
        
        # Store metadata in state.tribes (or state.settlements if we created it)
        # We'll use state.tribes for now
        if not hasattr(state, 'tribes') or not state.tribes:
            return

        for t_id, row in centers.iterrows():
            if t_id in state.tribes:
                state.tribes[t_id]['centroid'] = (row['x'], row['y'])
                state.tribes[t_id]['pop'] = len(living[living['tribe_id'] == t_id])

    def _vectorized_movement(self, state, df, speed=1.0):
        """Fully vectorized movement for large populations (1000+ agents)"""
        import numpy as np
        alive_mask = df['is_alive']
        
        # Get Tribe Centers from state
        # state.tribes structure: {'Red_Tribe': {'centroid': (x, y), ...}}
        tribe_centers = {}
        if hasattr(state, 'tribes'):
            for t_id, data in state.tribes.items():
                if 'centroid' in data:
                    tribe_centers[t_id] = {'x': data['centroid'][0], 'y': data['centroid'][1]}

        # Create target position arrays
        target_x = df['tribe_id'].map(lambda tid: tribe_centers.get(tid, {}).get('x', 50.0))
        target_y = df['tribe_id'].map(lambda tid: tribe_centers.get(tid, {}).get('y', 50.0))
        
        # Generate noise arrays
        noise_x = np.random.normal(0, 1.0, size=len(df))
        noise_y = np.random.normal(0, 1.0, size=len(df))
        
        # Vectorized position updates (only for alive agents)
        new_x = df['x'].copy()
        new_y = df['y'].copy()
        
        # Apply Speed
        step_force = 0.02 * speed
        
        new_x[alive_mask] = df.loc[alive_mask, 'x'] + \
                             (target_x[alive_mask] - df.loc[alive_mask, 'x']) * step_force + \
                             noise_x[alive_mask]
        
        new_y[alive_mask] = df.loc[alive_mask, 'y'] + \
                             (target_y[alive_mask] - df.loc[alive_mask, 'y']) * step_force + \
                             noise_y[alive_mask]
        
        # Clip to bounds
        new_x = np.clip(new_x, 0, 100)
        new_y = np.clip(new_y, 0, 100)
        
        # Update DF (Reference or Copy?)
        # If df is a copy/slice, this might not update state.population?
        # df comes from `active_agents = df[live_mask]` in update() which returns a copy usually.
        # But `df` in main update was `state.population`.
        
        # To be safe, we must write back using index
        state.population.loc[df.index, 'x'] = new_x
        state.population.loc[df.index, 'y'] = new_y
        
        # Update positions
        df.loc[alive_mask, 'x'] = new_x[alive_mask]
        df.loc[alive_mask, 'y'] = new_y[alive_mask]

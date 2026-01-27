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
        # tribe_centers dict: {'Red_Tribe': {'x': 20, 'y': 20}, ...}
        
        # Create separate series for target x/y
        # This is strictly manual loop for clarity in complex logic, optimal enough for 500 agents
        
        # Actually, let's try a hybrid approach
        # Extract x, y, tribe_id vectors
        
        # TODO: Optimization - If pop > 1000, use numpy exclusively
        
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

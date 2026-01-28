import random
import pickle
import os
import numpy as np
from src.engine.systems import System

import random
import pickle
import os
import numpy as np
from src.engine.systems import System

class CultureSystem(System):
    """
    The 'Spirit of the Tribe'. now Decentralized!
    Each Tribe has its own Q-Learning Brain.
    
    Manages Tribal Policies:
    - mating_strictness (0.0 - 1.0)
    - rationing_strictness (0.0 - 1.0)
    """
    def __init__(self, brain_path="data/tribal_brains.pkl"):
        self.brain_path = brain_path
        self.brains = {} # Dict[tribe_id, q_table]
        self.last_states = {} # Dict[tribe_id, state_key]
        self.last_actions = {} # Dict[tribe_id, action_idx]
        
        # Learning Params
        self.alpha = 0.1 
        self.gamma = 0.95 
        self.epsilon = 0.2 
        
        # Actions: Adjustments [Increase, Maintain, Decrease]
        # Combined Action Space: 3x3 = 9 Actions
        self.adjustments = [0.1, 0.0, -0.1]
        
        self.load_brains()
        
    def update(self, state):
        # AI runs weekly
        if state.day % 7 != 0:
            return

        # Ensure tribes exist
        if not hasattr(state, 'tribes') or not state.tribes:
            return

        # Process each tribe independently
        for tid in state.tribes.keys():
            self._process_tribe_brain(state, tid)
            
        if state.day % 30 == 0:
            self.save_brains()

    def _process_tribe_brain(self, state, tid):
        # 1. Initialize Brain if new tribe
        if tid not in self.brains:
            self.brains[tid] = {}
        
        # Initialize Policies if missing
        if 'policies' not in state.tribes[tid]:
            state.tribes[tid]['policies'] = {
                'mating_strictness': 0.5,
                'rationing_strictness': 0.5
            }

        # 2. Observe Local State
        current_state = self._get_state_key(state, tid)
        
        # 3. Learn from previous action (if any)
        last_s = self.last_states.get(tid)
        last_a = self.last_actions.get(tid)
        
        if last_s is not None:
            reward = self._calculate_reward(state, tid)
            self._learn(tid, last_s, last_a, reward, current_state)
            
        # 4. Act
        action_idx = self._choose_action(tid, current_state)
        self._apply_policy(state, tid, action_idx)
        
        # 5. Save Context
        self.last_states[tid] = current_state
        self.last_actions[tid] = action_idx

    def _get_state_key(self, state, tid):
        # Filter population for this tribe
        tribe_mask = (state.population['tribe_id'] == tid) & (state.population['is_alive'] == True)
        pop_count = tribe_mask.sum()
        
        if pop_count < 10: pop_s = "CRITICAL"
        elif pop_count < 50: pop_s = "LOW"
        else: pop_s = "HEALTHY"
        
        # Genetic Health of Tribe
        if 'genetic_vulnerability' in state.population.columns and pop_count > 0:
            avg_vul = state.population.loc[tribe_mask, 'genetic_vulnerability'].mean()
        else:
            avg_vul = 0.0
        
        if avg_vul < 0.2: gen_s = "PURE"
        elif avg_vul < 0.5: gen_s = "MIXED"
        else: gen_s = "DEGENERATED"
        
        # Resources (Global Context for now, as local inventory isn't aggregated yet)
        res = state.globals['resources']
        total_food = res.get('food', 0) if isinstance(res, dict) else res
            
        # Per capita relative to global pop (Simulated competition)
        total_alive = len(state.population[state.population['is_alive']])
        food_per_capita = total_food / max(1, total_alive)
        
        if food_per_capita < 5: res_s = "FAMINE"
        elif food_per_capita < 20: res_s = "SCARCE"
        else: res_s = "ABUNDANT"
        
        return (pop_s, gen_s, res_s)

    def _calculate_reward(self, state, tid):
        # Reward based on TRIBE survival
        tribe_mask = (state.population['tribe_id'] == tid) & (state.population['is_alive'] == True)
        pop_count = tribe_mask.sum()
        
        reward = 1.0
        
        # Survival is key
        if pop_count == 0: return -100.0
        
        # Genetics
        if 'genetic_vulnerability' in state.population.columns and pop_count > 0:
            avg_vul = state.population.loc[tribe_mask, 'genetic_vulnerability'].mean()
            if avg_vul > 0.5: reward -= 5.0
            elif avg_vul > 0.3: reward -= 1.0
                
        # Hunger status of tribe members
        # Count starving members
        # Assuming malnutrition check logic exists elsewhere, we check logs or nutrients?
        # Let's check average hp as proxy for health
        avg_hp = state.population.loc[tribe_mask, 'hp'].mean()
        if avg_hp < 50: reward -= 2.0
            
        return reward

    def _choose_action(self, tid, state_key):
        q_table = self.brains[tid]
        
        if state_key not in q_table:
            q_table[state_key] = [0.0] * 9 # 9 Actions
            
        if random.random() < self.epsilon:
            return random.randint(0, 8)
        else:
            max_q = max(q_table[state_key])
            best = [i for i, x in enumerate(q_table[state_key]) if x == max_q]
            return random.choice(best)

    def _apply_policy(self, state, tid, action_idx):
        # Decode action [0-8]
        m_idx = action_idx // 3
        r_idx = action_idx % 3
        
        m_adj = self.adjustments[m_idx]
        r_adj = self.adjustments[r_idx]
        
        # Apply strictness to TRIBE policies
        curr_m = state.tribes[tid]['policies'].get('mating_strictness', 0.5)
        curr_r = state.tribes[tid]['policies'].get('rationing_strictness', 0.5)
        
        new_m = max(0.0, min(1.0, curr_m + m_adj))
        new_r = max(0.0, min(1.0, curr_r + r_adj))
        
        state.tribes[tid]['policies']['mating_strictness'] = new_m
        state.tribes[tid]['policies']['rationing_strictness'] = new_r
        
        # Map back to discrete readable policies for UI/Systems
        state.tribes[tid]['policies']['ratioing_label'] = 'Communal' if new_r < 0.3 else ('Meritocracy' if new_r > 0.7 else 'ChildFirst') # Example mapping
        # Actual mapping:
        # Rationing: 0.0-0.33 (Communal), 0.33-0.66 (ChildFirst - Middle?), 0.66-1.0 (Meritocracy)
        # Let's standardize:
        if new_r <= 0.33: r_lbl = 'Communal'
        elif new_r <= 0.66: r_lbl = 'ChildFirst'
        else: r_lbl = 'Meritocracy'
        
        if new_m > 0.6: m_lbl = 'Strict'
        else: m_lbl = 'Open'
        
        state.tribes[tid]['policies']['mating_label'] = m_lbl
        state.tribes[tid]['policies']['rationing_label'] = r_lbl

    def _learn(self, tid, old_state, action, reward, new_state):
        q_table = self.brains[tid]
        
        if new_state not in q_table:
             q_table[new_state] = [0.0] * 9
             
        old_val = q_table[old_state][action]
        next_max = max(q_table[new_state])
        new_val = old_val + self.alpha * (reward + self.gamma * next_max - old_val)
        q_table[old_state][action] = new_val

    def save_brains(self):
        try:
            os.makedirs(os.path.dirname(self.brain_path), exist_ok=True)
            with open(self.brain_path, 'wb') as f:
                pickle.dump(self.brains, f)
        except: pass

    def load_brains(self):
        if os.path.exists(self.brain_path):
            try:
                with open(self.brain_path, 'rb') as f:
                    self.brains = pickle.load(f)
            except Exception as e: 
                print(f"[WARNING] Failed to load brains: {e}")
                self.brains = {}

    def reset_brain(self, tid=None):
        """Resets the Q-Learning Memory"""
        if tid:
            if tid in self.brains:
                self.brains[tid] = {}
        else:
            self.brains = {}
        self.save_brains()
        print("🧠 AI Brain(s) Reset!")

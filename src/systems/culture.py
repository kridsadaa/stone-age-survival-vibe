import random
import pickle
import os
import numpy as np
from src.engine.systems import System

class CultureSystem(System):
    """
    The 'Spirit of the Tribe'.
    Controls Tribal Policy via Continuous Parameters (Sliders).
    
    Parameters:
    - mating_strictness (0.0 - 1.0): 0.0 = Free Love, 1.0 = Eugenics
    - rationing_strictness (0.0 - 1.0): 0.0 = Communism, 1.0 = Meritocracy
    """
    def __init__(self, brain_path="data/tribal_brain.pkl"):
        self.brain_path = brain_path
        self.q_table = {} 
        # Learning Params
        self.alpha = 0.1 
        self.gamma = 0.95 
        self.epsilon = 0.2 
        
        # Actions: Adjustments [Increase, Maintain, Decrease]
        # Combined Action Space: 3x3 = 9 Actions
        # Action Index = m_adj * 3 + r_adj
        # 0: M+, R+ | 1: M+, R= | 2: M+, R-
        # 3: M=, R+ | ...
        self.adjustments = [0.1, 0.0, -0.1]
        
        self.last_state = None
        self.last_action_idx = None
        
        self.load_brain()
        
    def update(self, state):
        # AI runs weekly
        if state.day % 7 != 0:
            return

        # Initialize Globals if missing
        if 'policy_mating_strictness' not in state.globals:
            state.globals['policy_mating_strictness'] = 0.5 # Default balanced
        if 'policy_rationing_strictness' not in state.globals:
            state.globals['policy_rationing_strictness'] = 0.5

        # 1. Observe
        current_state = self._get_state_key(state)
        
        # 2. Learn
        if self.last_state is not None:
            reward = self._calculate_reward(state)
            self._learn(self.last_state, self.last_action_idx, reward, current_state)
            
        # 3. Act
        action_idx = self._choose_action(current_state)
        self._apply_policy(state, action_idx)
        
        # 4. Save Context
        self.last_state = current_state
        self.last_action_idx = action_idx
        
        if state.day % 30 == 0:
            self.save_brain()

    def _get_state_key(self, state):
        # State: (PopHealth, Resources, GeneticHealth)
        pop_count = len(state.population[state.population['is_alive']])
        if pop_count < 50: pop_s = "CRITICAL"
        elif pop_count < 200: pop_s = "LOW"
        else: pop_s = "HEALTHY"
        
        if 'genetic_vulnerability' in state.population.columns:
            avg_vul = state.population[state.population['is_alive']]['genetic_vulnerability'].mean()
        else:
            avg_vul = 0.0
        
        if avg_vul < 0.2: gen_s = "PURE"
        elif avg_vul < 0.5: gen_s = "MIXED"
        else: gen_s = "DEGENERATED"
        
        food_per_capita = state.globals['resources'] / max(1, pop_count)
        if food_per_capita < 5: res_s = "FAMINE"
        elif food_per_capita < 20: res_s = "SCARCE"
        else: res_s = "ABUNDANT"
        
        return (pop_s, gen_s, res_s)

    def _calculate_reward(self, state):
        pop_alive = len(state.population[state.population['is_alive']])
        reward = 1.0
        
        # Penalize Genetics
        if 'genetic_vulnerability' in state.population.columns:
            avg_vul = state.population[state.population['is_alive']]['genetic_vulnerability'].mean()
            if avg_vul > 0.5: reward -= 5.0
            elif avg_vul > 0.3: reward -= 1.0
                
        # Penalize Starvation Risk
        food_per_capita = state.globals['resources'] / max(1, pop_alive)
        if food_per_capita < 2: reward -= 2.0
            
        return reward

    def _choose_action(self, state_key):
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * 9 # 9 Actions
            
        if random.random() < self.epsilon:
            return random.randint(0, 8)
        else:
            max_q = max(self.q_table[state_key])
            best = [i for i, x in enumerate(self.q_table[state_key]) if x == max_q]
            return random.choice(best)

    def _apply_policy(self, state, action_idx):
        # Decode action [0-8]
        # m_idx = 0(Inc), 1(Same), 2(Dec)
        m_idx = action_idx // 3
        r_idx = action_idx % 3
        
        m_adj = self.adjustments[m_idx]
        r_adj = self.adjustments[r_idx]
        
        # Apply strictness
        curr_m = state.globals.get('policy_mating_strictness', 0.5)
        curr_r = state.globals.get('policy_rationing_strictness', 0.5)
        
        new_m = max(0.0, min(1.0, curr_m + m_adj))
        new_r = max(0.0, min(1.0, curr_r + r_adj))
        
        state.globals['policy_mating_strictness'] = new_m
        state.globals['policy_rationing_strictness'] = new_r

    def _learn(self, old_state, action, reward, new_state):
        if new_state not in self.q_table:
             self.q_table[new_state] = [0.0] * 9
             
        old_val = self.q_table[old_state][action]
        next_max = max(self.q_table[new_state])
        new_val = old_val + self.alpha * (reward + self.gamma * next_max - old_val)
        self.q_table[old_state][action] = new_val

    def save_brain(self):
        try:
            os.makedirs(os.path.dirname(self.brain_path), exist_ok=True)
            with open(self.brain_path, 'wb') as f:
                pickle.dump(self.q_table, f)
        except: pass

    def load_brain(self):
        if os.path.exists(self.brain_path):
            try:
                with open(self.brain_path, 'rb') as f:
                    loaded_q = pickle.load(f)
                    
                # Validate Logic: Check random key for shape
                if loaded_q:
                    first_key = next(iter(loaded_q))
                    if len(loaded_q[first_key]) == 9:
                        self.q_table = loaded_q
                    else:
                        print(f"[WARNING] Brain Incompatible (Size {len(loaded_q[first_key])} != 9). Resetting AI.")
                        self.q_table = {}
                else:
                    self.q_table = {}
            except Exception as e: 
                print(f"[WARNING] Failed to load brain: {e}")
                self.q_table = {}

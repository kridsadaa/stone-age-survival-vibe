import random
import pickle
import os

class QAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = {} # (state) -> [q_value_action_0, q_value_action_1, ...]
        self.alpha = alpha # Learning Rate
        self.gamma = gamma # Discount Factor
        self.epsilon = epsilon # Exploration Rate
        self.actions = [0, 1, 2] # 0: Gather, 1: Balance, 2: Heal
        
        self.last_state = None
        self.last_action = None
        
        self.load_brain()

    def get_state_key(self, season, resources, population, infected_count):
        # Discretize Resources
        if resources < population * 2: res_state = "CRITICAL"
        elif resources < population * 10: res_state = "LOW"
        elif resources < population * 20: res_state = "NORMAL"
        else: res_state = "ABUNDANT"
        
        # Discretize Health
        infection_rate = infected_count / max(1, population)
        health_state = "PLAGUE" if infection_rate > 0.1 else "HEALTHY"
        
        return (season, res_state, health_state)

    def choose_action(self, state):
        self.last_state = state
        
        # Initialize state if new
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)
            
        # Exploration
        if random.random() < self.epsilon:
            action = random.choice(self.actions)
        else:
            # Exploitation
            q_values = self.q_table[state]
            max_q = max(q_values)
            # breaking ties randomly
            best_actions = [i for i, q in enumerate(q_values) if q == max_q]
            action = random.choice(best_actions)
            
        self.last_action = action
        return action

    def learn(self, reward, new_state):
        if self.last_state is None or self.last_action is None:
            return
            
        # Initialize new state
        if new_state not in self.q_table:
            self.q_table[new_state] = [0.0] * len(self.actions)
            
        # Q-Learning Formula
        old_value = self.q_table[self.last_state][self.last_action]
        next_max = max(self.q_table[new_state])
        
        new_value = old_value + self.alpha * (reward + self.gamma * next_max - old_value)
        self.q_table[self.last_state][self.last_action] = new_value
        
    def save_brain(self, filename="tribal_brain.pkl"):
        try:
            with open(filename, "wb") as f:
                pickle.dump(self.q_table, f)
        except:
            pass # Handle perms issue

    def load_brain(self, filename="tribal_brain.pkl"):
        if os.path.exists(filename):
            try:
                with open(filename, "rb") as f:
                    self.q_table = pickle.load(f)
            except:
                pass

import json
import pandas as pd
import numpy as np
import uuid
import os
from typing import List, Dict

def load_diseases(filepath: str) -> List[Dict]:
    """Loads disease data from a JSON file."""
    if not os.path.exists(filepath):
        print(f"Warning: Disease file not found at {filepath}")
        return []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {filepath}")
        return []

def load_traits(filepath: str) -> pd.DataFrame:
    """Loads trait data from a CSV file."""
    if not os.path.exists(filepath):
        print(f"Warning: Trait file not found at {filepath}")
        return pd.DataFrame() # Return empty DF
        
    try:
        df = pd.read_csv(filepath)
        # Parse the survival_bonus column which is a string representation of a dict
        # We'll do it safely using json.loads if it's strictly valid JSON, or eval if it's python dict str.
        # Given the CSV format in the plan, it looks like valid JSON-ish or Python dict string.
        # Let's use json.loads but replace single quotes with double if necessary, or better, strictly expect valid JSON in CSV.
        # The input I wrote uses double quotes for keys, so it should be parseable as JSON if we are careful.
        # Actually, standard pandas doesn't auto-parse dict columns.
        import ast
        df['survival_bonus'] = df['survival_bonus'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else {})
        return df
    except Exception as e:
        print(f"Error loading traits CSV: {e}")
        return pd.DataFrame()

def generate_initial_state(count: int, traits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the initial population DataFrame.
    """
    ids = [f"HMN-{str(uuid.uuid4())[:8]}" for _ in range(count)]
    ages = np.random.randint(0, 60, size=count).astype(float)
    genders = np.random.choice(['Male', 'Female'], size=count)
    
    # Create DF
    df = pd.DataFrame({
        "id": ids,
        "age": ages,
        "gender": genders,
        "job": "Gatherer",
        "hp": 100.0,
        "max_hp": 100.0,
        "stamina": 100.0,
        "is_alive": True,
        "is_pregnant": False, 
        "pregnancy_days": 0,
        # partner_id Removed
        "family_id": [f"FAM-{str(uuid.uuid4())[:8]}" for _ in range(count)], 
        "cause_of_death": None,
        # Ocean Traits (0.0 - 1.0)
        "trait_openness": np.random.random(count),
        "trait_conscientiousness": np.random.random(count),
        "trait_extraversion": np.random.random(count),
        "trait_agreeableness": np.random.random(count),
        "trait_neuroticism": np.random.random(count),
        # Psychology State
        "happiness": 100.0,
        "rebellion": 0.0,
        "criminal_history": 0,
        "criminal_history": 0,
        # Phenotypes
        "skin_tone": np.random.random(count), # 0.0 (Light) to 1.0 (Dark)
        "libido": np.random.beta(2, 5, size=count), # Skewed slightly lower, but some high
        "attractiveness": np.random.normal(0.5, 0.15, size=count).clip(0, 1), # Bell curve
        # Phase 4: Tribal System & Spatial
        "tribe_id": np.random.choice(['Red_Tribe', 'Blue_Tribe', 'Green_Tribe'], size=count),
    })
    
    # Initialize Spatial Coordinates based on Tribe (Homelands)
    # Red: Top-Left (0-40, 0-40)
    # Blue: Top-Right (60-100, 0-40)
    # Green: Bottom (30-70, 60-100)
    
    def get_start_pos(tribe):
        if tribe == 'Red_Tribe':
            return np.random.uniform(0, 40), np.random.uniform(0, 40)
        elif tribe == 'Blue_Tribe':
            return np.random.uniform(60, 100), np.random.uniform(0, 40)
        elif tribe == 'Green_Tribe':
            return np.random.uniform(30, 70), np.random.uniform(60, 100)
        return 50.0, 50.0

    # Apply spatial init
    coords = [get_start_pos(t) for t in df['tribe_id']]
    df['x'] = [c[0] for c in coords]
    df['y'] = [c[1] for c in coords]
    df['settlement_id'] = None # Will be assigned by SettlementSystem
    
    # Heuristic Job Assignment
    # Elders -> Healers
    df.loc[df['age'] > 50, 'job'] = 'Healer' 
    
    return df

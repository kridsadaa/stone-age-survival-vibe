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
    """Loads trait data from a CSV file with validation."""
    # Check file existence
    if not os.path.exists(filepath):
        print(f"⚠️ [Loaders] Warning: Traits file not found at {filepath}, using defaults")
        return pd.DataFrame()  # Return empty DF
    
    try:
        df = pd.read_csv(filepath)
        
        # Validate schema
        required_columns = ['name', 'survival_bonus']
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Validate data
        if df.empty:
            print(f"⚠️ [Loaders] Warning: Trait file is empty at {filepath}")
            return pd.DataFrame()
        
        # Parse survival_bonus column safely
        import ast
        try:
            df['survival_bonus'] = df['survival_bonus'].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else {}
            )
        except (ValueError, SyntaxError) as e:
            print(f"⚠️ [Loaders] Warning: Failed to parse survival_bonus, using empty dict - {e}")
            df['survival_bonus'] = {}
        
        return df
        
    except pd.errors.EmptyDataError:
        print(f"❌ [Loaders] Error: Trait CSV is empty at {filepath}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ [Loaders] Error: Failed to parse traits CSV - {e}")
        return pd.DataFrame()

def generate_initial_state(count: int, traits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the initial population DataFrame with validation.
    """
    # Validate inputs
    if count <= 0:
        raise ValueError(f"Population count must be positive, got {count}")
    if count > 10000:
        print(f"⚠️ Warning: Large population ({count}) may cause performance issues")
    
    ids = [f"HMN-{str(uuid.uuid4())[:8]}" for _ in range(count)]
    ages = np.random.randint(0, 60, size=count).astype(float)
    genders = np.random.choice(['Male', 'Female'], size=count)
    
    # Create DF
    df = pd.DataFrame({
        "id": ids,
        "age": ages,
        "gender": genders,
        "job": "Gatherer",
        "role": "Gatherer", # Default role
        "hp": 100.0,
        "max_hp": 100.0,
        "stamina": 100.0,
        "prestige": 0.0,
        "injuries": "[]", # Default empty list (stringified for DF safety or simple string)
        "nutrients": "{'protein': 100, 'carbs': 100, 'vitamins': 100}", # Serialized dict
        "is_alive": True,
        "is_pregnant": False, 
        "pregnancy_days": 0,
        "family_id": [f"FAM-{str(uuid.uuid4())[:8]}" for _ in range(count)], 
        
        # Family Tree (Realism Phase 6)
        # Store strings/lists directly to avoid DataFrame recursion issues
        "parents": "[]", # Serialized list of IDs
        "children": "[]", # Serialized list of IDs
        "partner_id": None, # Current primary partner
        
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

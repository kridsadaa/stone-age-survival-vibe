import json
import pandas as pd
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

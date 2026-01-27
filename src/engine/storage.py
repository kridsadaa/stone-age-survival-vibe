import pandas as pd
import os
from typing import Dict, List, Optional

class ArchiveManager:
    """
    Manages the 'Cold Storage' for dead agents.
    Moves rows from the active RAM DataFrame to a persistent CSV/Parquet file.
    """
    def __init__(self, storage_dir="data/archive"):
        self.storage_dir = storage_dir
        self.graveyard_path = os.path.join(storage_dir, "graveyard.csv")
        self.lineage_path = os.path.join(storage_dir, "lineage_index.pkl") # Future use
        
        # Ensure dir exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize graveyard file if not exists
        if not os.path.exists(self.graveyard_path):
            # We don't write header yet because we don't know columns until first flush
            pass

    def archive_dead(self, population_df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes dead agents from population_df, appends them to disk, 
        and returns the cleaned DataFrame.
        """
        # Identify dead
        if 'is_alive' not in population_df.columns:
            return population_df
            
        dead_mask = population_df['is_alive'] == False
        dead_count = dead_mask.sum()
        
        if dead_count == 0:
            return population_df
            
        # Extract
        dead_rows = population_df[dead_mask].copy()
        
        # Append to Disk
        # We use mode='a' (append). Include header only if file is new.
        header = not os.path.exists(self.graveyard_path)
        
        try:
            dead_rows.to_csv(self.graveyard_path, mode='a', header=header, index=False)
            # print(f"Archived {dead_count} agents to {self.graveyard_path}")
        except Exception as e:
            print(f"❌ Archive Failed: {e}")
            # If fail, keep them in RAM to avoid data loss
            return population_df
            
        # Drop from RAM
        # Return only living
        # Reset index to keep it clean? Or preserve ID link?
        # Preserving original ID is key. Reset_index might mess up if logic relies on index.
        # But our logic mostly uses 'id' column, not index.
        # However, some systems might use index for fast lookup if we weren't careful.
        # Safer to drop by index and reset, assuming systems re-query indices.
        
        clean_df = population_df[~dead_mask].copy() 
        clean_df.reset_index(drop=True, inplace=True)
        
        return clean_df

    def get_graveyard_stats(self):
        if not os.path.exists(self.graveyard_path):
            return 0
        # Fast line count
        try:
            with open(self.graveyard_path) as f:
                return sum(1 for line in f) - 1 # Minus header
        except:
            return 0

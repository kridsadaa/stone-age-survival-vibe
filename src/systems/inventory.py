from src.engine.systems import System
import pandas as pd
import numpy as np

class InventorySystem(System):
    """
    Manages Item Storage, Spoilage, and Durability.
    """
    def update(self, state):
        self._handle_spoilage(state)
        self._cleanup_inventory(state)
        
    def _handle_spoilage(self, state):
        df = state.inventory
        if df.empty: return
        
        # 1. Decay Spoilage (Food)
        # perishable items have spoilage_rate > 0
        # Reduce amount by rate * current_amount (Exponential decay) or Linear?
        # Let's do Linear for simplicity: Amount -= Rate
        
        # Filter perishables
        perish_mask = df['spoilage_rate'] > 0
        
        if perish_mask.any():
            # Apply decay
            df.loc[perish_mask, 'amount'] -= df.loc[perish_mask, 'spoilage_rate']
            
            # Clamp to 0
            df.loc[perish_mask, 'amount'] = df.loc[perish_mask, 'amount'].clip(lower=0.0)
            
        # 2. Durability Check (Tools) happens on use (in EconomySystem),
        # but we can enforce max caps here if needed.
            
    def _cleanup_inventory(self, state):
        df = state.inventory
        if df.empty: return
        
        # Remove items with Amount <= 0
        # Remove items with Durability <= 0 (Broken tools)
        
        # Keep items that are useful
        valid_mask = (df['amount'] > 0.1) & ((df['max_durability'] == 0) | (df['durability'] > 0))
        
        # We need to drop rows where valid_mask is False
        # But pandas inplace drop is tricky in systems.
        # Re-assign
        state.inventory = df[valid_mask].copy()

    def add_item(self, state, agent_id, item, amount, sp_rate=0.0, dur=0, max_dur=0):
        """Helper to add/stack items"""
        df = state.inventory
        
        # Check if exists
        mask = (df['agent_id'] == agent_id) & (df['item'] == item)
        
        if mask.any():
            # Update existing
            # If stackable? Assume same item type stacks.
            # Weighted avg for spoilage? Too complex. Keep worst spoilage?
            # Just add amount.
            df.loc[mask, 'amount'] += amount
            
            # If it was a tool being added to a tool?
            # Usually tools don't stack if they have durability.
            # For simplicity: Tools don't stack if max_dur > 0.
            # But here we act as if they are commodities.
            # TODO: Separate logic for unstackables later.
        else:
            # Add new row
            new_row = {
                "agent_id": agent_id,
                "item": item,
                "amount": amount,
                "durability": dur,
                "max_durability": max_dur,
                "spoilage_rate": sp_rate
            }
            # Concat
            state.inventory = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

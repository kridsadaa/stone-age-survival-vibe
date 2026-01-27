from src.engine.systems import System
import random
import pandas as pd

class TribalSystem(System):
    """
    Manages Tribe Metadata and Inter-Tribal Relations.
    Tribes: Red_Tribe, Blue_Tribe, Green_Tribe
    """
    def update(self, state):
        # 1. Initialize Metadata if missing
        if not state.tribes:
            self._init_tribes(state)
            
        # 2. Assign Leaders (Headman) per Tribe
        # TODO
        
        # 3. Inter-Tribal Events (War/Trade)
        # TODO: Phase 4.2
        pass

    def _init_tribes(self, state):
        state.tribes = {
            'Red_Tribe': {'color': '#FF4B4B', 'relations': {'Blue_Tribe': 0, 'Green_Tribe': -10}, 'policy': 'Aggressive'},
            'Blue_Tribe': {'color': '#4B4BFF', 'relations': {'Red_Tribe': 0, 'Green_Tribe': 10}, 'policy': 'Peaceful'},
            'Green_Tribe': {'color': '#4BFF4B', 'relations': {'Red_Tribe': -10, 'Blue_Tribe': 10}, 'policy': 'Neutral'}
        }
        state.log("⚔️ TRIBES ESTABLISHED: Red, Blue, Green have claimed territories.")

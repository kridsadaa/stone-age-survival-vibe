import pandas as pd
from typing import Dict, List, Any
import time
import threading
from .systems import System
from .storage import ArchiveManager

class WorldState:
    """
    Central Data Retrieval Object (DRO).
    Holds all state for the simulation.
    """
    def __init__(self):
        self.day: int = 0
        
        # Core Data: Population as Vectorized DataFrame
        # Columns: id, age, gender, job, hp, stamina, is_alive, etc.
        self.population: pd.DataFrame = pd.DataFrame(columns=[
            "id", "family_id", "age", "gender", "job", 
            "hp", "max_hp", "stamina", 
            "is_pregnant", "pregnancy_days", # partner_id REMOVED
            "traits", "params", "infected_diseases", "immunities",
            "cause_of_death", "is_alive"
        ])
        
        # Kinship Graph (Many-to-Many)
        # Type: Spouse, Lover, Ex, Child, Parent
        self.relationships: pd.DataFrame = pd.DataFrame(columns=[
            "id_a", "id_b", "type", "commitment", "affection", "start_day"
        ])
        
        # Knowledge Graph (Skills)
        self.skills: pd.DataFrame = pd.DataFrame(columns=[
            "agent_id", "skill", "level"
        ])
        
        # Tribes Metadata
        self.tribes: Dict[str, Any] = {}
        
        # Global Resources & Config
        self.globals: Dict[str, Any] = {
            "resources": 1000.0,
            "season": "Spring",
            "inventory": {"Wood": 0, "Stone": 0},
            "idea_points": 0.0,
            "era": "Stone Age",
            # Climate Globals
            "latitude": 45.0, # Degrees (0-90)
            "elevation": 100.0, # Meters
            "temperature": 15.0, # Celsius
            "biome": "Temperate Forest",
            "is_night": False
        }
        
        # Sub-modules (Keep these as Objects for now, or migate later)
        self.map = None 
        self.tech_tree = None 
        
        # Logs
        self.chronicle: List[str] = []

    def log(self, message: str):
        self.chronicle.insert(0, f"Day {self.day}: {message}")
        if len(self.chronicle) > 1000: # Keep log manageable
            self.chronicle.pop()

    @property
    def current_season(self):
        day_of_year = self.day % 365
        if day_of_year < 90: return "Spring"
        elif day_of_year < 180: return "Summer"
        elif day_of_year < 270: return "Autumn"
        else: return "Winter"

class SimulationEngine:
    """
    Manages the verification loop and system execution.
    Supports running in a background thread.
    """
    def __init__(self):
        self.state = WorldState()
        self.systems: List[System] = []
        self.running = False
        self.paused = False
        self._thread = None
        self.tps_limit = 20 # Ticks Per Second Limit
        self.simulation_speed = 1.0 # Multiplier
        self.archiver = ArchiveManager()
        
    def add_system(self, system: System):
        self.systems.append(system)
        
    def tick(self, force=False):
        """Execute one simulation step"""
        if self.paused and not force:
            return

        self.state.day += 1
        
        # Update Globals (Season)
        self.state.globals["season"] = self.state.current_season
        
        # Run Systems
        for system in self.systems:
            system.update(self.state)
            
        # Optimization: Archive Dead
        if self.state.day % 30 == 0:
            self.state.population = self.archiver.archive_dead(self.state.population)
            
    def start(self):
        """Start background processing"""
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            
    def toggle_pause(self):
        self.paused = not self.paused

    def set_speed(self, speed: float):
        self.simulation_speed = speed

    def _loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            start_t = time.time()
            try:
                self.tick()
            except Exception as e:
                print(f"❌ SIMULATION CRASHED: {e}")
                import traceback
                traceback.print_exc()
                with open("crash.log", "w") as f:
                    f.write(f"Crash at Day {self.state.day}:\n")
                    f.write(traceback.format_exc())
                self.paused = True
                self.running = False
            elapsed = time.time() - start_t
            
            # FPS Limiter
            if self.simulation_speed > 0:
                target_wait = (1.0 / (self.tps_limit * self.simulation_speed))
                if elapsed < target_wait:
                    time.sleep(target_wait - elapsed)

import pandas as pd
from typing import Dict, List, Any
import time
import threading
from .systems import System
from .storage import ArchiveManager
from src.loaders import load_traits, generate_initial_state

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
            "id", "family_id", "age", "gender", "job", "role", # Added role
            "hp", "max_hp", "stamina", "prestige", # Added prestige
            "is_pregnant", "pregnancy_days", 
            "traits", "params", "infected_diseases", "immunities",
            "cause_of_death", "is_alive",
            "injuries", "nutrients", # Pre-add Phase 3 columns to save time
            "parents", "children", "partner_id" # Phase 6 Family Tree
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
        
        # Terrain Map (20x20 Grid)
        self.map_data: pd.DataFrame = None 
        
        # Phase 5: Inventory (Agent ID, Item, Amount, Durability, MaxDurability, Spoilage)
        self.inventory: pd.DataFrame = pd.DataFrame(columns=[
            "agent_id", "item", "amount", "durability", "max_durability", "spoilage_rate"
        ])
        
        # Global Resources & Config
        self.globals: Dict[str, Any] = {
            "resources": {"wood": 0, "stone": 0, "food": 0},
            "policies": {},
            "policy_mating": "Strict", # Strict, Open
            "policy_rationing": "Communal", # Communal, Meritocracy, ChildFirst
            "season": "Spring",
            "year": 1,
            "weather": "Sunny"
        }
        
        # Structured Logs (Realism Phase 6)
        # Structured Logs (Realism Phase 6)
        # Format: {'tick': int, 'message': str, 'agent_id': str | None, 'category': str}
        self.logs: List[Dict] = []
        
        # Sub-modules (Keep these as Objects for now, or migate later)
        self.map = None 
        self.tech_tree = None 
        
        # Logs
        self.chronicle: List[str] = []

    def log(self, message: str, agent_id: str = None, category: str = "General"):
        """
        Logs an event with metadata for UI filtering.
        """
        entry = {
            "tick": self.day,
            "message": message,
            "agent_id": agent_id,
            "category": category
        }
        self.logs.append(entry)
        
        # Keep log size manageable (Last 2000 entries)
        if len(self.logs) > 2000:
            self.logs.pop(0)
            
        # Chronicle (Text only)
        self.chronicle.insert(0, f"Day {self.day}: {message}")
        if len(self.chronicle) > 1000:
            self.chronicle.pop()
            
        print(f"[Day {self.day}] {message}") # Console echo
            
    def get_logs_for_agent(self, agent_id: str) -> List[Dict]:
        """Returns logs specific to an agent (by ID match or text mention)."""
        return [l for l in self.logs if l.get('agent_id') == agent_id or (agent_id and agent_id in l.get('message', ''))]

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
        
        # Thread safety: RLock allows same thread to acquire multiple times
        self._state_lock = threading.RLock()
        
    def add_system(self, system: System) -> None:
        self.systems.append(system)
        
    def tick(self, force: bool = False) -> None:
        """Execute one simulation step (thread-safe)"""
        with self._state_lock:
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
            
    def start(self) -> None:
        """Start background processing"""
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        
    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            
    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def set_speed(self, speed: float) -> None:
        self.simulation_speed = speed

    def reset(self):
        """Resets the simulation state to Day 0."""
        self.state.log("♻️ Auto-Restarting Simulation...")
        # Persist Settings
        restart_pref = self.state.globals.get('auto_restart', True)
        
        # New State
        self.state = WorldState()
        self.state.globals['auto_restart'] = restart_pref
        
        # Reload Data
        traits = load_traits('data/traits.csv')
        self.state.population = generate_initial_state(500, traits)
        
        # Note: Systems will see new state on next tick via self.state logic
        self.state.log("🌍 World Regenerated!")

    def _loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            start_t = time.time()
            try:
                self.tick()
                
                # Check Auto-Restart
                if self.state.globals.get('auto_restart', True):
                    # Check if population is critical (< 10)
                    alive_count = self.state.population['is_alive'].sum()
                    if alive_count < 10:
                        self.state.log(f"⚠️ Population Critical ({alive_count} < 10). Auto-Restarting...")
                        
                        # Save Report before wiping state
                        try:
                            from src.engine.reporter import save_simulation_report
                            save_simulation_report(self.state, getattr(self.state, 'ai', None), cause="Extinction (Pop < 10)")
                        except Exception as e:
                            print(f"Report Failed: {e}")

                        self.reset()
                        time.sleep(1.0) # Pause to let systems catch up
                        continue
                        
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

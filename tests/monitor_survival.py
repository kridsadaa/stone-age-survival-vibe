import time
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.disease import DiseaseSystem
from src.systems.climate import ClimateSystem
from src.systems.economy import EconomySystem
from src.loaders import generate_initial_state

def run_survival_test(days=730):
    print(f"\n--- Survival Monitor: {days} Days Challenge ---")
    
    engine = SimulationEngine()
    engine.add_system(BiologySystem())
    engine.add_system(EconomySystem()) # Critical for food
    engine.add_system(ClimateSystem())
    engine.add_system(DiseaseSystem())
    
    # Init Population
    start_pop = 500
    pop_df = generate_initial_state(start_pop, pd.DataFrame()) 
    engine.state.population = pop_df
    
    # Set starting resources to be reasonable
    engine.state.globals['resources'] = 5000.0 
    
    # Run
    engine.tps_limit = 10000 
    engine.simulation_speed = 0 
    
    # Stats Tracking
    history = []
    
    start_time = time.time()
    
    for _ in range(days):
        engine.tick()
        
        day = engine.state.day
        live_pop = len(engine.state.population[engine.state.population['is_alive']])
        season = engine.state.current_season
        temp = engine.state.globals.get('temperature', 0)
        food = engine.state.globals['resources']
        
        if day % 1 == 0:
            avg_stamina = engine.state.population[engine.state.population['is_alive']]['stamina'].mean()
            with open("daily.csv", "a") as f:
                f.write(f"{day},{live_pop},{food},{avg_stamina}\n")
            
        # Log every 30 days (Monthly)
        if day % 30 == 0:
            # Count recent events (approximation)
            # Stats
            pop_count = len(engine.state.population[engine.state.population['is_alive']])
            food = engine.state.globals['resources'] # Re-evaluate food at this point
            pregnant = len(engine.state.population[engine.state.population['is_pregnant'] & engine.state.population['is_alive']])
            
            avg_happy = 0
            if 'happiness' in engine.state.population.columns:
                avg_happy = engine.state.population[engine.state.population['is_alive']]['happiness'].mean()
            
            chief_id = engine.state.globals.get('chief_id', None)
            chief_age = "N/A"
            if chief_id:
                 crow = engine.state.population[engine.state.population['id'] == chief_id]
                 if not crow.empty:
                     chief_age = f"{crow.iloc[0]['age']:.1f}"
            
            print(f"Day {engine.state.day:03d} [{season} {temp:.1f}C]: Pop {pop_count} | Food {food:.0f} | HAPPY {avg_happy:.1f} | CHIEF {chief_id} (Age {chief_age})")
            
            history.append({
                "day": day, "pop": pop_count, "food": food, "season": season
            })
            
            if pop_count == 0:
                print("EXTINCTION EVENT DETECTED!")
                break
                
    elapsed = time.time() - start_time
    print(f"\n--- Result after {days} days ({elapsed:.2f}s real-time) ---")
    
    final_pop = len(engine.state.population[engine.state.population['is_alive']])
    # Write results to file
    with open("results.txt", "w", encoding='utf-8') as f:
        if final_pop > 0:
            children = len(engine.state.population[(engine.state.population['age'] < 10) & (engine.state.population['is_alive'])])
            f.write(f"SURVIVED! Final Population: {final_pop}\n")
            f.write(f"Children (<10y): {children}\n")
        else:
            f.write("FAILED: The tribe has perished.\n")
            
        dead_df = engine.state.population[engine.state.population['is_alive'] == False]
        if not dead_df.empty:
            f.write("\nCauses of Death:\n")
            f.write(dead_df['cause_of_death'].value_counts().to_string())

if __name__ == "__main__":
    run_survival_test(1000)


import os
import datetime
import pandas as pd
from collections import Counter

def save_simulation_report(state, ai=None, cause="Manual Reset"):
    """
    Saves a text summary of the simulation to 'simulation_logs/'
    """
    # 1. Prepare Directory
    log_dir = "simulation_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{log_dir}/summary_{timestamp}.txt"
    
    # 2. Gather Stats
    days = state.day
    pop_current = len(state.population[state.population['is_alive']])
    pop_total_spawned = len(state.population)
    deaths = pop_total_spawned - pop_current
    
    # Cause of death stats
    death_counts = Counter()
    dead_df = state.population[~state.population['is_alive']]
    if not dead_df.empty and 'cause_of_death' in dead_df.columns:
        death_counts.update(dead_df['cause_of_death'].dropna())
        
    # Tribe Stats
    tribe_summary = "--- Tribal Governance ---\n"
    if hasattr(state, 'tribes') and state.tribes:
        for tid, tdata in state.tribes.items():
            leader_id = tdata.get('chief_id', 'None')
            if 'tribe_id' in state.population.columns:
                 pop_count = len(state.population[(state.population['tribe_id'] == tid) & (state.population['is_alive'])])
            else:
                 pop_count = "?"
            policies = tdata.get('policies', {})
            
            tribe_summary += f"[{tid}]\n"
            tribe_summary += f"  Leader: {leader_id}\n"
            tribe_summary += f"  Population: {pop_count}\n"
            tribe_summary += f"  Policies: {policies}\n"
            tribe_summary += "\n"
    else:
        tribe_summary += "No tribal structures defined.\n"

    # AI Stats (Legacy Support)
    ai_summary = ""
    if ai:
        ai_summary = f"""--- AI Brain (Q-Learning) ---
    Epsilon (Exploration): {ai.epsilon:.2f}
    Knowledge Base: {len(ai.q_table)} States
    Last Action: {ai.last_action}
        """
        
    # World Stats (Resources)
    try:
        avg_wood = state.inventory[state.inventory['item'] == 'Wood']['amount'].mean()
    except:
        avg_wood = 0
        
    # 3. Write Report
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== Stone Age Survival World Report ===\n")
            f.write(f"ID: {timestamp}\n")
            f.write(f"Reset Cause: {cause}\n")
            f.write(f"Duration: {days} Days\n\n")
            
            f.write(f"--- Population Statistics ---\n")
            f.write(f"Final Living Population: {pop_current}\n")
            f.write(f"Total Agents Existed: {pop_total_spawned}\n")
            f.write(f"Total Deaths: {deaths}\n\n")
            
            if deaths > 0:
                f.write(f"--- Causes of Death ---\n")
                for c, count in death_counts.most_common():
                    f.write(f"  - {c}: {count}\n")
            f.write("\n")
            
            f.write(tribe_summary)
            f.write(ai_summary)
            f.write("\n")
            f.write(f"--- End of Report ---\n")
            
        print(f"📄 Report saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return None

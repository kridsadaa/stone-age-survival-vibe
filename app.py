import streamlit as st
import pandas as pd
from src.simulation import World
import time

st.set_page_config(page_title="Stone Age Survival", layout="wide")

st.title("🗿 Stone Age Survival Simulation")

# Initialize Session State
if 'world' not in st.session_state:
    st.session_state.world = World()
    st.session_state.auto_play = False

def advance_day():
    st.session_state.world.tick()

# Sidebar Controls
with st.sidebar:
    st.header("Controls")
    if st.button("Advance 1 Day"):
        advance_day()
    
    # Auto-play logic is tricky in Streamlit without reruns. 
    # We can use a simple toggle to "simulate X days" instantly or just manual steps.
    # For a true "Animation", we'd typically use st.empty() loop.
    
    days_to_sim = st.number_input("Fast Forward Days", min_value=1, max_value=100, value=1)
    if st.button("Simulate Batch"):
        progress_bar = st.progress(0)
        for i in range(days_to_sim):
            advance_day()
            progress_bar.progress((i + 1) / days_to_sim)
        st.success(f"Simulated {days_to_sim} days.")

    st.markdown("### Debug Stats")
    st.write(f"Total Resources: {st.session_state.world.resources}")

# Main Dashboard
world = st.session_state.world
living_pop = [p for p in world.population if p.is_alive]
dead_pop = [p for p in world.population if not p.is_alive]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Day", world.day)
col2.metric("Alive Population", len(living_pop), delta=f"{len(living_pop) - 50} from start" if world.day > 0 else 0)
col3.metric("Dead Population", len(dead_pop))
col4.metric("Infected Count", sum(1 for p in living_pop if p.infected_diseases))

# Detailed Views
tab1, tab2, tab3 = st.tabs(["Village Status", "The Chronicle", "Data Export"])

with tab1:
    st.subheader("Population Demographics")
    if living_pop:
        # Create DataFrame for display
        data = []
        for p in living_pop:
            data.append({
                "ID": p.id,
                "Age": p.age,
                "Gender": p.gender,
                "HP": p.current_hp,
                "Stamina": p.stamina,
                "Traits": ", ".join([t['name'] for t in p.traits]),
                "Infected": ", ".join(p.infected_diseases)
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Simple Charts
        st.bar_chart(df['Age'].value_counts())
    else:
        st.warning("The tribe has been wiped out.")

with tab2:
    st.subheader("Event Log")
    for log in world.chronicle:
        if "died" in log:
            st.error(log)
        elif "born" in log:
            st.success(log)
        elif "OUTBREAK" in log:
            st.warning(log)
        else:
            st.text(log)

with tab3:
    st.subheader("Export Data")
    if st.button("Generate CSV Snapshot"):
        # Full export including dead
        all_data = []
        for p in world.population:
            all_data.append({
                "ID": p.id,
                "Status": "Alive" if p.is_alive else "Dead",
                "Cause of Death": p.cause_of_death,
                "Age": p.age,
                "Gender": p.gender,
                "HP": p.current_hp,
                "Traits": [t['name'] for t in p.traits]
            })
        export_df = pd.DataFrame(all_data)
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Population CSV",
            data=csv,
            file_name=f"stone_age_pop_day_{world.day}.csv",
            mime="text/csv",
        )

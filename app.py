import streamlit as st
import pandas as pd
import time
import altair as alt
from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.disease import DiseaseSystem
from src.systems.climate import ClimateSystem
from src.loaders import load_traits, generate_initial_state

st.set_page_config(page_title="Stone Age Survival 2.0", layout="wide")

# --- Initialization ---
if 'engine' not in st.session_state:
    # Bootstrap Engine
    engine = SimulationEngine()
    
    # Add Systems
    engine.add_system(BiologySystem())
    engine.add_system(DiseaseSystem())
    engine.add_system(ClimateSystem())
    
    # Load Data
    traits = load_traits('data/traits.csv')
    
    # Spawn Population (Start big!)
    init_pop = 500
    pop_df = generate_initial_state(init_pop, traits)
    engine.state.population = pop_df
    
    # Start Thread
    engine.start()
    st.session_state.engine = engine

engine = st.session_state.engine
state = engine.state

# --- Sidebar ---
with st.sidebar:
    st.header("🎮 Controls")
    
    # Speed Control
    speed = st.slider("Simulation Speed", 0.1, 5.0, 1.0, help="Multiplier for Ticks Per Second")
    engine.set_speed(speed)
    
    # Pause/Resume
    btn_label = "▶️ Resume" if engine.paused else "⏸️ Pause"
    if st.button(btn_label):
        engine.toggle_pause()
        st.rerun()

    st.markdown("---")
    st.metric("TPS Limit", engine.tps_limit)
    
    if st.button("Reset Simulation"):
        engine.stop()
        del st.session_state.engine
        st.rerun()

    st.markdown("---")
    st.header("🌍 World Gen")
    new_lat = st.number_input("Latitude", -90.0, 90.0, state.globals.get('latitude', 45.0))
    new_elev = st.number_input("Elevation (m)", 0.0, 8000.0, state.globals.get('elevation', 100.0))
    
    if new_lat != state.globals.get('latitude', 45.0) or new_elev != state.globals.get('elevation', 100.0):
        state.globals['latitude'] = new_lat
        state.globals['elevation'] = new_elev
        st.success("Geography Updated!")
        
# --- Main UI ---
st.title(f"🗿 Stone Age Survival: Generative World (Day {state.day})")

# Top Metrics
living_df = state.population[state.population['is_alive']]
dead_count = len(state.population) - len(living_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Population", len(living_df), delta=f"-{dead_count} Dead")
col2.metric("Season", state.current_season, delta=f"{state.globals.get('temperature', 0):.1f}°C")
col3.metric("Food", f"{state.globals['resources']:.0f}", delta=f"Biome: {state.globals.get('biome', 'Unknown')}")

# Disease Stats
active_infections = 0
if hasattr(state, 'infections') and not state.infections.empty:
    active_infections = len(state.infections)
col4.metric("Infected", active_infections, delta="Active Cases")

# --- Tabs ---
tab_overview, tab_health, tab_raw = st.tabs(["Overview", "Health & Diseases", "Data Inspector"])

with tab_overview:
    # Charts (Sampled for performance)
    if len(living_df) > 0:
        st.subheader("Demographics")
        
        # Age Distribution
        chart_data = living_df[['age', 'gender']].copy()
        chart_data['age_group'] = (chart_data['age'] // 10) * 10
        
        c = alt.Chart(chart_data).mark_bar().encode(
            x='age_group:O',
            y='count()',
            color='gender'
        )
        st.altair_chart(c, use_container_width=True)
        
        # Job Distribution
        st.caption("Job Roles")
        job_counts = living_df['job'].value_counts()
        st.bar_chart(job_counts)

with tab_health:
    st.subheader("☣️ Disease Control Center")
    
    # Show active diseases
    disease_sys = next((s for s in engine.systems if isinstance(s, DiseaseSystem)), None)
    
    if disease_sys and disease_sys.known_diseases:
        st.markdown("### Known Pathogens")
        for d_id, disease in disease_sys.known_diseases.items():
            with st.expander(f"{disease.name} (R0: {disease.transmission:.2f})"):
                st.write(f"**Lethality:** {disease.lethality:.2%}")
                st.write(f"**Duration:** {disease.duration} Days")
                st.write(f"**Symptoms:** {disease.effects}")
    else:
        st.info("No diseases discovered yet.")

with tab_raw:
    st.subheader("Population DataFrame")
    st.dataframe(living_df.head(100)) # Show top 100 only

# --- Auto Refresh ---
# Simple Poll Mechanism
if not engine.paused:
    time.sleep(0.5) # Refresh every 500ms
    st.rerun()

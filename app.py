import streamlit as st
import pandas as pd
import time
import altair as alt
from src.engine.core import SimulationEngine
from src.systems.biology import BiologySystem
from src.systems.disease import DiseaseSystem
from src.systems.climate import ClimateSystem
from src.systems.economy import EconomySystem
from src.systems.genetics import GeneticsSystem
from src.systems.culture import CultureSystem
from src.systems.psychology import PsychologySystem
from src.systems.social import SocialSystem
from src.systems.politics import PoliticalSystem
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
    engine.add_system(EconomySystem())
    engine.add_system(GeneticsSystem())
    engine.add_system(GeneticsSystem())
    engine.add_system(CultureSystem())
    engine.add_system(PsychologySystem())
    engine.add_system(SocialSystem())
    engine.add_system(PoliticalSystem())
    
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
    st.header("⏩ Time Warp")
    skip_days = st.number_input("Days to Skip", min_value=1, max_value=3650, value=30, step=10)
    if st.button(f"Jump {skip_days} Days"):
        with st.spinner(f"Warping {skip_days} days..."):
            progress_bar = st.progress(0)
            # Temporarily pause thread to avoid race conditions
            was_paused = engine.paused
            engine.paused = True
            
            # Manual Loop
            for i in range(skip_days):
                engine.tick(force=True)
                if i % 10 == 0:
                    progress_bar.progress((i + 1) / skip_days)
            
            progress_bar.progress(1.0)
            # Restore state
            engine.paused = was_paused
            st.success(f"Warped {skip_days} days!")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.metric("TPS Limit", engine.tps_limit)
    
    if st.button("Reset Simulation"):
        engine.stop()
        del st.session_state.engine
        st.rerun()

    st.markdown("---")
    # Health Check
    if engine._thread is None or not engine._thread.is_alive():
        st.error("🚨 Simulation Thread Died!")
        if st.button("Restart Thread"):
             engine.start()
    elif engine.paused:
        st.warning("⏸️ Simulation Paused")
    else:
        st.success("▶️ Simulation Running")

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
tab_overview, tab_health, tab_genetics, tab_psych, tab_spirit, tab_raw = st.tabs(["Overview", "Health", "Genetics", "Psychology", "Tribal Spirit", "Data Inspector"])

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
    
    # Disease Metrics
    active_mask = (state.infections['active'] == True) if hasattr(state, 'infections') and not state.infections.empty else []
    latent_mask = (state.infections['active'] == False) if hasattr(state, 'infections') and not state.infections.empty else []
    
    active_count = sum(active_mask) if len(active_mask) > 0 else 0
    latent_count = sum(latent_mask) if len(latent_mask) > 0 else 0
    
    h1, h2 = st.columns(2)
    h1.metric("Active Infections", active_count, delta="Contagious")
    h2.metric("Latent/Dormant", latent_count, delta="Hidden Carriers")

    # Show active diseases
    disease_sys = next((s for s in engine.systems if isinstance(s, DiseaseSystem)), None)
    
    if disease_sys and disease_sys.known_diseases:
        st.markdown("### Known Pathogens")
        for d_id, disease in list(disease_sys.known_diseases.items()):
            with st.expander(f"{disease.name} ({disease.immunity_type})"):
                st.write(f"**Lethality:** {disease.lethality:.2%}")
                st.write(f"**Transmission:** {disease.transmission:.2f}")
                st.write(f"**Chronic:** {'Yes' if disease.is_chronic else 'No'}")
                st.write(f"**Symptoms:** {disease.effects}")
    else:
        st.info("No diseases discovered yet.")

with tab_genetics:
    st.subheader("🧬 Genetics & Evolution")
    
    if 'genetic_vulnerability' in living_df.columns:
        avg_vul = living_df['genetic_vulnerability'].mean()
        high_risk_count = len(living_df[living_df['genetic_vulnerability'] > 0.7])
        
        g1, g2 = st.columns(2)
        g1.metric("Avg Genetic Vulnerability", f"{avg_vul:.3f}", help="0.0 = Diverse, 1.0 = Clone")
        g2.metric("High Risk (Inbred)", high_risk_count, delta="Vulnerable Agents")
        
        st.markdown("#### Vulnerability Distribution")
        # Histogram
        st.bar_chart(living_df['genetic_vulnerability'])
        
    st.info("Genetic Vulnerability increases with inbreeding (parents with similar genomes). High vulnerability leads to weaker immunity.")

with tab_psych:
    st.subheader("🧠 Tribal Psychology")
    
    if 'happiness' in living_df.columns:
        avg_happy = living_df['happiness'].mean()
        rebels = len(living_df[living_df['rebellion'] > 0.5])
        criminals = len(living_df[living_df['criminal_history'] > 0])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("😊 Avg Happiness", f"{avg_happy:.1f}", help="Below 50 is bad. Below 20 is RIOT.")
        c2.metric("😠 Rebels", rebels, delta="Dissidents", delta_color="inverse")
        c3.metric("👮 Criminals", criminals, delta="Thieves")
        
        st.markdown("#### Mind State")
        st.bar_chart(living_df[['happiness', 'rebellion']].head(50))
        
        # Ocean Distribution
        st.markdown("#### Personality Types (OCEAN)")
        st.scatter_chart(living_df, x='trait_openness', y='trait_conscientiousness', color='job')

with tab_spirit:
    st.subheader("👻 The Spirit of the Tribe (AI)")
    
    # Chief Profile
    chief_id = state.globals.get('chief_id')
    if chief_id:
        chief_row = living_df[living_df['id'] == chief_id]
        if not chief_row.empty:
            c = chief_row.iloc[0]
            st.success(f"👑 **Chief {c['id']}**\n\nAge: **{c['age']:.1f}**")
            cols = st.columns(3)
            cols[0].write(f"Wisdom (C): {c['trait_conscientiousness']:.2f}")
            cols[1].write(f"Kindness (A): {c['trait_agreeableness']:.2f}")
            cols[2].write(f"Chaos (N): {c['trait_neuroticism']:.2f}")
    else:
        st.warning("No Chief elected yet!")
        
    culture_sys = next((s for s in engine.systems if isinstance(s, CultureSystem)), None)
    if culture_sys:
        # Current Policies
        # Current Policies (Dynamic Sliders)
        st.markdown("### ⚖️ Tribal Laws (AI Controlled)")
        
        # Mating Strictness
        m_strict = state.globals.get('policy_mating_strictness', 0.5)
        m_label = "Free Love"
        if m_strict > 0.8: m_label = "🧬 Eugenics (Strict)"
        elif m_strict > 0.4: m_label = "🚫 Incest Ban (No Siblings)"
        else: m_label = "❤️ Free Love (Risk High)"
        
        st.write(f"**Mating Law:** {m_label}")
        st.progress(m_strict)
        
        # Rationing Strictness
        r_strict = state.globals.get('policy_rationing_strictness', 0.5)
        r_label = "Communism"
        if r_strict > 0.6: r_label = "🛡️ Women & Children First"
        elif r_strict > 0.3: r_label = "⚒️ Workers First"
        else: r_label = "🍞 Shared Equally"
        
        st.write(f"**Rationing Law:** {r_label}")
        st.progress(r_strict)
        
        st.markdown("---")
        st.markdown("### Brain Activity")
        if culture_sys.last_state:
            st.write(f"**Observed State:** {culture_sys.last_state}")
            st.write(f"**Last Reward:** {culture_sys._calculate_reward(state):.2f}")
        
        # Q-Table Visualization
        if culture_sys.q_table:
            st.text(f"Brain Knowledge Size: {len(culture_sys.q_table)} States")
            # Convert Q-Table to DataFrame for view
            # Flatten dict: State -> Action Values
            q_data = []
            for k, v in list(culture_sys.q_table.items())[:10]: # Show top 10
                row = {"State": str(k), "Values": str([f"{x:.1f}" for x in v])}
                q_data.append(row)
            st.table(q_data)
    else:
        st.error("Spirit AI not found.")

with tab_raw:
    st.subheader("Population DataFrame")
    st.dataframe(living_df.head(100)) # Show top 100 only

# --- Auto Refresh ---
# Simple Poll Mechanism
if not engine.paused:
    time.sleep(0.5) # Refresh every 500ms
    st.rerun()

import streamlit as st
import time
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
from src.systems.tech import TechSystem
from src.systems.tribe import TribalSystem
from src.systems.knowledge import KnowledgeSystem
from src.systems.settlement import SettlementSystem
from src.systems.map import MapSystem
from src.systems.trade import TradeSystem
from src.loaders import load_traits, generate_initial_state

# Import UI Components
from src.ui.sidebar import render_sidebar
from src.ui.dashboard import render_dashboard
from src.ui.tabs.overview import render_overview
from src.ui.tabs.health import render_health
from src.ui.tabs.genetics import render_genetics
from src.ui.tabs.psychology import render_psychology
from src.ui.tabs.social import render_social
from src.ui.tabs.civilization import render_civilization
from src.ui.tabs.inspector import render_inspector
from src.ui.tabs.economy import render_economy
from src.ui.tabs.governance import render_governance

st.set_page_config(page_title="Stone Age Survival 2.0", layout="wide")

# --- Engine Initialization ---
if 'engine' not in st.session_state:
    # Bootstrap Engine
    engine = SimulationEngine()
    
    # Systems Registration
    # Dependency Order: Map -> Climate -> Biology -> Economy -> Social
    from src.systems.map import MapSystem
    engine.add_system(MapSystem()) # Move Map to first
    
    engine.add_system(BiologySystem())
    engine.add_system(DiseaseSystem())
    engine.add_system(ClimateSystem())
    engine.add_system(EconomySystem())
    engine.add_system(GeneticsSystem())
    engine.add_system(CultureSystem())
    engine.add_system(PsychologySystem())
    engine.add_system(SocialSystem())
    engine.add_system(PoliticalSystem())
    # Phase 4 Systems
    engine.add_system(TechSystem())
    engine.add_system(TribalSystem())
    engine.add_system(KnowledgeSystem())
    engine.add_system(SettlementSystem())
    # engine.add_system(MapSystem()) # Moved up
    engine.add_system(TradeSystem())
    
    # Phase 5 Systems
    from src.systems.inventory import InventorySystem
    engine.add_system(InventorySystem())
    
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

# --- Render UI Components ---
render_sidebar(engine)
render_dashboard(state)

# Filter Data for View
living_df = state.population[state.population['is_alive']]

# Tabs Layout
tab_names = [
    "Overview", 
    "Governance",
    "Economy",
    "Health", 
    "Genetics", 
    "Psychology", 
    "Social Structure", 
    "Civilization", 
    "Data Inspector"
]
tabs = st.tabs(tab_names)

# Render Tab Contents
with tabs[0]: render_overview(living_df)
with tabs[1]: render_governance(state)
with tabs[2]: 
    # Check signature for economy, some use just state
    if 'living_df' in render_economy.__code__.co_varnames:
        render_economy(state, living_df)
    else:
        render_economy(state)

with tabs[3]: render_health(state, engine)
with tabs[4]: render_genetics(living_df)
with tabs[5]: render_psychology(living_df)
with tabs[6]: render_social(state, living_df)
with tabs[7]: render_civilization(state, living_df)
with tabs[8]: render_inspector(living_df)

# --- Auto Refresh Disabled ---
# User requested manual refresh
# if not engine.paused:
#     time.sleep(0.5) 
#     st.rerun()

import streamlit as st

def render_dashboard(state):
    st.title(f"🗿 Stone Age Survival: Generative World (Day {state.day})")
    
    # Top Row Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    
    living_mask = state.population['is_alive']
    population = len(state.population[living_mask])
    
    year = state.globals.get('year', 1)
    season = state.globals.get('season', 'Spring')
    weather = state.globals.get('weather', 'Sunny')
    
    # Icons
    w_icon = {'Sunny': '☀️', 'Rain': '🌧️', 'Storm': '⛈️'}.get(weather, '❓')
    
    c1.metric("Population", f"{population}")
    c2.metric("Year", f"{year}")
    c3.metric("Season", f"{season}")
    c4.metric("Weather", f"{w_icon} {weather}")
    c5.metric("Day", f"{state.day}")
    
    st.divider()

    # Infection Stats (if any)
    if hasattr(state, 'infections') and not state.infections.empty:
        st.warning(f"☣️ Active Infections: {len(state.infections)}")

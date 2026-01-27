import streamlit as st

def render_dashboard(state):
    st.title(f"🗿 Stone Age Survival: Generative World (Day {state.day})")
    
    # Top Metrics
    living_df = state.population[state.population['is_alive']]
    dead_count = len(state.population) - len(living_df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Population", len(living_df), delta=f"-{dead_count} Dead")
    col2.metric("Season", state.current_season, delta=f"{state.globals.get('temperature', 0):.1f}°C")
    col3.metric("Food", f"{state.globals['resources']:.0f}", delta=f"Biome: {state.globals.get('biome', 'Unknown')}")
    
    weather_desc = f"{state.globals.get('precipitation', 'Clear')}"
    if state.globals.get('wind_speed', 0) > 40: weather_desc += " 🌪️"
    
    col4.metric("Weather", weather_desc, delta=f"Hum: {state.globals.get('humidity', 0):.0%} | Wind: {state.globals.get('wind_speed', 0):.0f}km/h")
    col5.metric("UV Index", f"{state.globals.get('uv_index', 0):.1f}", delta="Risk Level")
    
    # Disease Stats override (using col4 again or maybe separate?)
    # Original app reused col4 for "Infected". Let's put it in dashboard but maybe as a new row or sub-metric if needed.
    # Actually original code overwrote col4 variable with new metric call? No, Streamlit renders immediately.
    # Ah, the original code had:
    # col4.metric("Infected"... 
    # Wait, col4 was used for Weather, then reused for Infected? 
    # "col4.metric("Infected", active_infections, delta="Active Cases")" appears AFTER weather.
    # This implies it stacked it or overwrote it? Streamlit columns are containers.
    # It appends to the column. So Col4 has 2 metrics.
    
    active_infections = 0
    if hasattr(state, 'infections') and not state.infections.empty:
        active_infections = len(state.infections)
    col4.metric("Infected", active_infections, delta="Active Cases")

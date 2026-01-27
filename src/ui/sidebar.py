import streamlit as st
import time

def render_sidebar(engine):
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
        state = engine.state
        new_lat = st.number_input("Latitude", -90.0, 90.0, state.globals.get('latitude', 45.0))
        new_elev = st.number_input("Elevation (m)", 0.0, 8000.0, state.globals.get('elevation', 100.0))
        
        if new_lat != state.globals.get('latitude', 45.0) or new_elev != state.globals.get('elevation', 100.0):
            state.globals['latitude'] = new_lat
            state.globals['elevation'] = new_elev
            st.success("Geography Updated!")

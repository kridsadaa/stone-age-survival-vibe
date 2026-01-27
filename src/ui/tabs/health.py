import streamlit as st
from src.systems.disease import DiseaseSystem

def render_health(state, engine):
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

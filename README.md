# Stone Age Survival Simulation 🗿

A dynamic agent-based simulation where a Stone Age tribe struggles to survive against hunger, disease, and the elements. Built with Python and Streamlit.

## Features

- **Agent-Based Modeling**: Each "Human" agent has unique genetics, physical attributes (HP, Stamina), and personality traits.
- **Dynamic Disease System**: Diseases spread through the population based on transmission rates, symptoms, and incubation periods.
- **Resource Management**: The tribe must gather enough food to survive. Scarcity leads to starvation, affecting the weakest first.
- **Data-Driven Architecture**:
    - `data/diseases.json`: easy-to-edit disease definitions.
    - `data/traits.csv`: defining genetic traits and survival bonuses.
- **Interactive Dashboard**:
    - Real-time village status (Population, Infected, Resources).
    - Event Chronicle (Births, Deaths, Outbreaks).
    - Data Export (CSV).

## Logic Overview

The simulation runs in "Days". Each day (`tick()`):
1.  **Gathering**: Agents contribute to the community food store based on their traits (e.g., "Sharp Eyes").
2.  **Consumption**: Agents eat. If food is insufficient, they take damage.
3.  **Disease Spread**:
    - Random "Spontaneous Outbreaks" based on population density.
    - Infected agents spread disease to contacts based on transmission rates.
4.  **Life Cycle**: Agents age, take damage from diseases/starvation, and can die.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install streamlit pandas
    ```
3.  Run the application:
    ```bash
    streamlit run app.py
    ```

## File Structure

- `app.py`: Main Streamlit dashboard application.
- `src/`:
    - `models.py`: Defines the `Human` agent class.
    - `simulation.py`: The `World` engine logic.
    - `loaders.py`: Helper functions for loading data.
- `data/`:
    - `diseases.json`: Database of diseases.
    - `traits.csv`: Database of agent traits.

## Future Plans

- Add "Events" system (e.g., Volcanic Eruption, Drought).
- More complex reproduction and inheritance logic.
- Clan politics and social interactions.

---
*Created by Antigravity*
# Stone Age Survival Vibe 2.0 🗿🏹

An advanced **Agent-Based Simulation** of a Neolithic society, where agents live, love, gossip, trade, and try to survive in a dynamic ecosystem. Built with **Python (Pandas)** and **Streamlit**.

## 🌟 Key Features

### 🏛️ Tribal Society
The world is no longer a single group. Agents belong to distinct tribes, each with its own culture and politics:
- **Red Tribe 🔴**: Aggressive warriors.
- **Blue Tribe 🔵**: Peaceful diplomats.
- **Green Tribe 🟢**: Neutral naturists.
- **Politics**: Tribes elect **Chiefs** based on Prestige. Chiefs set policies (e.g., *Strict Mating* vs *Open Love*, *Communal Rationing* vs *Meritocracy*).

### 💕 Complex Social Dynamics
Agents are not just resource consumers; they have feelings:
- **Romance System**: Agents have a "Love Drive" prompting them to seek partners.
- **Gossip Network**: Agents share opinions (Positive/Negative) about others, influencing global Reputation.
- **Family Trees**: Tracking lineage, parents, and children.

### 📊 Advanced Simulation Engine
- **Vectorized Logic**: Powered by `pandas` for handling populations of 500+ agents efficiently.
- **Economics**: Agents gather resources, craft tools (Spears, Baskets), and **Trade** surpluses with neighbors.
- **Desire-Driven Movement**: Agents move with purpose—towards food when hungry, towards lovers when lonely.

### 🛠️ Tools & Analytics
- **Inspector Tab**: Click on any agent to see their full profile: Attributes, Relationships, History Log, and Family Tree.
- **Auto-Reporter**: Automatically saves a detailed text summary (`simulation_logs/`) every time the world restarts (Extinction) or is manually reset.
- **Data Export**: Download current world state as CSV.

---

## 🚀 Installation & Run

1.  **Clone the Repository**
2.  **Install Dependencies**:
    ```bash
    pip install streamlit pandas numpy
    ```
3.  **Run the App**:
    ```bash
    streamlit run app.py
    ```
4.  **Explore**: Use the Tabs to view different aspects of the simulation (Governance, Social, Health, etc.).

---

## 📂 Project Structure

- **`app.py`**: Main entry point and UI layout.
- **`src/`**:
    - **`engine/`**: Core Simulation Loop & World State (`core.py`, `reporter.py`).
    - **`systems/`**: Logic modules for each aspect of life:
        - `tribe.py`: Tribal politics & Chiefs.
        - `social.py`: Gossip & Reputation.
        - `biology.py`: Health, Pregnancy, Genetics.
        - `settlement.py`: Movement & Migration.
        - `economy.py`: Gathering, Crafting, Trade.
    - **`ui/`**: Streamlit renderers (`inspector.py`, `sidebar.py`, etc.).
- **`data/`**:
    - `traits.csv`: Genetic traits definitions.
    - `diseases.json`: Disease configuration.
- **`simulation_logs/`**: Auto-generated simulation summaries.

---

## 📝 Configuration

You can tweak the simulation via the **Sidebar**:
- **Simulation Speed**: Adjust ticks per second.
- **Time Warp**: Skip ahead 10-100 days.
- **Auto-Restart**: Automatically reboot the world if population drops below 10.

---
*Developed by Antigravity*
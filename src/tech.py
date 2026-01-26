from typing import List, Dict, Optional

class Technology:
    def __init__(self, key: str, name: str, cost: float, description: str, requirements: List[str] = None):
        self.key = key
        self.name = name
        self.cost = cost
        self.description = description
        self.requirements = requirements if requirements else []
        self.unlocked = False

class TechTree:
    def __init__(self):
        # Define the Tech Tree
        self.techs: Dict[str, Technology] = {}
        
        # 1. Primitive Tools
        self.add_tech("primitive_tools", "Primitive Tools", 500, 
                      "Use sharp stones and sticks. Unlocks gathering of Wood and Stone.")
        
        # 2. Composite Tools (Wood + Stone)
        self.add_tech("composite_tools", "Composite Tools", 2000, 
                      "Combine materials. Unlocks Stone Axe (+50% Wood).", 
                      requirements=["primitive_tools"])

        # 3. Fire Mastery
        self.add_tech("fire", "Fire Mastery", 5000, 
                      "Control fire. Reduces Winter cold penalties.", 
                      requirements=["primitive_tools"])

        # 4. Weapons (Spears)
        self.add_tech("spears", "Hunting Spears", 3500, 
                      "Sharp stick with stone tip. Hunts yield +50% food.",
                      requirements=["composite_tools"])

        self.research_speed_modifier = 1.0

    def add_tech(self, key, name, cost, desc, requirements=None):
        self.techs[key] = Technology(key, name, cost, desc, requirements)

    def unlock(self, key):
        if key in self.techs:
            self.techs[key].unlocked = True

    def get_available_research(self) -> List[Technology]:
        # Logic for "Active Research" could go here if we want manual selection.
        # For now, we unlock automatically if points sufficient? 
        # Or we return list of things that CAN be unlocked logic.
        return [t for t in self.techs.values() if not t.unlocked]

    def check_unlocks(self, current_ideas: float) -> List[str]:
        """
        Checks if any tech costs are met and requirements satisfied.
        Returns list of newly unlocked tech names.
        """
        unlocked_now = []
        # Sort by cost (cheapest first)
        sorted_candidates = sorted([t for t in self.techs.values() if not t.unlocked], key=lambda x: x.cost)
        
        for tech in sorted_candidates:
            # Check reqs
            reqs_met = all(self.techs[req].unlocked for req in tech.requirements)
            
            if reqs_met and current_ideas >= tech.cost:
                tech.unlocked = True
                unlocked_now.append(tech.name)
                # We do NOT deduct cost in this "Organic" model? 
                # "Ideas" are cumulative cultural knowledge, not currency spent?
                # Actually, usually 'spending' points makes game balance easier.
                # But 'Cumulative Knowledge' feels more Stone Age. Knowledge builds up.
                # Let's try CUMULATIVE first. If 2000 points, you know everything cost < 2000.
                pass
                
        return unlocked_now

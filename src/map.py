import random
from typing import List, Tuple

COLORS = {
    "Plains": "#90EE90",  # Light Green
    "Forest": "#228B22",  # Dark Green
    "Mountain": "#808080", # Grey
    "River": "#87CEEB",    # Blue
    "Village": "#FF4500",  # Orange Red
    "Unexplored": "#000000" # Black
}

class Tile:
    def __init__(self, x, y, biome="Plains"):
        self.x = x
        self.y = y
        self.biome = biome
        self.is_explored = False
        self.danger_level = 0.0 # 0.0 to 1.0 (Predator chance)
        self.resource_yield = {}
        
        # Set base yields & Danger
        if biome == "Forest":
            self.resource_yield = {"Wood": 1.0, "Food": 0.5}
            self.danger_level = 0.3 # Wolves/Bears
        elif biome == "Mountain":
            self.resource_yield = {"Stone": 1.0}
            self.danger_level = 0.5 # Mountain Lions/Falls
        elif biome == "River":
            self.resource_yield = {"Food": 1.5, "Water": 1.0}
            self.danger_level = 0.1 # Crocodiles?
        else: # Plains
            self.resource_yield = {"Food": 0.2}
            self.danger_level = 0.05 # Safe

class WorldMap:
    def __init__(self, width=20, height=20):
        self.width = width
        self.height = height
        self.grid = []
        self.generate()
        
        # Center Village
        self.village_x = width // 2
        self.village_y = height // 2
        self.explore(self.village_x, self.village_y, radius=1) # Reveal starting area

    def generate(self):
        self.grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Simple random generation for now. 
                # Can be improved with noise later.
                rand = random.random()
                if rand < 0.6: biome = "Plains"
                elif rand < 0.8: biome = "Forest"
                elif rand < 0.9: biome = "Mountain"
                else: biome = "River"
                
                # Create Tile
                t = Tile(x, y, biome)
                
                # Random "Danger Zones" (Nests)
                if random.random() < 0.05:
                    t.danger_level = 0.9 # Deadly
                    
                row.append(t)
            self.grid.append(row)

    def explore(self, cx, cy, radius):
        """Reveals tiles within radius of center x,y"""
        count_new = 0
        for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                if not self.grid[y][x].is_explored:
                    self.grid[y][x].is_explored = True
                    count_new += 1
        return count_new

    def get_stats(self):
        stats = {"Plains": 0, "Forest": 0, "Mountain": 0, "River": 0}
        total_explored = 0
        for row in self.grid:
            for tile in row:
                if tile.is_explored:
                    stats[tile.biome] += 1
                    total_explored += 1
        return stats, total_explored

    def get_view_matrix(self):
        """Returns color matrix for rendering"""
        matrix = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = self.grid[y][x]
                if x == self.village_x and y == self.village_y:
                    row.append(COLORS["Village"])
                elif tile.is_explored:
                    row.append(COLORS[tile.biome])
                else:
                    row.append(COLORS["Unexplored"])
            matrix.append(row)
        return matrix

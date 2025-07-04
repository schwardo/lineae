"""Board management for Lineae game."""

from typing import Dict, List, Optional, Set, Tuple
import random
from .constants import (
    BOARD_WIDTH, BOARD_HEIGHT, Position, ResourceType, 
    LOCK_POSITIONS, INITIAL_SUBMERSIBLE_POSITIONS,
    SUBMERSIBLE_NAMES, DEPOSIT_TYPES
)
from .resources import ResourcePool, Submersible, Rocket, MineralDeposit

class OceanSpace:
    """Represents a space in the ocean."""
    
    def __init__(self, position: Position):
        self.position = position
        self.resource: Optional[ResourceType] = None
        self.submersible: Optional[Submersible] = None
        self.has_water = False
    
    def is_empty(self) -> bool:
        """Check if space has no resource or submersible."""
        return self.resource is None and self.submersible is None
    
    def can_enter(self) -> bool:
        """Check if a submersible can enter this space."""
        return self.resource is None and self.submersible is None
    
    def add_resource(self, resource_type: ResourceType) -> bool:
        """Add a resource cube if space is empty."""
        if self.is_empty():
            self.resource = resource_type
            return True
        return False
    
    def remove_resource(self) -> Optional[ResourceType]:
        """Remove and return resource from space."""
        resource = self.resource
        self.resource = None
        return resource
    
    def __repr__(self) -> str:
        content = []
        if self.resource:
            content.append(f"R:{self.resource.value[0]}")
        if self.submersible:
            content.append(f"S:{self.submersible.name}")
        return f"Space({self.position.x},{self.position.y},[{','.join(content)}])"


class Board:
    """Represents the game board."""
    
    def __init__(self):
        # Initialize ocean grid
        self.ocean: Dict[Position, OceanSpace] = {}
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                pos = Position(x, y)
                self.ocean[pos] = OceanSpace(pos)
        
        # Water tiles and locks
        self.water_tiles: List[Position] = []
        self.locks: Dict[int, bool] = {}  # x-position -> is_open
        # Initialize locks: 2 open and 2 closed (alternating pattern)
        for i, lock_pos in enumerate(LOCK_POSITIONS):
            self.locks[lock_pos] = (i % 2 == 0)  # Alternating: positions 1 and 4 open, 3 and 6 closed
        
        # Submersibles
        self.submersibles: Dict[str, Submersible] = {}
        for name in SUBMERSIBLE_NAMES:
            sub = Submersible(name)
            self.submersibles[name] = sub
        
        # Surface vessels (player positions)
        self.vessel_positions: Dict[int, Position] = {}  # player_id -> position
        
        # Rockets (8 rockets, one per tile position)
        self.rockets: List[Optional[Rocket]] = [None] * 8
        
        # Mineral deposits
        self.deposits: List[Optional[MineralDeposit]] = [None] * 4
        
        # Jupiter position (0-6, where 0 is rightmost)
        self.jupiter_position = 0
        
        # Atmosphere (hydrocarbon cubes blocking sunlight)
        self.atmosphere: Dict[int, int] = {}  # x-position -> count
    
    def setup_board(self) -> None:
        """Set up initial board state."""
        # Place submersibles at starting positions
        for name, pos in INITIAL_SUBMERSIBLE_POSITIONS.items():
            self.place_submersible(name, pos)
        
        # Initialize water tiles
        self._initialize_water()
        
        # Set up mineral deposits (random selection)
        available_deposits = DEPOSIT_TYPES.copy()
        random.shuffle(available_deposits)
        
        for i in range(4):
            resource_type = available_deposits[i]
            # Random setup bonus (could be same as main resource)
            setup_bonus = random.choice(DEPOSIT_TYPES)
            self.deposits[i] = MineralDeposit(resource_type, setup_bonus)
            
            # Place initial resource cubes above deposit (one in each of the 6 columns)
            for col in range(6):
                x = i * 6 + col
                self.ocean[Position(x, BOARD_HEIGHT - 1)].add_resource(resource_type)
        
        # Generate random rockets
        self._generate_rockets()
    
    def _initialize_water(self) -> None:
        """Initialize water tiles based on lock positions."""
        # Water fills from left, stopped by closed locks
        for y in range(3):  # Top 3 rows have water
            for x in range(BOARD_WIDTH):
                # Check if blocked by a lock
                blocked = False
                for lock_x in sorted(self.locks.keys()):
                    if x > lock_x and not self.locks[lock_x]:  # Closed lock
                        blocked = True
                        break
                
                if not blocked:
                    pos = Position(x, y)
                    self.ocean[pos].has_water = True
                    self.water_tiles.append(pos)
    
    def _generate_rockets(self) -> None:
        """Generate random rocket cards."""
        rocket_names = [
            "Orbital Station", "Mars Colony", "Asteroid Miner",
            "Jupiter Probe", "Research Lab", "Solar Array",
            "Lunar Base", "Deep Space Explorer"
        ]
        
        # Place 8 rockets, one per tile position
        for i in range(8):
            # All rockets have exactly 5 cubes
            # 4 specific resource requirements + 1 wildcard
            requirements = {}
            
            # Generate 4 specific resource requirements
            for _ in range(4):
                resource = random.choice(list(ResourceType))
                requirements[resource] = requirements.get(resource, 0) + 1
            
            # Note: The wildcard slot is handled in the loading logic
            # We just track the 4 specific requirements here
            self.rockets[i] = Rocket(rocket_names[i], requirements, i)
    
    def place_submersible(self, name: str, position: Position) -> bool:
        """Place a submersible at a position."""
        if name not in self.submersibles:
            return False
        
        space = self.ocean.get(position)
        if not space or not space.can_enter():
            return False
        
        sub = self.submersibles[name]
        
        # Remove from old position if any
        if sub.position:
            old_space = self.ocean.get(sub.position)
            if old_space and old_space.submersible == sub:
                old_space.submersible = None
        
        # Place at new position
        space.submersible = sub
        sub.position = position
        return True
    
    def move_submersible(self, name: str, path: List[Position]) -> List[ResourceType]:
        """
        Move submersible along path, collecting resources.
        Returns list of resources collected.
        """
        if name not in self.submersibles:
            return []
        
        sub = self.submersibles[name]
        collected = []
        
        for pos in path:
            # Check if valid move
            space = self.ocean.get(pos)
            if not space:
                break
            
            # Collect resource if present and sub has space
            if space.resource and sub.has_space():
                resource = space.remove_resource()
                sub.load(resource)
                collected.append(resource)
            
            # Can't end on occupied space
            if pos == path[-1] and not space.can_enter():
                break
            
            # Move submersible
            if pos != path[-1]:  # Don't place on final position yet
                continue
                
            self.place_submersible(name, pos)
        
        return collected
    
    def toggle_lock(self, lock_x: int) -> bool:
        """Toggle a lock open/closed. Returns new state."""
        if lock_x not in self.locks:
            return False
        
        self.locks[lock_x] = not self.locks[lock_x]
        self._update_water_flow()
        return self.locks[lock_x]
    
    def _update_water_flow(self) -> None:
        """Update water flow after lock change."""
        # This is simplified - full implementation would handle
        # water sliding, dropping into holes, etc.
        pass
    
    def place_vessel(self, player_id: int, position: Position) -> bool:
        """Place a player's surface vessel."""
        if position.y != 0:  # Must be at surface
            return False
        # Convert to tile column (0-7) range
        tile_x = position.x
        if tile_x < 0 or tile_x >= 8:  # Only 8 tile columns
            return False
        
        self.vessel_positions[player_id] = position
        return True
    
    def move_vessel(self, player_id: int, new_tile_x: int) -> bool:
        """Move vessel horizontally if water level allows."""
        if player_id not in self.vessel_positions:
            return False
        
        current_pos = self.vessel_positions[player_id]
        
        # Check if new position is valid (tile column 0-7)
        if new_tile_x < 0 or new_tile_x >= 8:
            return False
        
        # Check if water levels allow movement between current and new position
        # Must check all intermediate positions
        start_x = min(current_pos.x, new_tile_x)
        end_x = max(current_pos.x, new_tile_x)
        
        # Get water level at starting position (check middle mineral column of tile)
        start_water_level = self.get_water_level_at_x(start_x * 3 + 1)
        
        # Check all positions between start and end
        for x in range(start_x, end_x + 1):
            # Check middle mineral column of each tile
            if self.get_water_level_at_x(x * 3 + 1) != start_water_level:
                return False
        
        # Movement is valid
        self.vessel_positions[player_id] = Position(new_tile_x, 0)
        return True
    
    def get_water_level_at_x(self, x: int) -> int:
        """Get the water level (y-coordinate of top water) at a given x position."""
        # Find the highest y-coordinate with water at this x
        for y in range(BOARD_HEIGHT):
            if self.ocean[Position(x, y)].has_water:
                return y
        return -1  # No water at this x position
    
    def get_sunlight_positions(self) -> Set[int]:
        """Get x-positions receiving sunlight."""
        sunlit = set()
        
        for x in range(BOARD_WIDTH):
            # Check if blocked by Jupiter
            if x >= BOARD_WIDTH - 2 - self.jupiter_position:
                continue
            
            sunlit.add(x)
        
        return sunlit
    
    def get_electricity_at_position(self, tile_x: int) -> int:
        """Get electricity generated at a tile position (considering pollution)."""
        # Check center mineral column of the tile
        mineral_x = tile_x * 3 + 1
        
        if mineral_x not in self.get_sunlight_positions():
            return 0
        
        # Each pollution cube blocks 2 electricity
        pollution_count = self.atmosphere.get(mineral_x, 0)
        electricity = 6 - (pollution_count * 2)
        return max(0, electricity)
    
    def add_to_atmosphere(self, x: int) -> bool:
        """Add hydrocarbon to atmosphere at x position."""
        if x < 0 or x >= BOARD_WIDTH:
            return False
        
        self.atmosphere[x] = self.atmosphere.get(x, 0) + 1
        return True
    
    def advance_jupiter(self) -> None:
        """Advance Jupiter one space left."""
        if self.jupiter_position < 6:
            self.jupiter_position += 1
    
    def dissolve_minerals(self) -> None:
        """Add minerals from deposits at cleanup phase."""
        for i, deposit in enumerate(self.deposits):
            if not deposit:
                continue
            
            # Each deposit dissolves 2 cubes per round (across its 6 columns)
            cubes_to_add = 2
            
            # Try to place cubes in the deposit's 6 columns
            for col in range(6):
                if cubes_to_add == 0:
                    break
                    
                x = i * 6 + col
                # Determine which resource type based on alternating pattern
                if col % 2 == 0:
                    resource_type = deposit.resource_type
                else:
                    resource_type = deposit.secondary_resource_type
                
                # Find lowest empty space in this column
                for y in range(BOARD_HEIGHT - 1, -1, -1):
                    pos = Position(x, y)
                    space = self.ocean[pos]
                    
                    if space.is_empty():
                        space.add_resource(resource_type)
                        cubes_to_add -= 1
                        break
    
    def get_deposit_below(self, position: Position) -> Optional[Tuple[int, MineralDeposit]]:
        """Get mineral deposit below a position at ocean floor."""
        if position.y != BOARD_HEIGHT - 1:  # Not at ocean floor
            return None
        
        # Check which deposit we're in (each deposit spans 6 columns)
        deposit_idx = position.x // 6
        if deposit_idx < len(self.deposits):
            deposit = self.deposits[deposit_idx]
            if deposit:
                return deposit_idx, deposit
        
        return None
    
    def is_submersible_at_surface(self, name: str) -> bool:
        """Check if submersible is at water surface."""
        if name not in self.submersibles:
            return False
        
        sub = self.submersibles[name]
        if not sub.position:
            return False
        
        # Check if at top row with water
        return (sub.position.y == 0 and 
                self.ocean[sub.position].has_water)
    
    def is_submersible_below_vessel(self, sub_name: str, player_id: int) -> bool:
        """Check if submersible is below a player's vessel (for docking)."""
        if not self.is_submersible_at_surface(sub_name):
            return False
        
        if player_id not in self.vessel_positions:
            return False
        
        sub = self.submersibles[sub_name]
        vessel_tile_x = self.vessel_positions[player_id].x
        
        # Vessel covers 3 mineral columns (tile_x * 3 to tile_x * 3 + 2)
        # Check if submersible is in one of those columns
        return vessel_tile_x * 3 <= sub.position.x <= vessel_tile_x * 3 + 2
    
    def get_board_state(self) -> dict:
        """Get board state for display/logging."""
        state = {
            "jupiter_position": self.jupiter_position,
            "locks": {f"x{k}": "open" if v else "closed" 
                     for k, v in self.locks.items()},
            "vessels": {f"P{pid}": f"x{pos.x}" 
                       for pid, pos in self.vessel_positions.items()},
            "submersibles": {name: f"({sub.position.x},{sub.position.y})" 
                           if sub.position else "none"
                           for name, sub in self.submersibles.items()},
            "rockets": [{"name": r.name, "progress": f"{r.loaded_resources.total()}/{sum(r.required_resources.values())}"}
                       if r else None
                       for r in self.rockets],
            "deposits": [d.resource_type.value if d else None 
                        for d in self.deposits]
        }
        return state
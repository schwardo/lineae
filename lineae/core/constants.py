"""Game constants and configuration for Lineae."""

from enum import Enum, auto
from typing import Dict, List, Tuple

# Game Configuration
MAX_PLAYERS = 5
MIN_PLAYERS = 1
MAX_ROUNDS = 7
BOARD_WIDTH = 8
BOARD_HEIGHT = 10
INITIAL_MONEY = 3
MAX_ELECTRICITY = 9
INITIAL_WORKERS = 4  # 3 for 4-5 player games
MAX_TECHNOLOGY_CARDS = 2

# Resource Types
class ResourceType(Enum):
    """Types of resources in the game."""
    SILICA = "silica"
    SULFUR = "sulfur"
    SALT = "salt"
    IRON = "iron"
    HYDROCARBON = "hydrocarbon"

# Resource Colors for display
RESOURCE_COLORS: Dict[ResourceType, str] = {
    ResourceType.SILICA: "white",
    ResourceType.SULFUR: "yellow",
    ResourceType.SALT: "cyan",
    ResourceType.IRON: "red",
    ResourceType.HYDROCARBON: "black"
}

# Action Types
class ActionType(Enum):
    """Types of actions players can take."""
    PLACE_WORKER = auto()
    MOVE_VESSEL = auto()
    MOVE_SUBMERSIBLE = auto()
    TOGGLE_LOCK = auto()
    LOAD_ROCKET = auto()
    EXCAVATE = auto()
    DOCK = auto()
    BASIC_INCOME = auto()
    HIRE_WORKER = auto()
    SPECIAL_ELECTION = auto()
    USE_DIESEL = auto()
    PASS = auto()

# Submersible Configuration
SUBMERSIBLE_NAMES = ["A", "B", "C", "D", "E", "F"]
SUBMERSIBLE_CAPACITY = 3

# Victory Points
VP_EXCAVATION_TRACK = [1, 1, 2, 1, 3]  # VP earned at each track position
VP_ROCKET_LOADING = [1, 2, 3, 3, 3]  # VP for loading 1st, 2nd, 3rd+ cubes

# Costs
WORKER_HIRE_COSTS = [4, 5, 6, 7, 8]  # Cost to hire 4th, 5th, 6th+ workers
DOCK_COST_PER_CUBE = 1
ELECTRICITY_PER_MOVE = 1  # After first free move
DIESEL_ENGINE_ELECTRICITY = 6

# Board Positions
class Position:
    """Represents a position on the board."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __repr__(self):
        return f"Position({self.x}, {self.y})"

# Lock Positions (x-coordinates where locks are placed)
LOCK_POSITIONS = [1, 3, 4, 6]

# Initial Submersible Positions
INITIAL_SUBMERSIBLE_POSITIONS: Dict[str, Position] = {
    "A": Position(0, 5),
    "B": Position(2, 5),
    "C": Position(3, 7),
    "D": Position(5, 7),
    "E": Position(6, 9),
    "F": Position(7, 5)
}

# Mineral Deposit Configuration
DEPOSIT_TYPES = [
    ResourceType.SILICA,
    ResourceType.SULFUR,
    ResourceType.SALT,
    ResourceType.IRON,
    ResourceType.HYDROCARBON
]

# Game Phases
class GamePhase(Enum):
    """Phases of each game round."""
    SUNLIGHT = "sunlight"
    ACTION = "action"
    CLEANUP = "cleanup"

# Worker Placement Rules
MULTIPLE_WORKERS_ALLOWED = [ActionType.BASIC_INCOME]
IMMEDIATE_SECOND_ACTION = [ActionType.TOGGLE_LOCK, ActionType.BASIC_INCOME]
"""Player management for Lineae game."""

from typing import List, Optional, Set
from .constants import (
    INITIAL_MONEY, INITIAL_WORKERS, MAX_ELECTRICITY, 
    ResourceType, Position, WORKER_HIRE_COSTS
)
from .resources import ResourcePool

class Player:
    """Represents a player in the game."""
    
    def __init__(self, player_id: int, name: str, num_players: int):
        self.id = player_id
        self.name = name
        self.money = INITIAL_MONEY
        self.victory_points = 0
        self.electricity = 0
        
        # Workers
        self.total_workers = INITIAL_WORKERS if num_players <= 3 else 3
        self.available_workers = self.total_workers
        self.workers_in_supply = 8 - self.total_workers  # Remaining workers to hire
        
        # Resources
        self.cargo_bay = ResourcePool()
        
        # Position
        self.vessel_position: Optional[Position] = None
        
        # Game state
        self.technology_cards: List[str] = []
        self.launched_rockets: List[str] = []
        self.has_first_player_marker = False
        self.passed = False
        
        # Track which excavation tracks this player is on
        self.excavation_positions: dict = {}  # deposit_id -> position
    
    def add_money(self, amount: int) -> None:
        """Add money to player's supply."""
        if amount < 0:
            raise ValueError("Cannot add negative money")
        self.money += amount
    
    def spend_money(self, amount: int) -> bool:
        """Spend money if player has enough. Returns True if successful."""
        if amount < 0:
            raise ValueError("Cannot spend negative money")
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def add_victory_points(self, points: int) -> None:
        """Add victory points."""
        self.victory_points += points
    
    def add_electricity(self, amount: int) -> None:
        """Add electricity, capped at MAX_ELECTRICITY."""
        self.electricity = min(self.electricity + amount, MAX_ELECTRICITY)
    
    def use_electricity(self, amount: int) -> bool:
        """Use electricity if available. Returns True if successful."""
        if amount < 0:
            raise ValueError("Cannot use negative electricity")
        if self.electricity >= amount:
            self.electricity -= amount
            return True
        return False
    
    def place_workers(self, count: int) -> bool:
        """Place workers if available. Returns True if successful."""
        if count <= 0:
            raise ValueError("Must place at least one worker")
        if self.available_workers >= count:
            self.available_workers -= count
            return True
        return False
    
    def recall_workers(self, count: int) -> None:
        """Recall workers (e.g., when bumped)."""
        self.available_workers = min(self.available_workers + count, self.total_workers)
    
    def reset_workers(self) -> None:
        """Reset all workers at end of round."""
        self.available_workers = self.total_workers
    
    def hire_worker(self) -> bool:
        """Hire a new worker if possible. Returns True if successful."""
        if self.workers_in_supply <= 0:
            return False
        
        # Calculate cost
        workers_hired = self.total_workers - INITIAL_WORKERS
        if workers_hired >= len(WORKER_HIRE_COSTS):
            cost = WORKER_HIRE_COSTS[-1]  # Use last cost for 6+ workers
        else:
            cost = WORKER_HIRE_COSTS[workers_hired]
        
        if self.spend_money(cost):
            self.workers_in_supply -= 1
            self.total_workers += 1
            self.available_workers += 1
            return True
        return False
    
    def can_hire_worker(self) -> tuple[bool, int]:
        """Check if player can hire worker and return cost."""
        if self.workers_in_supply <= 0:
            return False, 0
        
        workers_hired = self.total_workers - INITIAL_WORKERS
        if workers_hired >= len(WORKER_HIRE_COSTS):
            cost = WORKER_HIRE_COSTS[-1]
        else:
            cost = WORKER_HIRE_COSTS[workers_hired]
        
        return self.money >= cost, cost
    
    def add_technology_card(self, card_name: str) -> Optional[str]:
        """
        Add technology card. Returns card that was discarded if at limit.
        """
        self.technology_cards.append(card_name)
        if len(self.technology_cards) > 2:
            # Player must discard one (in real game, player chooses)
            # For now, discard the oldest
            return self.technology_cards.pop(0)
        return None
    
    def launch_rocket(self, rocket_name: str) -> None:
        """Record that player launched a rocket."""
        self.launched_rockets.append(rocket_name)
    
    def use_diesel_engine(self) -> bool:
        """
        Use diesel engine to generate electricity by burning hydrocarbon.
        Returns True if successful.
        """
        if self.cargo_bay.has(ResourceType.HYDROCARBON):
            if self.cargo_bay.remove(ResourceType.HYDROCARBON):
                self.add_electricity(6)
                return True
        return False
    
    def calculate_end_game_vp(self) -> int:
        """Calculate additional VP at game end."""
        additional_vp = 0
        
        # $5 = 1 VP
        additional_vp += self.money // 5
        
        # Pairs of same resource = 1 VP each
        for resource_type in ResourceType:
            count = self.cargo_bay.count(resource_type)
            additional_vp += count // 2
        
        return additional_vp
    
    def get_state(self) -> dict:
        """Get player state as dictionary for display/logging."""
        return {
            "id": self.id,
            "name": self.name,
            "money": self.money,
            "victory_points": self.victory_points,
            "electricity": self.electricity,
            "workers": f"{self.available_workers}/{self.total_workers}",
            "cargo": self.cargo_bay.get_all(),
            "technology_cards": len(self.technology_cards),
            "rockets_launched": len(self.launched_rockets),
            "has_first_player": self.has_first_player_marker,
            "passed": self.passed
        }
    
    def __repr__(self) -> str:
        return (f"Player({self.name}, VP={self.victory_points}, "
                f"${self.money}, E={self.electricity})")


class PlayerOrder:
    """Manages turn order for players."""
    
    def __init__(self, players: List[Player]):
        self.players = players
        self.current_player_index = 0
        self.first_player_id = 0 if players else None
    
    def get_current_player(self) -> Optional[Player]:
        """Get the current player."""
        if not self.players:
            return None
        return self.players[self.current_player_index]
    
    def next_turn(self) -> Optional[Player]:
        """Move to next player who hasn't passed."""
        if not self.players:
            return None
        
        starting_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            
            # If we've gone full circle, all have passed
            if self.current_player_index == starting_index:
                # Check if starting player has also passed
                if self.players[starting_index].passed:
                    return None
                else:
                    return self.players[starting_index]
            
            # Return next player who hasn't passed
            if not self.players[self.current_player_index].passed:
                return self.players[self.current_player_index]
    
    def set_first_player(self, player_id: int) -> None:
        """Set the first player for next round."""
        self.first_player_id = player_id
        # Find player index
        for i, player in enumerate(self.players):
            if player.id == player_id:
                self.current_player_index = i
                break
    
    def reset_for_new_round(self) -> None:
        """Reset turn order for new round."""
        # Reset all players' passed status
        for player in self.players:
            player.passed = False
        
        # Set current player to first player
        if self.first_player_id is not None:
            self.set_first_player(self.first_player_id)
    
    def get_reverse_order(self) -> List[Player]:
        """Get players in reverse turn order (for setup)."""
        # Start from player before first player
        start_idx = (self.current_player_index - 1) % len(self.players)
        reverse_order = []
        
        for i in range(len(self.players)):
            idx = (start_idx - i) % len(self.players)
            reverse_order.append(self.players[idx])
        
        return reverse_order
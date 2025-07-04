"""AI strategies for Lineae simulations."""

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..core.game import Game
from ..core.constants import Position, ResourceType, ActionType
from ..core.actions import (
    Action, PassAction, BasicIncomeAction, HireWorkerAction,
    SpecialElectionAction, MoveVesselAction, MoveSubmersibleAction,
    ToggleLockAction, LoadRocketAction, UseDieselAction
)

class Strategy(ABC):
    """Base class for AI strategies."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def choose_action(self, game: Game, player_id: int) -> Optional[Action]:
        """Choose an action for the player."""
        pass
    
    def get_valid_actions(self, game: Game, player_id: int) -> List[str]:
        """Get list of valid actions for player."""
        return game.get_valid_actions(player_id)


class RandomStrategy(Strategy):
    """Completely random strategy."""
    
    def __init__(self):
        super().__init__("Random")
    
    def choose_action(self, game: Game, player_id: int) -> Optional[Action]:
        """Choose a random valid action."""
        valid_actions = self.get_valid_actions(game, player_id)
        if not valid_actions:
            return None
        
        action_type = random.choice(valid_actions)
        return self._create_random_action(game, player_id, action_type)
    
    def _create_random_action(self, game: Game, player_id: int, 
                            action_type: str) -> Optional[Action]:
        """Create a random action of the given type."""
        if action_type == "PASS":
            return PassAction(player_id)
        
        elif action_type == "BASIC_INCOME":
            return BasicIncomeAction(player_id)
        
        elif action_type == "HIRE_WORKER":
            return HireWorkerAction(player_id)
        
        elif action_type == "SPECIAL_ELECTION":
            return SpecialElectionAction(player_id)
        
        elif action_type == "MOVE_VESSEL":
            new_x = random.randint(0, 7)
            return MoveVesselAction(player_id, new_x)
        
        elif action_type == "MOVE_SUBMERSIBLE":
            # Pick random submersible
            sub_name = random.choice(list(game.board.submersibles.keys()))
            sub = game.board.submersibles[sub_name]
            
            if sub.position:
                # Create random path
                path = []
                current_pos = sub.position
                moves = random.randint(1, 3)
                
                for _ in range(moves):
                    # Random direction
                    dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    new_pos = Position(
                        max(0, min(7, current_pos.x + dx)),
                        max(0, min(9, current_pos.y + dy))
                    )
                    path.append(new_pos)
                    current_pos = new_pos
                
                action = MoveSubmersibleAction(player_id, sub_name, path)
                
                # Random excavate/dock
                if path[-1].y == 9 and random.random() < 0.5:
                    action.excavate = True
                elif path[-1].y == 0 and random.random() < 0.5:
                    action.dock = True
                
                return action
        
        elif action_type == "TOGGLE_LOCK":
            lock_x = random.choice(list(game.board.locks.keys()))
            return ToggleLockAction(player_id, lock_x)
        
        elif action_type == "LOAD_ROCKET":
            player = game.get_player(player_id)
            vessel_pos = game.board.vessel_positions[player_id]
            rocket = game.board.rockets[vessel_pos.x]
            
            # Load random resources that match requirements
            resources = []
            for resource_type in ResourceType:
                if player.cargo_bay.has(resource_type):
                    needed = rocket.required_resources.get(resource_type, 0)
                    loaded = rocket.loaded_resources.count(resource_type)
                    if loaded < needed:
                        resources.append(resource_type)
            
            if resources:
                # Load 1-3 random resources
                num_to_load = min(len(resources), random.randint(1, 3))
                resources_to_load = random.sample(resources, num_to_load)
                return LoadRocketAction(player_id, resources_to_load)
        
        elif action_type == "USE_DIESEL":
            return UseDieselAction(player_id)
        
        return None


class GreedyStrategy(Strategy):
    """Greedy strategy focused on immediate gains."""
    
    def __init__(self):
        super().__init__("Greedy")
    
    def choose_action(self, game: Game, player_id: int) -> Optional[Action]:
        """Choose action that gives immediate benefits."""
        player = game.get_player(player_id)
        valid_actions = self.get_valid_actions(game, player_id)
        
        if not valid_actions:
            return None
        
        # Priority order for greedy strategy
        # 1. Load rockets if we can (immediate VP)
        if "LOAD_ROCKET" in valid_actions:
            action = self._try_load_rocket(game, player_id)
            if action:
                return action
        
        # 2. Move submersible to collect resources
        if "MOVE_SUBMERSIBLE" in valid_actions and player.electricity > 0:
            action = self._try_collect_resources(game, player_id)
            if action:
                return action
        
        # 3. Basic income if low on money
        if "BASIC_INCOME" in valid_actions and player.money < 5:
            return BasicIncomeAction(player_id)
        
        # 4. Use diesel if low on electricity
        if "USE_DIESEL" in valid_actions and player.electricity < 3:
            return UseDieselAction(player_id)
        
        # 5. Hire worker if we can afford it
        if "HIRE_WORKER" in valid_actions:
            return HireWorkerAction(player_id)
        
        # 6. Pass if nothing else
        return PassAction(player_id)
    
    def _try_load_rocket(self, game: Game, player_id: int) -> Optional[LoadRocketAction]:
        """Try to load resources onto rocket."""
        player = game.get_player(player_id)
        vessel_pos = game.board.vessel_positions[player_id]
        rocket = game.board.rockets[vessel_pos.x]
        
        if not rocket or rocket.is_complete():
            return None
        
        # Load all matching resources we have
        resources_to_load = []
        for resource_type, needed in rocket.required_resources.items():
            loaded = rocket.loaded_resources.count(resource_type)
            while loaded < needed and player.cargo_bay.has(resource_type):
                resources_to_load.append(resource_type)
                player.cargo_bay.remove(resource_type)  # Temporary
                loaded += 1
        
        # Restore cargo
        for resource in resources_to_load:
            player.cargo_bay.add(resource)
        
        if resources_to_load:
            return LoadRocketAction(player_id, resources_to_load)
        
        return None
    
    def _try_collect_resources(self, game: Game, player_id: int) -> Optional[MoveSubmersibleAction]:
        """Try to move submersible to collect resources."""
        player = game.get_player(player_id)
        best_action = None
        best_value = 0
        
        for sub_name, sub in game.board.submersibles.items():
            if not sub.position or not sub.has_space():
                continue
            
            # Find nearby resources
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    new_x = sub.position.x + dx
                    new_y = sub.position.y + dy
                    
                    if 0 <= new_x < 8 and 0 <= new_y < 10:
                        pos = Position(new_x, new_y)
                        space = game.board.ocean[pos]
                        
                        if space.resource and space.can_enter():
                            # Value this move
                            value = 1  # Base value for any resource
                            
                            # Check if we need this for a rocket
                            vessel_pos = game.board.vessel_positions.get(player_id)
                            if vessel_pos:
                                rocket = game.board.rockets[vessel_pos.x]
                                if rocket and not rocket.is_complete():
                                    needed = rocket.required_resources.get(space.resource, 0)
                                    loaded = rocket.loaded_resources.count(space.resource)
                                    if loaded < needed:
                                        value += 5  # High value for needed resources
                            
                            if value > best_value:
                                best_value = value
                                best_action = MoveSubmersibleAction(
                                    player_id, sub_name, [pos]
                                )
        
        return best_action


class BalancedStrategy(Strategy):
    """Balanced strategy that considers multiple factors."""
    
    def __init__(self):
        super().__init__("Balanced")
        self.action_weights = {
            "early_game": {
                "MOVE_SUBMERSIBLE": 0.4,
                "BASIC_INCOME": 0.2,
                "HIRE_WORKER": 0.2,
                "TOGGLE_LOCK": 0.1,
                "OTHER": 0.1
            },
            "mid_game": {
                "MOVE_SUBMERSIBLE": 0.3,
                "LOAD_ROCKET": 0.3,
                "BASIC_INCOME": 0.1,
                "HIRE_WORKER": 0.1,
                "SPECIAL_ELECTION": 0.1,
                "OTHER": 0.1
            },
            "late_game": {
                "LOAD_ROCKET": 0.5,
                "MOVE_SUBMERSIBLE": 0.2,
                "USE_DIESEL": 0.1,
                "SPECIAL_ELECTION": 0.1,
                "OTHER": 0.1
            }
        }
    
    def choose_action(self, game: Game, player_id: int) -> Optional[Action]:
        """Choose action based on game phase and strategy."""
        player = game.get_player(player_id)
        valid_actions = self.get_valid_actions(game, player_id)
        
        if not valid_actions:
            return None
        
        # Determine game phase
        if game.current_round <= 2:
            phase = "early_game"
        elif game.current_round <= 5:
            phase = "mid_game"
        else:
            phase = "late_game"
        
        # Score each valid action
        action_scores = {}
        for action_type in valid_actions:
            if action_type == "PASS":
                continue  # Only pass if nothing else available
            
            # Base weight from strategy
            weight = self.action_weights[phase].get(action_type, 
                    self.action_weights[phase]["OTHER"])
            
            # Adjust based on game state
            score = self._score_action(game, player_id, action_type, weight)
            if score > 0:
                action_scores[action_type] = score
        
        if not action_scores:
            return PassAction(player_id)
        
        # Choose action probabilistically based on scores
        total_score = sum(action_scores.values())
        if total_score == 0:
            return PassAction(player_id)
        
        rand = random.random() * total_score
        cumulative = 0
        
        for action_type, score in action_scores.items():
            cumulative += score
            if rand <= cumulative:
                return self._create_action(game, player_id, action_type)
        
        return PassAction(player_id)
    
    def _score_action(self, game: Game, player_id: int, 
                     action_type: str, base_weight: float) -> float:
        """Score an action based on current game state."""
        player = game.get_player(player_id)
        score = base_weight
        
        if action_type == "BASIC_INCOME":
            # Higher value if low on money
            if player.money < 3:
                score *= 2.0
            elif player.money > 10:
                score *= 0.5
        
        elif action_type == "HIRE_WORKER":
            # Value workers more if we have few
            if player.available_workers == 0:
                score *= 2.0
            if player.total_workers >= 6:
                score *= 0.5
        
        elif action_type == "MOVE_SUBMERSIBLE":
            # Check if we can collect valuable resources
            if player.electricity == 0:
                score = 0
            elif player.electricity > 5:
                score *= 1.5
        
        elif action_type == "LOAD_ROCKET":
            # Check if we have matching resources
            vessel_pos = game.board.vessel_positions.get(player_id)
            if vessel_pos:
                rocket = game.board.rockets[vessel_pos.x]
                if rocket and not rocket.is_complete():
                    matches = sum(1 for r in rocket.required_resources 
                                if player.cargo_bay.has(r))
                    if matches > 0:
                        score *= (1 + matches * 0.5)
                    else:
                        score = 0
        
        elif action_type == "USE_DIESEL":
            # Use if low on electricity
            if player.electricity < 2:
                score *= 2.0
            elif player.electricity > 6:
                score = 0
        
        return score
    
    def _create_action(self, game: Game, player_id: int, 
                      action_type: str) -> Optional[Action]:
        """Create an action of the given type."""
        # Use random strategy for simplicity
        random_strat = RandomStrategy()
        return random_strat._create_random_action(game, player_id, action_type)


class AggressiveStrategy(Strategy):
    """Aggressive strategy focused on completing rockets quickly."""
    
    def __init__(self):
        super().__init__("Aggressive")
    
    def choose_action(self, game: Game, player_id: int) -> Optional[Action]:
        """Choose actions focused on rocket completion."""
        player = game.get_player(player_id)
        valid_actions = self.get_valid_actions(game, player_id)
        
        if not valid_actions:
            return None
        
        # Find nearest incomplete rocket
        vessel_pos = game.board.vessel_positions[player_id]
        target_rocket = None
        min_distance = float('inf')
        
        for i, rocket in enumerate(game.board.rockets):
            if rocket and not rocket.is_complete():
                distance = abs(i - vessel_pos.x)
                if distance < min_distance:
                    min_distance = distance
                    target_rocket = (i, rocket)
        
        if not target_rocket:
            return PassAction(player_id)
        
        rocket_pos, rocket = target_rocket
        
        # 1. Move vessel to rocket if needed
        if vessel_pos.x != rocket_pos and "MOVE_VESSEL" in valid_actions:
            return MoveVesselAction(player_id, rocket_pos)
        
        # 2. Load rocket if at correct position
        if vessel_pos.x == rocket_pos and "LOAD_ROCKET" in valid_actions:
            action = self._try_load_rocket_aggressive(game, player_id, rocket)
            if action:
                return action
        
        # 3. Get resources we need
        needed_resources = set()
        for resource, count in rocket.required_resources.items():
            loaded = rocket.loaded_resources.count(resource)
            have = player.cargo_bay.count(resource)
            if loaded + have < count:
                needed_resources.add(resource)
        
        if needed_resources and "MOVE_SUBMERSIBLE" in valid_actions:
            action = self._find_needed_resources(game, player_id, needed_resources)
            if action:
                return action
        
        # 4. Get electricity for submersibles
        if "USE_DIESEL" in valid_actions and player.electricity < 3:
            return UseDieselAction(player_id)
        
        # 5. Get money if needed
        if "BASIC_INCOME" in valid_actions and player.money < 3:
            return BasicIncomeAction(player_id)
        
        # 6. Default to hiring workers
        if "HIRE_WORKER" in valid_actions:
            return HireWorkerAction(player_id)
        
        return PassAction(player_id)
    
    def _try_load_rocket_aggressive(self, game: Game, player_id: int, 
                                   rocket) -> Optional[LoadRocketAction]:
        """Aggressively load all possible resources."""
        player = game.get_player(player_id)
        resources_to_load = []
        
        for resource_type, needed in rocket.required_resources.items():
            loaded = rocket.loaded_resources.count(resource_type)
            while loaded < needed and player.cargo_bay.has(resource_type):
                resources_to_load.append(resource_type)
                player.cargo_bay.remove(resource_type)  # Temporary
                loaded += 1
        
        # Restore cargo
        for resource in resources_to_load:
            player.cargo_bay.add(resource)
        
        if resources_to_load:
            return LoadRocketAction(player_id, resources_to_load)
        
        return None
    
    def _find_needed_resources(self, game: Game, player_id: int,
                             needed: set) -> Optional[MoveSubmersibleAction]:
        """Find submersible path to collect needed resources."""
        # Simple implementation - just look for any needed resource
        for sub_name, sub in game.board.submersibles.items():
            if not sub.position or not sub.has_space():
                continue
            
            # Check nearby spaces
            for y in range(10):
                for x in range(8):
                    pos = Position(x, y)
                    space = game.board.ocean[pos]
                    
                    if space.resource and space.resource in needed:
                        # Simple path - just move there if close
                        distance = abs(pos.x - sub.position.x) + abs(pos.y - sub.position.y)
                        if distance <= 3:
                            # Create simple path
                            path = [pos]
                            return MoveSubmersibleAction(player_id, sub_name, path)
        
        return None


# Strategy factory
def create_strategy(strategy_name: str) -> Strategy:
    """Create a strategy instance by name."""
    strategies = {
        "random": RandomStrategy,
        "greedy": GreedyStrategy,
        "balanced": BalancedStrategy,
        "aggressive": AggressiveStrategy
    }
    
    strategy_class = strategies.get(strategy_name.lower())
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    return strategy_class()
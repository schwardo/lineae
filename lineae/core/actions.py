"""Game actions and validation for Lineae."""

from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass, field
from .constants import (
    ActionType, ResourceType, Position, 
    VP_ROCKET_LOADING, VP_EXCAVATION_TRACK,
    DOCK_COST_PER_CUBE, ELECTRICITY_PER_MOVE
)

@dataclass
class Action:
    """Base class for game actions."""
    action_type: ActionType
    player_id: int
    workers_required: int = 1

@dataclass
class PassAction(Action):
    """Player passes their turn."""
    def __init__(self, player_id: int):
        super().__init__(ActionType.PASS, player_id, 0)

@dataclass
class BasicIncomeAction(Action):
    """Take $2 basic income."""
    def __init__(self, player_id: int):
        super().__init__(ActionType.BASIC_INCOME, player_id, 1)

@dataclass
class HireWorkerAction(Action):
    """Hire a new worker."""
    def __init__(self, player_id: int):
        super().__init__(ActionType.HIRE_WORKER, player_id, 1)

@dataclass
class SpecialElectionAction(Action):
    """Take first player marker."""
    def __init__(self, player_id: int, workers: int = 1):
        super().__init__(ActionType.SPECIAL_ELECTION, player_id, workers)

@dataclass
class MoveVesselAction(Action):
    """Move surface vessel."""
    new_x: int = 0
    
    def __init__(self, player_id: int, new_x: int):
        super().__init__(ActionType.MOVE_VESSEL, player_id, 0)
        self.new_x = new_x

@dataclass
class MoveSubmersibleAction(Action):
    """Move a submersible."""
    submersible_name: str = ""
    path: List[Position] = field(default_factory=list)
    excavate: bool = False
    dock: bool = False
    
    def __init__(self, player_id: int, submersible_name: str, 
                 path: List[Position] = None, workers: int = 1,
                 excavate: bool = False, dock: bool = False):
        super().__init__(ActionType.MOVE_SUBMERSIBLE, player_id, workers)
        self.submersible_name = submersible_name
        self.path = path if path is not None else []
        self.excavate = excavate
        self.dock = dock

@dataclass
class ToggleLockAction(Action):
    """Toggle a lock open/closed."""
    lock_x: int = 0
    
    def __init__(self, player_id: int, lock_x: int):
        super().__init__(ActionType.TOGGLE_LOCK, player_id, 1)
        self.lock_x = lock_x

@dataclass
class LoadRocketAction(Action):
    """Load resources onto a rocket."""
    resources: List[ResourceType] = field(default_factory=list)
    
    def __init__(self, player_id: int, resources: List[ResourceType]):
        super().__init__(ActionType.LOAD_ROCKET, player_id, 1)
        self.resources = resources if resources is not None else []

@dataclass
class UseDieselAction(Action):
    """Use diesel engine to generate electricity."""
    pollution_x: int = -1  # X position to place pollution
    
    def __init__(self, player_id: int, pollution_x: int = -1):
        super().__init__(ActionType.USE_DIESEL, player_id, 0)
        self.pollution_x = pollution_x


class ActionValidator:
    """Validates if actions are legal."""
    
    def __init__(self, game):
        self.game = game  # Reference to game instance
    
    def validate(self, action: Action) -> Tuple[bool, Optional[str]]:
        """
        Validate if an action is legal.
        Returns (is_valid, error_message).
        """
        player = self.game.get_player(action.player_id)
        if not player:
            return False, "Invalid player"
        
        # Check if player has passed
        if player.passed and action.action_type != ActionType.PASS:
            return False, "Player has already passed"
        
        # Validate specific action types
        validators = {
            ActionType.PASS: self._validate_pass,
            ActionType.BASIC_INCOME: self._validate_basic_income,
            ActionType.HIRE_WORKER: self._validate_hire_worker,
            ActionType.SPECIAL_ELECTION: self._validate_special_election,
            ActionType.MOVE_VESSEL: self._validate_move_vessel,
            ActionType.MOVE_SUBMERSIBLE: self._validate_move_submersible,
            ActionType.TOGGLE_LOCK: self._validate_toggle_lock,
            ActionType.LOAD_ROCKET: self._validate_load_rocket,
            ActionType.USE_DIESEL: self._validate_use_diesel,
        }
        
        validator = validators.get(action.action_type)
        if not validator:
            return False, "Unknown action type"
        
        return validator(action, player)
    
    def _validate_pass(self, action: PassAction, player) -> Tuple[bool, Optional[str]]:
        """Validate pass action."""
        if player.passed:
            return False, "Already passed"
        return True, None
    
    def _validate_basic_income(self, action: BasicIncomeAction, player) -> Tuple[bool, Optional[str]]:
        """Validate basic income action."""
        if player.available_workers < 1:
            return False, "No workers available"
        return True, None
    
    def _validate_hire_worker(self, action: HireWorkerAction, player) -> Tuple[bool, Optional[str]]:
        """Validate hire worker action."""
        if player.available_workers < 1:
            return False, "No workers available"
        
        can_hire, cost = player.can_hire_worker()
        if not can_hire:
            if player.workers_in_supply <= 0:
                return False, "No workers left to hire"
            else:
                return False, f"Not enough money (need ${cost})"
        
        return True, None
    
    def _validate_special_election(self, action: SpecialElectionAction, player) -> Tuple[bool, Optional[str]]:
        """Validate special election action."""
        if player.available_workers < action.workers_required:
            return False, f"Need {action.workers_required} workers"
        
        # Check if need to bump existing placement
        current_holder = self.game.worker_placements.get("special_election")
        if current_holder and current_holder[0] != player.id:
            required = current_holder[1] + 1
            if action.workers_required < required:
                return False, f"Need {required} workers to bump"
        
        return True, None
    
    def _validate_move_vessel(self, action: MoveVesselAction, player) -> Tuple[bool, Optional[str]]:
        """Validate vessel movement."""
        # Check if movement is valid (simplified)
        if action.new_x < 0 or action.new_x >= 8:
            return False, "Invalid position"
        
        return True, None
    
    def _validate_move_submersible(self, action: MoveSubmersibleAction, player) -> Tuple[bool, Optional[str]]:
        """Validate submersible movement."""
        if player.available_workers < action.workers_required:
            return False, f"Need {action.workers_required} workers"
        
        # Check submersible control
        current_controller = self.game.worker_placements.get(f"sub_{action.submersible_name}")
        if current_controller and current_controller[0] != player.id:
            required = current_controller[1] + 1
            if action.workers_required < required:
                return False, f"Need {required} workers to bump"
        
        # Check electricity cost (only if actually moving)
        if len(action.path) > 1:
            electricity_cost = len(action.path) - 1
            if player.electricity < electricity_cost:
                return False, f"Need {electricity_cost} electricity"
        
        # Allow no movement if excavate or dock is specified
        if len(action.path) == 0 and not (action.excavate or action.dock):
            return False, "Must specify movement, excavation, or docking"
        
        return True, None
    
    def _validate_toggle_lock(self, action: ToggleLockAction, player) -> Tuple[bool, Optional[str]]:
        """Validate lock toggle."""
        if player.available_workers < 1:
            return False, "No workers available"
        
        if action.lock_x not in self.game.board.locks:
            return False, "Invalid lock position"
        
        return True, None
    
    def _validate_load_rocket(self, action: LoadRocketAction, player) -> Tuple[bool, Optional[str]]:
        """Validate rocket loading."""
        if player.available_workers < 1:
            return False, "No workers available"
        
        # Check if player is at a rocket
        vessel_pos = self.game.board.vessel_positions.get(player.id)
        if not vessel_pos:
            return False, "Vessel not placed"
        
        rocket = self.game.board.rockets[vessel_pos.x]
        if not rocket or rocket.is_complete():
            return False, "No rocket or already complete"
        
        # Check if player has resources
        for resource in action.resources:
            if not player.cargo_bay.has(resource):
                return False, f"Don't have {resource.value}"
        
        return True, None
    
    def _validate_use_diesel(self, action: UseDieselAction, player) -> Tuple[bool, Optional[str]]:
        """Validate diesel engine use."""
        if not player.cargo_bay.has(ResourceType.HYDROCARBON):
            return False, "No hydrocarbon available"
        
        vessel_pos = self.game.board.vessel_positions.get(player.id)
        if not vessel_pos:
            return False, "Vessel not placed"
        
        # If pollution_x not specified, check if current position is available
        if action.pollution_x == -1:
            # Check center mineral column of current tile
            current_mineral_x = vessel_pos.x * 3 + 1
            if self.game.board.atmosphere.get(current_mineral_x, 0) > 0:
                return False, "Current position already has pollution - specify another reachable position"
        else:
            # Check if specified position is reachable (same water level)
            current_water_level = self.game.board.get_water_level_at_x(vessel_pos.x * 3 + 1)
            target_water_level = self.game.board.get_water_level_at_x(action.pollution_x)
            
            if current_water_level != target_water_level:
                return False, "Target position not reachable (different water level)"
            
            # Check if target position already has pollution
            if self.game.board.atmosphere.get(action.pollution_x, 0) > 0:
                return False, "Target position already has pollution"
        
        return True, None


class ActionExecutor:
    """Executes validated actions."""
    
    def __init__(self, game):
        self.game = game
    
    def execute(self, action: Action) -> Dict[str, Any]:
        """
        Execute an action and return results.
        """
        executors = {
            ActionType.PASS: self._execute_pass,
            ActionType.BASIC_INCOME: self._execute_basic_income,
            ActionType.HIRE_WORKER: self._execute_hire_worker,
            ActionType.SPECIAL_ELECTION: self._execute_special_election,
            ActionType.MOVE_VESSEL: self._execute_move_vessel,
            ActionType.MOVE_SUBMERSIBLE: self._execute_move_submersible,
            ActionType.TOGGLE_LOCK: self._execute_toggle_lock,
            ActionType.LOAD_ROCKET: self._execute_load_rocket,
            ActionType.USE_DIESEL: self._execute_use_diesel,
        }
        
        executor = executors.get(action.action_type)
        if not executor:
            return {"success": False, "error": "Unknown action type"}
        
        return executor(action)
    
    def _execute_pass(self, action: PassAction) -> Dict[str, Any]:
        """Execute pass action."""
        player = self.game.get_player(action.player_id)
        player.passed = True
        return {"success": True, "message": f"{player.name} passed"}
    
    def _execute_basic_income(self, action: BasicIncomeAction) -> Dict[str, Any]:
        """Execute basic income action."""
        player = self.game.get_player(action.player_id)
        player.place_workers(1)
        player.add_money(2)
        return {
            "success": True, 
            "message": f"{player.name} took $2 basic income",
            "immediate_action": True
        }
    
    def _execute_hire_worker(self, action: HireWorkerAction) -> Dict[str, Any]:
        """Execute hire worker action."""
        player = self.game.get_player(action.player_id)
        player.place_workers(1)
        
        if player.hire_worker():
            return {
                "success": True,
                "message": f"{player.name} hired a worker"
            }
        
        return {"success": False, "error": "Failed to hire worker"}
    
    def _execute_special_election(self, action: SpecialElectionAction) -> Dict[str, Any]:
        """Execute special election action."""
        player = self.game.get_player(action.player_id)
        
        # Bump existing placement if any
        current = self.game.worker_placements.get("special_election")
        if current and current[0] != player.id:
            other_player = self.game.get_player(current[0])
            other_player.recall_workers(current[1])
        
        # Place workers
        player.place_workers(action.workers_required)
        self.game.worker_placements["special_election"] = (player.id, action.workers_required)
        
        # Update first player marker
        for p in self.game.players:
            p.has_first_player_marker = (p.id == player.id)
        
        self.game.player_order.set_first_player(player.id)
        
        return {
            "success": True,
            "message": f"{player.name} took first player marker"
        }
    
    def _execute_move_vessel(self, action: MoveVesselAction) -> Dict[str, Any]:
        """Execute vessel movement."""
        player = self.game.get_player(action.player_id)
        
        if self.game.board.move_vessel(player.id, action.new_x):
            return {
                "success": True,
                "message": f"{player.name} moved vessel to x={action.new_x}"
            }
        
        return {"success": False, "error": "Invalid vessel movement"}
    
    def _execute_move_submersible(self, action: MoveSubmersibleAction) -> Dict[str, Any]:
        """Execute submersible movement."""
        player = self.game.get_player(action.player_id)
        sub_name = action.submersible_name
        
        # Handle worker placement and bumping
        current = self.game.worker_placements.get(f"sub_{sub_name}")
        if current and current[0] != player.id:
            other_player = self.game.get_player(current[0])
            other_player.recall_workers(current[1])
        
        player.place_workers(action.workers_required)
        self.game.worker_placements[f"sub_{sub_name}"] = (player.id, action.workers_required)
        
        result = {
            "success": True,
            "message": f"{player.name} took control of submersible {sub_name}",
        }
        
        # Move submersible if path is provided
        if len(action.path) > 0:
            # Pay electricity cost
            electricity_cost = max(0, len(action.path) - 1)
            player.use_electricity(electricity_cost)
            
            # Move submersible and collect resources
            collected = self.game.board.move_submersible(sub_name, action.path)
            
            # Give $1 per resource collected
            player.add_money(len(collected))
            
            result["message"] = f"{player.name} moved submersible {sub_name}"
            result["resources_collected"] = [r.value for r in collected]
        
        # Get current submersible position for excavate/dock
        sub = self.game.board.submersibles[sub_name]
        current_pos = sub.position if sub else None
        
        # Check for excavation
        if action.excavate and current_pos:
            deposit_info = self.game.board.get_deposit_below(current_pos)
            if deposit_info:
                deposit_idx, deposit = deposit_info
                
                if sub.has_space():
                    # Excavate
                    sub.load(deposit.resource_type)
                    track_pos = deposit.excavate(player.id)
                    
                    if track_pos is not None:
                        vp = VP_EXCAVATION_TRACK[min(track_pos, len(VP_EXCAVATION_TRACK)-1)]
                        player.add_victory_points(vp)
                        result["excavated"] = deposit.resource_type.value
                        result["vp_earned"] = vp
                        
                        # Special bonus at certain track positions
                        if track_pos == 1:  # Second position
                            # Add a resource of choice to cargo bay
                            # For simplicity, give a random resource
                            import random
                            bonus_resource = random.choice(list(ResourceType))
                            player.cargo_bay.add(bonus_resource)
                            result["bonus_resource"] = bonus_resource.value
                        elif track_pos == 3:  # Fourth position
                            # Technology card (simplified)
                            tech_card = f"Technology_{len(player.technology_cards) + 1}"
                            discarded = player.add_technology_card(tech_card)
                            result["technology_gained"] = tech_card
                            if discarded:
                                result["technology_discarded"] = discarded
        
        # Check for docking
        if action.dock and self.game.board.is_submersible_below_vessel(sub_name, player.id):
            # Dock and transfer cargo
            cargo = sub.cargo.get_all()
            cost = sum(cargo.values()) * DOCK_COST_PER_CUBE
            
            if player.spend_money(cost):
                for resource_type, count in cargo.items():
                    for _ in range(count):
                        sub.cargo.transfer_to(player.cargo_bay, resource_type)
                
                result["docked"] = True
                result["cargo_transferred"] = cargo
            else:
                result["dock_failed"] = f"Not enough money (need ${cost})"
        
        return result
    
    def _execute_toggle_lock(self, action: ToggleLockAction) -> Dict[str, Any]:
        """Execute lock toggle."""
        player = self.game.get_player(action.player_id)
        player.place_workers(1)
        
        # Allow other players to move (simplified - no toll collection in this version)
        new_state = self.game.board.toggle_lock(action.lock_x)
        
        return {
            "success": True,
            "message": f"{player.name} {'opened' if new_state else 'closed'} lock at x={action.lock_x}",
            "immediate_action": True
        }
    
    def _execute_load_rocket(self, action: LoadRocketAction) -> Dict[str, Any]:
        """Execute rocket loading."""
        player = self.game.get_player(action.player_id)
        player.place_workers(1)
        
        vessel_pos = self.game.board.vessel_positions[player.id]
        rocket = self.game.board.rockets[vessel_pos.x]
        
        # Load resources and calculate VP
        vp_earned = 0
        for i, resource in enumerate(action.resources):
            if rocket.load(resource):
                player.cargo_bay.remove(resource)
                vp_idx = min(i, len(VP_ROCKET_LOADING) - 1)
                vp_earned += VP_ROCKET_LOADING[vp_idx]
        
        player.add_victory_points(vp_earned)
        
        result = {
            "success": True,
            "message": f"{player.name} loaded {len(action.resources)} resources",
            "vp_earned": vp_earned
        }
        
        # Check if rocket is complete
        if rocket.is_complete():
            rocket.completed_by = player.id
            player.launch_rocket(rocket.name)
            
            # Award technology card (simplified - random selection)
            tech_card = f"Technology_{len(player.technology_cards) + 1}"
            discarded = player.add_technology_card(tech_card)
            
            result["rocket_launched"] = rocket.name
            result["technology_gained"] = tech_card
            if discarded:
                result["technology_discarded"] = discarded
        
        return result
    
    def _execute_use_diesel(self, action: UseDieselAction) -> Dict[str, Any]:
        """Execute diesel engine use."""
        player = self.game.get_player(action.player_id)
        
        if player.use_diesel_engine():
            # Add to atmosphere at specified position (or current if not specified)
            vessel_pos = self.game.board.vessel_positions[player.id]
            
            # If no position specified, use center mineral column of current tile
            if action.pollution_x == -1:
                pollution_x = vessel_pos.x * 3 + 1
            else:
                pollution_x = action.pollution_x
            
            self.game.board.add_to_atmosphere(pollution_x)
            
            return {
                "success": True,
                "message": f"{player.name} used diesel engine for 6 electricity, placing pollution at mineral column {pollution_x}"
            }
        
        return {"success": False, "error": "Failed to use diesel engine"}
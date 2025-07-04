"""Main game controller for Lineae."""

from typing import List, Optional, Dict, Tuple
from .constants import (
    GamePhase, MAX_ROUNDS, MIN_PLAYERS, MAX_PLAYERS,
    Position, ResourceType
)
from .board import Board
from .player import Player, PlayerOrder
from .actions import Action, ActionValidator, ActionExecutor

class Game:
    """Main game controller."""
    
    def __init__(self, player_names: List[str]):
        """Initialize a new game with given player names."""
        if not MIN_PLAYERS <= len(player_names) <= MAX_PLAYERS:
            raise ValueError(f"Must have {MIN_PLAYERS}-{MAX_PLAYERS} players")
        
        # Initialize players
        self.players: List[Player] = []
        for i, name in enumerate(player_names):
            self.players.append(Player(i, name, len(player_names)))
        
        # Initialize board
        self.board = Board()
        
        # Initialize game state
        self.current_round = 0
        self.current_phase = GamePhase.SUNLIGHT
        self.player_order = PlayerOrder(self.players)
        self.game_over = False
        
        # Track worker placements
        self.worker_placements: Dict[str, Tuple[int, int]] = {}  # action -> (player_id, workers)
        
        # Initialize validators and executors
        self.validator = ActionValidator(self)
        self.executor = ActionExecutor(self)
        
        # Action history for logging
        self.action_history: List[Dict] = []
    
    def setup_game(self, vessel_positions: Dict[int, int]) -> None:
        """Set up the game board and initial player positions.
        
        Args:
            vessel_positions: Dict mapping player_id to x position choice
        """
        self.board.setup_board()
        
        # Place vessels based on player choices
        for player_id, pos_x in vessel_positions.items():
            position = Position(pos_x, 0)
            self.board.place_vessel(player_id, position)
            
            player = self.get_player(player_id)
            if player:
                player.vessel_position = position
                
                # Give setup bonus resource from deposit below
                deposit_idx = pos_x // 2
                if deposit_idx < len(self.board.deposits):
                    deposit = self.board.deposits[deposit_idx]
                    if deposit:
                        player.cargo_bay.add(deposit.setup_bonus)
    
    def start_new_round(self) -> bool:
        """
        Start a new round. Returns False if game should end.
        """
        self.current_round += 1
        
        # Check end conditions
        if self.current_round > MAX_ROUNDS:
            self.game_over = True
            return False
        
        # Check if all rockets launched
        rockets_remaining = sum(1 for r in self.board.rockets if r and not r.completed_by)
        if rockets_remaining == 0:
            self.game_over = True
            return False
        
        # Reset for new round
        self.current_phase = GamePhase.SUNLIGHT
        self.player_order.reset_for_new_round()
        self.worker_placements.clear()
        
        return True
    
    def execute_sunlight_phase(self) -> Dict[str, int]:
        """
        Execute sunlight phase. Returns electricity generated per player.
        """
        electricity_generated = {}
        
        for player in self.players:
            vessel_pos = self.board.vessel_positions.get(player.id)
            if vessel_pos:
                # Get electricity considering pollution
                electricity = self.board.get_electricity_at_position(vessel_pos.x)
                player.add_electricity(electricity)
                electricity_generated[player.name] = electricity
            else:
                electricity_generated[player.name] = 0
        
        self.current_phase = GamePhase.ACTION
        return electricity_generated
    
    def get_current_player(self) -> Optional[Player]:
        """Get the current player for action phase."""
        if self.current_phase != GamePhase.ACTION:
            return None
        return self.player_order.get_current_player()
    
    def execute_action(self, action: Action) -> Dict:
        """
        Validate and execute a player action.
        Returns result dictionary.
        """
        # Validate action
        is_valid, error = self.validator.validate(action)
        if not is_valid:
            return {"success": False, "error": error}
        
        # Execute action
        result = self.executor.execute(action)
        
        # Log action
        self.action_history.append({
            "round": self.current_round,
            "player": action.player_id,
            "action": action.action_type.name,
            "result": result
        })
        
        # Check for immediate action
        if not result.get("immediate_action", False):
            # Move to next player
            next_player = self.player_order.next_turn()
            if not next_player:
                # All players have passed
                self.current_phase = GamePhase.CLEANUP
        
        return result
    
    def execute_cleanup_phase(self) -> None:
        """Execute cleanup phase."""
        # Advance Jupiter
        self.board.advance_jupiter()
        
        # Dissolve minerals
        self.board.dissolve_minerals()
        
        # Reset workers
        for player in self.players:
            player.reset_workers()
        
        self.current_phase = GamePhase.SUNLIGHT
    
    def calculate_final_scores(self) -> Dict[str, int]:
        """Calculate final scores at game end."""
        final_scores = {}
        
        for player in self.players:
            # Add end-game VP
            end_game_vp = player.calculate_end_game_vp()
            player.add_victory_points(end_game_vp)
            
            final_scores[player.name] = {
                "victory_points": player.victory_points,
                "money": player.money,
                "resources": player.cargo_bay.total(),
                "rockets_launched": len(player.launched_rockets),
                "technology_cards": len(player.technology_cards)
            }
        
        return final_scores
    
    def get_winner(self) -> Optional[Player]:
        """Determine the winner of the game."""
        if not self.game_over:
            return None
        
        # Sort by VP, then by rockets launched as tiebreaker
        sorted_players = sorted(
            self.players,
            key=lambda p: (p.victory_points, len(p.launched_rockets)),
            reverse=True
        )
        
        return sorted_players[0]
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get player by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_valid_actions(self, player_id: int) -> List[str]:
        """Get list of valid action types for a player."""
        player = self.get_player(player_id)
        if not player:
            return []
        
        if player.passed:
            return []
        
        valid_actions = ["PASS"]
        
        # Check basic actions
        if player.available_workers > 0:
            valid_actions.extend(["BASIC_INCOME", "TOGGLE_LOCK"])
            
            if player.can_hire_worker()[0]:
                valid_actions.append("HIRE_WORKER")
            
            valid_actions.append("SPECIAL_ELECTION")
            
            # Check if at a rocket
            vessel_pos = self.board.vessel_positions.get(player_id)
            if vessel_pos:
                rocket = self.board.rockets[vessel_pos.x]
                if rocket and not rocket.is_complete() and player.cargo_bay.total() > 0:
                    valid_actions.append("LOAD_ROCKET")
            
            # Submersibles
            if player.electricity > 0:
                valid_actions.append("MOVE_SUBMERSIBLE")
        
        # Vessel movement (free)
        valid_actions.append("MOVE_VESSEL")
        
        return valid_actions
    
    def get_game_state(self) -> Dict:
        """Get complete game state for display/logging."""
        return {
            "round": self.current_round,
            "phase": self.current_phase.value,
            "current_player": self.get_current_player().name if self.get_current_player() else None,
            "players": [p.get_state() for p in self.players],
            "board": self.board.get_board_state(),
            "game_over": self.game_over
        }
    
    def get_game_summary(self) -> Dict:
        """Get game summary for logging."""
        return {
            "total_rounds": self.current_round,
            "total_actions": len(self.action_history),
            "rockets_launched": sum(1 for r in self.board.rockets if r and r.completed_by is not None),
            "final_scores": self.calculate_final_scores() if self.game_over else None,
            "winner": self.get_winner().name if self.get_winner() else None
        }
"""Unit tests for actions module."""

import pytest
from lineae.core.game import Game
from lineae.core.constants import Position, ResourceType
from lineae.core.actions import (
    PassAction, BasicIncomeAction, HireWorkerAction,
    SpecialElectionAction, MoveVesselAction, MoveSubmersibleAction,
    ToggleLockAction, LoadRocketAction, UseDieselAction,
    ActionValidator, ActionExecutor
)

class TestActions:
    """Test action classes."""
    
    def test_pass_action(self):
        """Test pass action creation."""
        action = PassAction(0)
        assert action.player_id == 0
        assert action.workers_required == 0
    
    def test_basic_income_action(self):
        """Test basic income action."""
        action = BasicIncomeAction(1)
        assert action.player_id == 1
        assert action.workers_required == 1
    
    def test_move_vessel_action(self):
        """Test move vessel action."""
        action = MoveVesselAction(0, 5)
        assert action.player_id == 0
        assert action.new_x == 5
        assert action.workers_required == 0  # Free action
    
    def test_move_submersible_action(self):
        """Test move submersible action."""
        path = [Position(1, 1), Position(1, 2)]
        action = MoveSubmersibleAction(0, "A", path, 2)
        assert action.player_id == 0
        assert action.submersible_name == "A"
        assert action.path == path
        assert action.workers_required == 2


class TestActionValidator:
    """Test action validation."""
    
    def setup_method(self):
        """Set up test game."""
        self.game = Game(["Alice", "Bob"])
        self.game.setup_game()
        self.game.start_new_round()
        self.game.execute_sunlight_phase()
        self.validator = self.game.validator
    
    def test_validate_pass(self):
        """Test pass action validation."""
        # Valid pass
        action = PassAction(0)
        valid, error = self.validator.validate(action)
        assert valid
        
        # Can't pass twice
        self.game.players[0].passed = True
        valid, error = self.validator.validate(action)
        assert not valid
    
    def test_validate_basic_income(self):
        """Test basic income validation."""
        # Valid
        action = BasicIncomeAction(0)
        valid, error = self.validator.validate(action)
        assert valid
        
        # No workers
        self.game.players[0].available_workers = 0
        valid, error = self.validator.validate(action)
        assert not valid
        assert "workers" in error.lower()
    
    def test_validate_hire_worker(self):
        """Test hire worker validation."""
        player = self.game.players[0]
        player.money = 10
        
        # Valid
        action = HireWorkerAction(0)
        valid, error = self.validator.validate(action)
        assert valid
        
        # Not enough money
        player.money = 2
        valid, error = self.validator.validate(action)
        assert not valid
        assert "money" in error.lower()
    
    def test_validate_move_submersible(self):
        """Test submersible movement validation."""
        player = self.game.players[0]
        player.electricity = 5
        
        # Valid move
        path = [Position(1, 1), Position(1, 2)]
        action = MoveSubmersibleAction(0, "A", path)
        valid, error = self.validator.validate(action)
        assert valid
        
        # Not enough electricity
        player.electricity = 0
        valid, error = self.validator.validate(action)
        assert not valid
        assert "electricity" in error.lower()
    
    def test_validate_load_rocket(self):
        """Test rocket loading validation."""
        player = self.game.players[0]
        player.cargo_bay.add(ResourceType.IRON, 2)
        
        # Valid (at rocket position)
        action = LoadRocketAction(0, [ResourceType.IRON])
        valid, error = self.validator.validate(action)
        assert valid
        
        # Don't have resource
        action = LoadRocketAction(0, [ResourceType.SALT])
        valid, error = self.validator.validate(action)
        assert not valid
        assert "Don't have" in error


class TestActionExecutor:
    """Test action execution."""
    
    def setup_method(self):
        """Set up test game."""
        self.game = Game(["Alice", "Bob"])
        self.game.setup_game()
        self.game.start_new_round()
        self.game.execute_sunlight_phase()
        self.executor = self.game.executor
    
    def test_execute_pass(self):
        """Test executing pass action."""
        action = PassAction(0)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert self.game.players[0].passed
    
    def test_execute_basic_income(self):
        """Test executing basic income."""
        player = self.game.players[0]
        initial_money = player.money
        
        action = BasicIncomeAction(0)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert player.money == initial_money + 2
        assert player.available_workers == player.total_workers - 1
        assert result.get("immediate_action")  # Can take another action
    
    def test_execute_hire_worker(self):
        """Test executing hire worker."""
        player = self.game.players[0]
        player.money = 10
        initial_workers = player.total_workers
        
        action = HireWorkerAction(0)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert player.total_workers == initial_workers + 1
        assert player.money == 6  # 10 - 4
    
    def test_execute_special_election(self):
        """Test executing special election."""
        action = SpecialElectionAction(0)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert self.game.players[0].has_first_player_marker
        assert not self.game.players[1].has_first_player_marker
        assert self.game.player_order.first_player_id == 0
    
    def test_execute_move_vessel(self):
        """Test executing vessel movement."""
        action = MoveVesselAction(0, 4)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert self.game.board.vessel_positions[0].x == 4
    
    def test_execute_toggle_lock(self):
        """Test executing lock toggle."""
        lock_x = 1
        initial_state = self.game.board.locks[lock_x]
        
        action = ToggleLockAction(0, lock_x)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert self.game.board.locks[lock_x] != initial_state
        assert result.get("immediate_action")
    
    def test_execute_use_diesel(self):
        """Test executing diesel engine use."""
        player = self.game.players[0]
        player.cargo_bay.add(ResourceType.HYDROCARBON)
        initial_electricity = player.electricity
        
        action = UseDieselAction(0)
        result = self.executor.execute(action)
        
        assert result["success"]
        assert player.electricity == initial_electricity + 6
        assert not player.cargo_bay.has(ResourceType.HYDROCARBON)
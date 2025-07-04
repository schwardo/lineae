"""Unit tests for game module."""

import pytest
from lineae.core.game import Game
from lineae.core.constants import GamePhase, ResourceType
from lineae.core.actions import PassAction, BasicIncomeAction

class TestGame:
    """Test Game class."""
    
    def test_init(self):
        """Test game initialization."""
        # Valid number of players
        game = Game(["Alice", "Bob", "Charlie"])
        assert len(game.players) == 3
        assert game.current_round == 0
        assert game.current_phase == GamePhase.SUNLIGHT
        assert not game.game_over
        
        # Invalid number of players
        with pytest.raises(ValueError):
            Game([])  # Too few
        
        with pytest.raises(ValueError):
            Game(["P1", "P2", "P3", "P4", "P5", "P6"])  # Too many
    
    def test_setup_game(self):
        """Test game setup."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        
        # Board should be set up
        assert len(game.board.submersibles) == 6
        assert len(game.board.deposits) == 4
        assert len(game.board.rockets) == 8
        
        # Players should have vessels placed
        for player in game.players:
            assert player.id in game.board.vessel_positions
            assert player.cargo_bay.total() > 0  # Setup bonus
    
    def test_start_new_round(self):
        """Test starting a new round."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        
        # First round
        assert game.start_new_round()
        assert game.current_round == 1
        assert game.current_phase == GamePhase.SUNLIGHT
        
        # Simulate reaching round 7
        game.current_round = 7
        assert not game.start_new_round()  # Game should end
        assert game.game_over
    
    def test_sunlight_phase(self):
        """Test sunlight phase execution."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        
        # Place vessels in sunlit positions
        game.board.vessel_positions[0].x = 0  # Should get sunlight
        game.board.vessel_positions[1].x = 7  # Blocked by Jupiter
        
        electricity = game.execute_sunlight_phase()
        
        assert game.players[0].electricity > 0
        assert game.players[1].electricity == 0
        assert game.current_phase == GamePhase.ACTION
    
    def test_execute_action_validation(self):
        """Test action validation."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        game.execute_sunlight_phase()
        
        # Valid action
        action = BasicIncomeAction(0)
        result = game.execute_action(action)
        assert result["success"]
        assert game.players[0].money > 3
        
        # Invalid action (player already passed)
        game.players[1].passed = True
        action = BasicIncomeAction(1)
        result = game.execute_action(action)
        assert not result["success"]
    
    def test_cleanup_phase(self):
        """Test cleanup phase."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        
        # Place some workers
        game.players[0].place_workers(2)
        game.players[1].place_workers(1)
        
        initial_jupiter = game.board.jupiter_position
        
        game.execute_cleanup_phase()
        
        # Jupiter should advance
        assert game.board.jupiter_position == initial_jupiter + 1
        
        # Workers should be reset
        assert game.players[0].available_workers == game.players[0].total_workers
        assert game.players[1].available_workers == game.players[1].total_workers
        
        # Phase should reset
        assert game.current_phase == GamePhase.SUNLIGHT
    
    def test_calculate_final_scores(self):
        """Test final score calculation."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        
        # Give players some resources and money
        game.players[0].victory_points = 10
        game.players[0].money = 15  # 3 VP
        game.players[0].cargo_bay.add(ResourceType.IRON, 4)  # 2 VP
        
        game.players[1].victory_points = 8
        game.players[1].money = 8  # 1 VP
        game.players[1].cargo_bay.add(ResourceType.SALT, 2)  # 1 VP
        
        scores = game.calculate_final_scores()
        
        assert scores["Alice"]["victory_points"] == 15  # 10 + 3 + 2
        assert scores["Bob"]["victory_points"] == 10    # 8 + 1 + 1
    
    def test_get_winner(self):
        """Test determining the winner."""
        game = Game(["Alice", "Bob", "Charlie"])
        game.setup_game()
        
        # Game not over yet
        assert game.get_winner() is None
        
        # Set scores and end game
        game.players[0].victory_points = 20
        game.players[1].victory_points = 25
        game.players[2].victory_points = 25
        
        # Tiebreaker: rockets launched
        game.players[1].launched_rockets = ["R1"]
        game.players[2].launched_rockets = ["R1", "R2"]
        
        game.game_over = True
        winner = game.get_winner()
        
        assert winner == game.players[2]  # Charlie wins on tiebreaker
    
    def test_get_valid_actions(self):
        """Test getting valid actions for a player."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        game.execute_sunlight_phase()
        
        player = game.players[0]
        valid = game.get_valid_actions(0)
        
        assert "PASS" in valid
        assert "BASIC_INCOME" in valid
        
        # Give player hydrocarbon
        player.cargo_bay.add(ResourceType.HYDROCARBON)
        valid = game.get_valid_actions(0)
        assert "USE_DIESEL" in valid
        
        # Player passes
        player.passed = True
        valid = game.get_valid_actions(0)
        assert len(valid) == 0
    
    def test_action_history(self):
        """Test that actions are logged."""
        game = Game(["Alice"])
        game.setup_game()
        game.start_new_round()
        game.execute_sunlight_phase()
        
        assert len(game.action_history) == 0
        
        action = BasicIncomeAction(0)
        game.execute_action(action)
        
        assert len(game.action_history) == 1
        assert game.action_history[0]["round"] == 1
        assert game.action_history[0]["player"] == 0
        assert game.action_history[0]["action"] == "BASIC_INCOME"
    
    def test_game_state(self):
        """Test getting game state."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        
        state = game.get_game_state()
        
        assert state["round"] == 1
        assert state["phase"] == GamePhase.SUNLIGHT.value
        assert len(state["players"]) == 2
        assert "board" in state
        assert not state["game_over"]
    
    def test_all_players_pass(self):
        """Test that phase ends when all players pass."""
        game = Game(["Alice", "Bob"])
        game.setup_game()
        game.start_new_round()
        game.execute_sunlight_phase()
        
        # Both players pass
        game.execute_action(PassAction(0))
        assert game.current_phase == GamePhase.ACTION
        
        game.execute_action(PassAction(1))
        assert game.current_phase == GamePhase.CLEANUP
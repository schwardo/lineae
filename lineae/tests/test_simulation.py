"""Unit tests for simulation module."""

import pytest
import json
import tempfile
from pathlib import Path

from lineae.simulation.strategies import (
    RandomStrategy, GreedyStrategy, BalancedStrategy, 
    AggressiveStrategy, create_strategy
)
from lineae.simulation.logger import GameLogger, SimulationAnalyzer
from lineae.simulation.simulator import GameSimulator
from lineae.core.game import Game

class TestStrategies:
    """Test AI strategies."""
    
    def setup_method(self):
        """Set up test game."""
        self.game = Game(["AI1", "AI2"])
        self.game.setup_game()
        self.game.start_new_round()
        self.game.execute_sunlight_phase()
    
    def test_random_strategy(self):
        """Test random strategy."""
        strategy = RandomStrategy()
        assert strategy.name == "Random"
        
        # Should return some action
        action = strategy.choose_action(self.game, 0)
        assert action is not None
    
    def test_greedy_strategy(self):
        """Test greedy strategy."""
        strategy = GreedyStrategy()
        assert strategy.name == "Greedy"
        
        # Give player low money - should prefer basic income
        player = self.game.players[0]
        player.money = 1
        
        action = strategy.choose_action(self.game, 0)
        assert action is not None
    
    def test_balanced_strategy(self):
        """Test balanced strategy."""
        strategy = BalancedStrategy()
        assert strategy.name == "Balanced"
        
        action = strategy.choose_action(self.game, 0)
        assert action is not None
    
    def test_aggressive_strategy(self):
        """Test aggressive strategy."""
        strategy = AggressiveStrategy()
        assert strategy.name == "Aggressive"
        
        action = strategy.choose_action(self.game, 0)
        assert action is not None
    
    def test_create_strategy(self):
        """Test strategy factory."""
        # Valid strategies
        assert isinstance(create_strategy("random"), RandomStrategy)
        assert isinstance(create_strategy("greedy"), GreedyStrategy)
        assert isinstance(create_strategy("balanced"), BalancedStrategy)
        assert isinstance(create_strategy("aggressive"), AggressiveStrategy)
        
        # Invalid strategy
        with pytest.raises(ValueError):
            create_strategy("invalid")


class TestGameLogger:
    """Test game logging."""
    
    def setup_method(self):
        """Set up test logger."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = GameLogger(log_dir=self.temp_dir, log_level="INFO")
    
    def test_log_game_start(self):
        """Test logging game start."""
        self.logger.log_game_start(
            "test123",
            [("Player1", "random"), ("Player2", "greedy")],
            {"max_rounds": 7}
        )
        
        # Check log file exists
        assert self.logger.log_file.exists()
        
        # Read and verify log
        with open(self.logger.log_file) as f:
            log_entry = json.loads(f.readline())
            assert log_entry["event"] == "game_start"
            assert log_entry["game_id"] == "test123"
    
    def test_log_action(self):
        """Test logging player action."""
        self.logger.log_action(
            "test123",
            0,
            "BASIC_INCOME",
            {"workers": 1},
            {"success": True, "message": "Took $2"}
        )
        
        with open(self.logger.log_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["event"] == "player_action":
                    assert entry["player_id"] == 0
                    assert entry["action_type"] == "BASIC_INCOME"
                    assert entry["result"]["success"]
                    break
    
    def test_log_game_end(self):
        """Test logging game end."""
        self.logger.log_game_end(
            "test123",
            {"Player1": {"victory_points": 25}},
            "Player1",
            {"total_rounds": 6, "total_actions": 50}
        )
        
        with open(self.logger.log_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["event"] == "game_end":
                    assert entry["winner"] == "Player1"
                    assert entry["summary"]["total_rounds"] == 6
                    break


class TestSimulationAnalyzer:
    """Test log analysis."""
    
    def test_analyze_logs(self):
        """Test analyzing simulation logs."""
        # Create test log file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # Write test data
        test_logs = [
            {"event": "game_start", "game_id": "g1", "players": [["P1", "random"]], "timestamp": "2024-01-01"},
            {"event": "player_action", "player_id": 0, "action_type": "BASIC_INCOME", "timestamp": "2024-01-01"},
            {"event": "round_start", "round": 1, "timestamp": "2024-01-01"},
            {"event": "game_end", "game_id": "g1", "winner": "P1", "final_scores": {"P1": {"victory_points": 20}}, 
             "summary": {"total_rounds": 5}, "timestamp": "2024-01-01"}
        ]
        
        for log in test_logs:
            temp_file.write(json.dumps(log) + '\n')
        temp_file.close()
        
        # Analyze
        analyzer = SimulationAnalyzer(temp_file.name)
        summary = analyzer.get_summary()
        
        assert summary["total_games"] == 1
        assert summary["completed_games"] == 1
        assert summary["average_rounds"] == 5
        assert "BASIC_INCOME" in summary["action_counts"]
        
        # Clean up
        Path(temp_file.name).unlink()


class TestGameSimulator:
    """Test game simulator."""
    
    def test_simulate_single_game(self):
        """Test simulating a single game."""
        simulator = GameSimulator()
        
        # Quick 2-player game
        configs = [("Random1", "random"), ("Random2", "random")]
        summary = simulator.simulate_game(configs, show_progress=False)
        
        assert "total_rounds" in summary
        assert "total_actions" in summary
        assert "winner" in summary
        assert summary["total_rounds"] <= 7
    
    def test_run_simulations(self):
        """Test running multiple simulations."""
        simulator = GameSimulator()
        
        configs = [("AI1", "random"), ("AI2", "random")]
        results = simulator.run_simulations(3, configs)
        
        assert len(results) == 3
        for result in results:
            assert "total_rounds" in result
    
    def test_tournament(self):
        """Test running a tournament."""
        simulator = GameSimulator()
        
        # Small tournament
        results = simulator.run_tournament(["random", "greedy"], games_per_matchup=2)
        
        assert "strategies" in results
        assert "overall_wins" in results
        assert len(results["matchups"]) > 0
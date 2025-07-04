"""Unit tests for player module."""

import pytest
from lineae.core.player import Player, PlayerOrder
from lineae.core.constants import ResourceType, INITIAL_MONEY, INITIAL_WORKERS

class TestPlayer:
    """Test Player class."""
    
    def test_init(self):
        """Test player initialization."""
        # 3 player game
        player = Player(0, "Alice", 3)
        assert player.id == 0
        assert player.name == "Alice"
        assert player.money == INITIAL_MONEY
        assert player.victory_points == 0
        assert player.electricity == 0
        assert player.total_workers == INITIAL_WORKERS
        assert player.available_workers == INITIAL_WORKERS
        assert not player.passed
        
        # 4+ player game has fewer starting workers
        player2 = Player(1, "Bob", 4)
        assert player2.total_workers == 3
        assert player2.available_workers == 3
    
    def test_money_management(self):
        """Test money operations."""
        player = Player(0, "Test", 2)
        
        player.add_money(5)
        assert player.money == INITIAL_MONEY + 5
        
        assert player.spend_money(3)
        assert player.money == INITIAL_MONEY + 2
        
        assert not player.spend_money(100)  # Not enough
        assert player.money == INITIAL_MONEY + 2
        
        with pytest.raises(ValueError):
            player.add_money(-1)
        
        with pytest.raises(ValueError):
            player.spend_money(-1)
    
    def test_victory_points(self):
        """Test victory point management."""
        player = Player(0, "Test", 2)
        
        player.add_victory_points(5)
        assert player.victory_points == 5
        
        player.add_victory_points(3)
        assert player.victory_points == 8
    
    def test_electricity_management(self):
        """Test electricity operations."""
        player = Player(0, "Test", 2)
        
        player.add_electricity(6)
        assert player.electricity == 6
        
        player.add_electricity(10)  # Should cap at 9
        assert player.electricity == 9
        
        assert player.use_electricity(4)
        assert player.electricity == 5
        
        assert not player.use_electricity(6)  # Not enough
        assert player.electricity == 5
    
    def test_worker_management(self):
        """Test worker placement and recall."""
        player = Player(0, "Test", 3)
        
        assert player.place_workers(2)
        assert player.available_workers == 2
        
        player.recall_workers(1)
        assert player.available_workers == 3
        
        assert not player.place_workers(5)  # Too many
        
        player.reset_workers()
        assert player.available_workers == 4
        
        with pytest.raises(ValueError):
            player.place_workers(0)
    
    def test_hire_worker(self):
        """Test hiring new workers."""
        player = Player(0, "Test", 2)
        player.money = 20  # Ensure enough money
        
        # First hire costs $4
        can_hire, cost = player.can_hire_worker()
        assert can_hire
        assert cost == 4
        
        assert player.hire_worker()
        assert player.total_workers == 5
        assert player.money == 16
        
        # Second hire costs $5
        assert player.hire_worker()
        assert player.total_workers == 6
        assert player.money == 11
        
        # Can't hire if no money
        player.money = 0
        can_hire, cost = player.can_hire_worker()
        assert not can_hire
        assert not player.hire_worker()
    
    def test_technology_cards(self):
        """Test technology card management."""
        player = Player(0, "Test", 2)
        
        discarded = player.add_technology_card("Tech1")
        assert discarded is None
        assert len(player.technology_cards) == 1
        
        player.add_technology_card("Tech2")
        assert len(player.technology_cards) == 2
        
        # Third card should cause discard
        discarded = player.add_technology_card("Tech3")
        assert discarded == "Tech1"
        assert len(player.technology_cards) == 2
        assert "Tech3" in player.technology_cards
    
    def test_diesel_engine(self):
        """Test using diesel engine."""
        player = Player(0, "Test", 2)
        
        # No hydrocarbon
        assert not player.use_diesel_engine()
        
        # Add hydrocarbon
        player.cargo_bay.add(ResourceType.HYDROCARBON)
        assert player.use_diesel_engine()
        assert player.electricity == 6
        assert player.cargo_bay.count(ResourceType.HYDROCARBON) == 0
    
    def test_end_game_vp(self):
        """Test end game victory point calculation."""
        player = Player(0, "Test", 2)
        
        # Money to VP
        player.money = 12  # $12 = 2 VP
        assert player.calculate_end_game_vp() == 2
        
        # Resources to VP
        player.cargo_bay.add(ResourceType.IRON, 4)  # 2 pairs = 2 VP
        player.cargo_bay.add(ResourceType.SALT, 3)  # 1 pair = 1 VP
        assert player.calculate_end_game_vp() == 5


class TestPlayerOrder:
    """Test PlayerOrder class."""
    
    def test_init(self):
        """Test player order initialization."""
        players = [Player(i, f"P{i}", 3) for i in range(3)]
        order = PlayerOrder(players)
        
        assert order.current_player_index == 0
        assert order.first_player_id == 0
        assert order.get_current_player() == players[0]
    
    def test_next_turn(self):
        """Test moving to next player."""
        players = [Player(i, f"P{i}", 3) for i in range(3)]
        order = PlayerOrder(players)
        
        # Move through players
        assert order.next_turn() == players[1]
        assert order.next_turn() == players[2]
        assert order.next_turn() == players[0]  # Wrap around
    
    def test_next_turn_with_passed_players(self):
        """Test next turn skips passed players."""
        players = [Player(i, f"P{i}", 3) for i in range(3)]
        order = PlayerOrder(players)
        
        # Player 1 passes
        players[1].passed = True
        
        assert order.next_turn() == players[2]  # Skip player 1
        assert order.next_turn() == players[0]
        
        # All pass
        players[0].passed = True
        players[2].passed = True
        assert order.next_turn() is None
    
    def test_set_first_player(self):
        """Test setting first player."""
        players = [Player(i, f"P{i}", 3) for i in range(3)]
        order = PlayerOrder(players)
        
        order.set_first_player(2)
        assert order.first_player_id == 2
        assert order.current_player_index == 2
    
    def test_reset_for_new_round(self):
        """Test resetting for new round."""
        players = [Player(i, f"P{i}", 3) for i in range(3)]
        order = PlayerOrder(players)
        
        # Pass all players and change first player
        for p in players:
            p.passed = True
        order.set_first_player(1)
        
        order.reset_for_new_round()
        
        # All players should be un-passed
        for p in players:
            assert not p.passed
        
        # Should start with first player
        assert order.current_player_index == 1
    
    def test_reverse_order(self):
        """Test getting reverse turn order."""
        players = [Player(i, f"P{i}", 3) for i in range(4)]
        order = PlayerOrder(players)
        
        # Normal order: 0, 1, 2, 3
        # Reverse: 3, 2, 1, 0
        reverse = order.get_reverse_order()
        assert [p.id for p in reverse] == [3, 2, 1, 0]
        
        # Change first player to 2
        order.set_first_player(2)
        # Order would be: 2, 3, 0, 1
        # Reverse: 1, 0, 3, 2
        reverse = order.get_reverse_order()
        assert [p.id for p in reverse] == [1, 0, 3, 2]
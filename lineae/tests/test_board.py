"""Unit tests for board module."""

import pytest
from lineae.core.board import Board, OceanSpace
from lineae.core.constants import Position, ResourceType, BOARD_WIDTH, BOARD_HEIGHT
from lineae.core.resources import Submersible

class TestOceanSpace:
    """Test OceanSpace class."""
    
    def test_init(self):
        """Test ocean space initialization."""
        pos = Position(3, 5)
        space = OceanSpace(pos)
        
        assert space.position == pos
        assert space.resource is None
        assert space.submersible is None
        assert not space.has_water
    
    def test_is_empty(self):
        """Test empty space check."""
        space = OceanSpace(Position(0, 0))
        assert space.is_empty()
        
        space.resource = ResourceType.IRON
        assert not space.is_empty()
        
        space.resource = None
        space.submersible = Submersible("A")
        assert not space.is_empty()
    
    def test_can_enter(self):
        """Test if submersible can enter space."""
        space = OceanSpace(Position(0, 0))
        assert space.can_enter()
        
        # Can't enter with resource
        space.resource = ResourceType.SALT
        assert not space.can_enter()
        
        # Can't enter with submersible
        space.resource = None
        space.submersible = Submersible("B")
        assert not space.can_enter()
    
    def test_add_remove_resource(self):
        """Test adding and removing resources."""
        space = OceanSpace(Position(2, 3))
        
        assert space.add_resource(ResourceType.SULFUR)
        assert space.resource == ResourceType.SULFUR
        
        # Can't add when occupied
        assert not space.add_resource(ResourceType.IRON)
        assert space.resource == ResourceType.SULFUR
        
        # Remove resource
        removed = space.remove_resource()
        assert removed == ResourceType.SULFUR
        assert space.resource is None


class TestBoard:
    """Test Board class."""
    
    def test_init(self):
        """Test board initialization."""
        board = Board()
        
        # Check ocean grid
        assert len(board.ocean) == BOARD_WIDTH * BOARD_HEIGHT
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                assert Position(x, y) in board.ocean
        
        # Check components
        assert len(board.submersibles) == 6
        assert len(board.rockets) == 8
        assert len(board.deposits) == 4
        assert board.jupiter_position == 0
    
    def test_setup_board(self):
        """Test board setup."""
        board = Board()
        board.setup_board()
        
        # Submersibles should be placed
        for name, sub in board.submersibles.items():
            assert sub.position is not None
            space = board.ocean[sub.position]
            assert space.submersible == sub
        
        # Deposits should be created
        for deposit in board.deposits:
            assert deposit is not None
        
        # Initial resources should be placed
        resources_placed = sum(1 for space in board.ocean.values() if space.resource)
        assert resources_placed >= 4  # At least one per deposit
        
        # Rockets should be generated
        for rocket in board.rockets:
            assert rocket is not None
            assert len(rocket.required_resources) >= 2
    
    def test_place_submersible(self):
        """Test placing submersibles."""
        board = Board()
        board.setup_board()
        
        sub = board.submersibles["A"]
        old_pos = sub.position
        new_pos = Position(4, 4)
        
        # Ensure new position is empty
        board.ocean[new_pos].resource = None
        board.ocean[new_pos].submersible = None
        
        assert board.place_submersible("A", new_pos)
        assert sub.position == new_pos
        assert board.ocean[new_pos].submersible == sub
        assert board.ocean[old_pos].submersible is None
    
    def test_move_submersible_collect_resources(self):
        """Test moving submersible and collecting resources."""
        board = Board()
        board.setup_board()
        
        # Place resources in path
        pos1 = Position(2, 2)
        pos2 = Position(2, 3)
        board.ocean[pos1].resource = ResourceType.IRON
        board.ocean[pos2].resource = ResourceType.SALT
        
        # Clear submersible from positions
        board.ocean[pos1].submersible = None
        board.ocean[pos2].submersible = None
        
        # Move submersible through resources
        collected = board.move_submersible("A", [pos1, pos2])
        
        assert ResourceType.IRON in collected
        assert ResourceType.SALT in collected
        assert board.ocean[pos1].resource is None
        assert board.ocean[pos2].resource is None
        assert board.submersibles["A"].position == pos2
    
    def test_toggle_lock(self):
        """Test toggling locks."""
        board = Board()
        
        # All locks start closed
        for lock_x in board.locks:
            assert not board.locks[lock_x]
        
        # Toggle a lock
        assert board.toggle_lock(1)  # Returns new state (True = open)
        assert board.locks[1]
        
        # Toggle back
        assert not board.toggle_lock(1)
        assert not board.locks[1]
    
    def test_vessel_placement_and_movement(self):
        """Test vessel placement and movement."""
        board = Board()
        
        # Place vessel
        assert board.place_vessel(0, Position(3, 0))
        assert board.vessel_positions[0].x == 3
        
        # Can't place at non-surface
        assert not board.place_vessel(1, Position(3, 5))
        
        # Move vessel
        assert board.move_vessel(0, 5)
        assert board.vessel_positions[0].x == 5
        
        # Can't move out of bounds
        assert not board.move_vessel(0, -1)
        assert not board.move_vessel(0, 8)
    
    def test_sunlight_positions(self):
        """Test getting sunlit positions."""
        board = Board()
        
        # Initially all positions get sun (Jupiter at far right)
        sunlit = board.get_sunlight_positions()
        assert len(sunlit) >= 6
        
        # Advance Jupiter
        board.jupiter_position = 2
        sunlit = board.get_sunlight_positions()
        assert 7 not in sunlit  # Rightmost positions blocked
        
        # Add atmosphere
        board.add_to_atmosphere(2)
        sunlit = board.get_sunlight_positions()
        assert 2 not in sunlit  # Blocked by hydrocarbon
    
    def test_dissolve_minerals(self):
        """Test mineral dissolution."""
        board = Board()
        board.setup_board()
        
        # Clear bottom row
        for x in range(BOARD_WIDTH):
            board.ocean[Position(x, BOARD_HEIGHT - 1)].resource = None
        
        board.dissolve_minerals()
        
        # Check that minerals were added above deposits
        minerals_added = 0
        for i, deposit in enumerate(board.deposits):
            if deposit:
                x = i * 2
                # Check column for new resources
                for y in range(BOARD_HEIGHT):
                    if board.ocean[Position(x, y)].resource == deposit.resource_type:
                        minerals_added += 1
        
        assert minerals_added > 0
    
    def test_get_deposit_below(self):
        """Test getting deposit below position."""
        board = Board()
        board.setup_board()
        
        # Position at ocean floor above deposit
        pos = Position(0, BOARD_HEIGHT - 1)
        deposit_info = board.get_deposit_below(pos)
        assert deposit_info is not None
        assert deposit_info[0] == 0  # First deposit
        
        # Position not at ocean floor
        pos = Position(0, 5)
        assert board.get_deposit_below(pos) is None
        
        # Position at odd x-coordinate (no deposit)
        pos = Position(1, BOARD_HEIGHT - 1)
        assert board.get_deposit_below(pos) is None
    
    def test_submersible_at_surface(self):
        """Test checking if submersible is at surface."""
        board = Board()
        board.setup_board()
        
        # Place submersible at surface with water
        surface_pos = Position(2, 0)
        board.ocean[surface_pos].has_water = True
        board.place_submersible("A", surface_pos)
        
        assert board.is_submersible_at_surface("A")
        
        # Move to non-surface
        deep_pos = Position(2, 5)
        board.place_submersible("A", deep_pos)
        assert not board.is_submersible_at_surface("A")
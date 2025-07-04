"""Unit tests for resources module."""

import pytest
from lineae.core.resources import ResourcePool, Submersible, Rocket, MineralDeposit
from lineae.core.constants import ResourceType

class TestResourcePool:
    """Test ResourcePool class."""
    
    def test_init(self):
        """Test resource pool initialization."""
        pool = ResourcePool()
        assert pool.total() == 0
        for resource_type in ResourceType:
            assert pool.count(resource_type) == 0
    
    def test_add_resources(self):
        """Test adding resources."""
        pool = ResourcePool()
        pool.add(ResourceType.IRON, 3)
        assert pool.count(ResourceType.IRON) == 3
        assert pool.total() == 3
        
        pool.add(ResourceType.SALT, 2)
        assert pool.count(ResourceType.SALT) == 2
        assert pool.total() == 5
    
    def test_add_negative_raises_error(self):
        """Test that adding negative amount raises error."""
        pool = ResourcePool()
        with pytest.raises(ValueError):
            pool.add(ResourceType.IRON, -1)
    
    def test_remove_resources(self):
        """Test removing resources."""
        pool = ResourcePool()
        pool.add(ResourceType.IRON, 5)
        
        assert pool.remove(ResourceType.IRON, 3)
        assert pool.count(ResourceType.IRON) == 2
        
        assert not pool.remove(ResourceType.IRON, 3)  # Not enough
        assert pool.count(ResourceType.IRON) == 2
    
    def test_has_resources(self):
        """Test checking if pool has resources."""
        pool = ResourcePool()
        pool.add(ResourceType.SILICA, 3)
        
        assert pool.has(ResourceType.SILICA, 2)
        assert pool.has(ResourceType.SILICA, 3)
        assert not pool.has(ResourceType.SILICA, 4)
        assert not pool.has(ResourceType.IRON, 1)
    
    def test_transfer_resources(self):
        """Test transferring resources between pools."""
        pool1 = ResourcePool()
        pool2 = ResourcePool()
        
        pool1.add(ResourceType.SULFUR, 5)
        assert pool1.transfer_to(pool2, ResourceType.SULFUR, 3)
        
        assert pool1.count(ResourceType.SULFUR) == 2
        assert pool2.count(ResourceType.SULFUR) == 3
        
        # Try to transfer more than available
        assert not pool1.transfer_to(pool2, ResourceType.SULFUR, 3)
        assert pool1.count(ResourceType.SULFUR) == 2
        assert pool2.count(ResourceType.SULFUR) == 3
    
    def test_clear(self):
        """Test clearing all resources."""
        pool = ResourcePool()
        pool.add(ResourceType.IRON, 3)
        pool.add(ResourceType.SALT, 2)
        
        pool.clear()
        assert pool.total() == 0
        assert pool.count(ResourceType.IRON) == 0
        assert pool.count(ResourceType.SALT) == 0


class TestSubmersible:
    """Test Submersible class."""
    
    def test_init(self):
        """Test submersible initialization."""
        sub = Submersible("A", capacity=3)
        assert sub.name == "A"
        assert sub.capacity == 3
        assert sub.cargo.total() == 0
        assert sub.position is None
    
    def test_load_cargo(self):
        """Test loading cargo."""
        sub = Submersible("B", capacity=3)
        
        assert sub.load(ResourceType.IRON)
        assert sub.cargo.count(ResourceType.IRON) == 1
        
        assert sub.load(ResourceType.IRON)
        assert sub.load(ResourceType.SALT)
        assert sub.cargo.total() == 3
        
        # Try to load when full
        assert not sub.load(ResourceType.SULFUR)
        assert sub.cargo.total() == 3
    
    def test_unload_cargo(self):
        """Test unloading cargo."""
        sub = Submersible("C")
        sub.load(ResourceType.IRON)
        sub.load(ResourceType.IRON)
        sub.load(ResourceType.SALT)
        
        assert sub.unload(ResourceType.IRON)
        assert sub.cargo.count(ResourceType.IRON) == 1
        
        assert not sub.unload(ResourceType.SULFUR)  # Don't have
        
        cargo = sub.unload_all()
        assert cargo[ResourceType.IRON] == 1
        assert cargo[ResourceType.SALT] == 1
        assert sub.cargo.total() == 0
    
    def test_space_checks(self):
        """Test space availability checks."""
        sub = Submersible("D", capacity=2)
        
        assert sub.has_space()
        assert sub.is_empty()
        
        sub.load(ResourceType.IRON)
        assert sub.has_space()
        assert not sub.is_empty()
        
        sub.load(ResourceType.SALT)
        assert not sub.has_space()
        assert not sub.is_empty()


class TestRocket:
    """Test Rocket class."""
    
    def test_init(self):
        """Test rocket initialization."""
        requirements = {
            ResourceType.IRON: 2,
            ResourceType.SILICA: 1
        }
        rocket = Rocket("Test Rocket", requirements, 0)
        
        assert rocket.name == "Test Rocket"
        assert rocket.position == 0
        assert rocket.loaded_resources.total() == 0
        assert not rocket.is_complete()
    
    def test_load_resources(self):
        """Test loading resources onto rocket."""
        requirements = {
            ResourceType.IRON: 2,
            ResourceType.SALT: 1
        }
        rocket = Rocket("Mars Mission", requirements, 3)
        
        # Load valid resources
        assert rocket.load(ResourceType.IRON)
        assert rocket.load(ResourceType.IRON)
        assert not rocket.load(ResourceType.IRON)  # Already have 2
        
        assert rocket.load(ResourceType.SALT)
        assert rocket.is_complete()
        
        # Try to load resource not needed
        assert not rocket.load(ResourceType.SULFUR)
    
    def test_progress(self):
        """Test getting loading progress."""
        requirements = {
            ResourceType.IRON: 2,
            ResourceType.SILICA: 1
        }
        rocket = Rocket("Station Alpha", requirements, 2)
        
        progress = rocket.get_progress()
        assert progress[ResourceType.IRON.value]["needed"] == 2
        assert progress[ResourceType.IRON.value]["loaded"] == 0
        
        rocket.load(ResourceType.IRON)
        progress = rocket.get_progress()
        assert progress[ResourceType.IRON.value]["loaded"] == 1


class TestMineralDeposit:
    """Test MineralDeposit class."""
    
    def test_init(self):
        """Test mineral deposit initialization."""
        deposit = MineralDeposit(ResourceType.IRON, ResourceType.SALT)
        assert deposit.resource_type == ResourceType.IRON
        assert deposit.setup_bonus == ResourceType.SALT
        assert len(deposit.excavation_track) == 0
        assert deposit.can_excavate()
    
    def test_excavation(self):
        """Test excavation mechanics."""
        deposit = MineralDeposit(ResourceType.SILICA, ResourceType.SILICA)
        
        # First player excavates
        pos = deposit.excavate(0)
        assert pos == 0
        assert len(deposit.excavation_track) == 1
        
        # Same player excavates again (advances)
        pos = deposit.excavate(0)
        assert pos == 1
        
        # Different player excavates
        pos = deposit.excavate(1)
        assert pos == 0  # Gets first available position
        
        # Fill up track
        for i in range(3):
            deposit.excavate(0)
        
        # Track should be full for player 0
        pos = deposit.excavate(0)
        assert pos is None
        
        # But other players can still excavate
        assert deposit.can_excavate()
    
    def test_excavation_track_limit(self):
        """Test that excavation track has proper limits."""
        deposit = MineralDeposit(ResourceType.HYDROCARBON, ResourceType.IRON)
        
        # Fill track with different players
        for i in range(5):
            pos = deposit.excavate(i)
            assert pos == i
        
        # Track is now full
        assert not deposit.can_excavate()
        pos = deposit.excavate(5)
        assert pos is None
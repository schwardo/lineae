"""Resource management for Lineae game."""

from typing import Dict, List, Optional
from collections import defaultdict
import random
from .constants import ResourceType

class ResourcePool:
    """Manages a collection of resources."""
    
    def __init__(self):
        self.resources: Dict[ResourceType, int] = defaultdict(int)
    
    def add(self, resource_type: ResourceType, amount: int = 1) -> None:
        """Add resources to the pool."""
        if amount < 0:
            raise ValueError("Cannot add negative amount")
        self.resources[resource_type] += amount
    
    def remove(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Remove resources from the pool. Returns True if successful."""
        if amount < 0:
            raise ValueError("Cannot remove negative amount")
        if self.resources[resource_type] >= amount:
            self.resources[resource_type] -= amount
            return True
        return False
    
    def has(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Check if pool has at least the specified amount of a resource."""
        return self.resources[resource_type] >= amount
    
    def count(self, resource_type: ResourceType) -> int:
        """Get count of a specific resource type."""
        return self.resources[resource_type]
    
    def total(self) -> int:
        """Get total number of all resources."""
        return sum(self.resources.values())
    
    def clear(self) -> None:
        """Remove all resources."""
        self.resources.clear()
    
    def transfer_to(self, other: 'ResourcePool', resource_type: ResourceType, 
                   amount: int = 1) -> bool:
        """Transfer resources to another pool. Returns True if successful."""
        if self.remove(resource_type, amount):
            other.add(resource_type, amount)
            return True
        return False
    
    def get_all(self) -> Dict[ResourceType, int]:
        """Get all resources as a dictionary."""
        return dict(self.resources)
    
    def __repr__(self) -> str:
        items = [f"{r.value}: {count}" for r, count in self.resources.items() if count > 0]
        return f"ResourcePool({', '.join(items)})"


class Submersible:
    """Represents a submersible vehicle."""
    
    def __init__(self, name: str, capacity: int = 4):
        self.name = name
        self.capacity = capacity
        self.cargo = ResourcePool()
        self.position = None  # Will be set by board
    
    def load(self, resource_type: ResourceType) -> bool:
        """Load a resource cube if there's space."""
        if self.cargo.total() < self.capacity:
            self.cargo.add(resource_type)
            return True
        return False
    
    def unload(self, resource_type: ResourceType) -> bool:
        """Unload a specific resource cube."""
        return self.cargo.remove(resource_type)
    
    def unload_all(self) -> Dict[ResourceType, int]:
        """Unload all cargo and return what was unloaded."""
        cargo = self.cargo.get_all()
        self.cargo.clear()
        return cargo
    
    def has_space(self) -> bool:
        """Check if submersible has cargo space."""
        return self.cargo.total() < self.capacity
    
    def is_empty(self) -> bool:
        """Check if submersible has no cargo."""
        return self.cargo.total() == 0
    
    def __repr__(self) -> str:
        return f"Submersible({self.name}, cargo={self.cargo.total()}/{self.capacity})"


class Rocket:
    """Represents a rocket card that needs resources."""
    
    def __init__(self, name: str, required_resources: Dict[ResourceType, int], 
                 position: int):
        self.name = name
        self.required_resources = required_resources
        self.loaded_resources = ResourcePool()
        self.position = position
        self.completed_by = None
        self.wildcard_filled = False  # Track if wildcard slot is used
        self.wildcard_resource = None  # Track what resource is in wildcard slot
    
    def load(self, resource_type: ResourceType) -> bool:
        """Load a resource cube onto the rocket."""
        # Check if this specific resource type is still needed
        needed = self.required_resources.get(resource_type, 0)
        loaded = self.loaded_resources.count(resource_type)
        
        # Subtract wildcard if it contains this resource type
        if self.wildcard_resource == resource_type:
            loaded -= 1
        
        if loaded < needed:
            self.loaded_resources.add(resource_type)
            return True
        elif not self.wildcard_filled:
            # Use wildcard slot
            self.loaded_resources.add(resource_type)
            self.wildcard_filled = True
            self.wildcard_resource = resource_type
            return True
        
        return False
    
    def is_complete(self) -> bool:
        """Check if rocket has all required resources."""
        # Must have exactly 5 cubes total (4 specific + 1 wildcard)
        return self.loaded_resources.total() == 5
    
    def get_progress(self) -> Dict[str, int]:
        """Get loading progress for each resource type."""
        progress = {}
        for resource_type, needed in self.required_resources.items():
            loaded = self.loaded_resources.count(resource_type)
            # Don't count wildcard in specific progress
            if self.wildcard_resource == resource_type:
                loaded -= 1
            progress[resource_type.value] = {
                "loaded": loaded,
                "needed": needed
            }
        # Add wildcard status
        progress["wildcard"] = {
            "loaded": 1 if self.wildcard_filled else 0,
            "needed": 1
        }
        return progress
    
    def __repr__(self) -> str:
        loaded = self.loaded_resources.total()
        return f"Rocket({self.name}, {loaded}/5)"


class MineralDeposit:
    """Represents a mineral deposit tile."""
    
    def __init__(self, resource_type: ResourceType, setup_bonus: ResourceType):
        self.resource_type = resource_type
        self.setup_bonus = setup_bonus
        self.excavation_track = []  # List of player IDs on track
        
        # Excavation type - what resource is excavated (can be different from main type)
        # Choose a random resource type for excavation
        self.excavation_type = random.choice(list(ResourceType))
        
        # Second resource type for alternating pattern
        # Choose a different resource type
        other_types = [t for t in ResourceType if t != resource_type]
        self.secondary_resource_type = random.choice(other_types)
        
    def can_excavate(self) -> bool:
        """Check if deposit can be excavated (track not full)."""
        return len(self.excavation_track) < 5
    
    def excavate(self, player_id: int) -> Optional[int]:
        """
        Excavate the deposit. Returns track position (0-based) if successful.
        Returns None if player is already at max position.
        """
        # Find player's current position
        current_position = None
        for i, pid in enumerate(self.excavation_track):
            if pid == player_id:
                current_position = i
                break
        
        if current_position is None:
            # New to this track
            if self.can_excavate():
                self.excavation_track.append(player_id)
                return 0
        elif current_position < 4:  # Can advance
            # Move player to next position
            self.excavation_track[current_position] = None
            # Find next available position
            for i in range(current_position + 1, 5):
                if i >= len(self.excavation_track):
                    self.excavation_track.append(player_id)
                    return i
                elif self.excavation_track[i] is None:
                    self.excavation_track[i] = player_id
                    return i
        
        return None
    
    def __repr__(self) -> str:
        return f"MineralDeposit({self.resource_type.value}, track={len(self.excavation_track)}/5)"
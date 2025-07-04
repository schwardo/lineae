"""Command-line interface for Lineae game."""

import click
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm

from ..core.game import Game
from ..core.constants import Position, ResourceType, GamePhase
from ..core.actions import (
    PassAction, BasicIncomeAction, HireWorkerAction,
    SpecialElectionAction, MoveVesselAction, MoveSubmersibleAction,
    ToggleLockAction, LoadRocketAction, UseDieselAction
)
from .display import (
    display_game_state, display_action_result, 
    display_final_scores, console
)

class GameCLI:
    """Command-line interface for playing Lineae."""
    
    def __init__(self, game: Game):
        self.game = game
        self.console = console
    
    def run(self) -> None:
        """Run the game loop."""
        self.console.print("[bold green]Welcome to Lineae![/]")
        self.console.print("Compete to extract resources from Europa's ocean!\n")
        
        # Setup game
        self.game.setup_game()
        
        # Game loop
        while not self.game.game_over:
            if not self.game.start_new_round():
                break
            
            self.play_round()
        
        # Show final scores
        display_final_scores(self.game)
    
    def play_round(self) -> None:
        """Play a single round."""
        # Sunlight phase
        self.console.print(f"\n[yellow]☀ SUNLIGHT PHASE - Round {self.game.current_round}[/]")
        electricity = self.game.execute_sunlight_phase()
        for player, amount in electricity.items():
            if amount > 0:
                self.console.print(f"  {player} gains {amount} electricity")
        
        Prompt.ask("\nPress Enter to continue")
        
        # Action phase
        self.play_action_phase()
        
        # Cleanup phase
        self.console.print("\n[blue]🧹 CLEANUP PHASE[/]")
        self.game.execute_cleanup_phase()
        self.console.print("  Jupiter advances")
        self.console.print("  Minerals dissolve from deposits")
        self.console.print("  Workers return")
    
    def play_action_phase(self) -> None:
        """Play the action phase."""
        while self.game.current_phase == GamePhase.ACTION:
            display_game_state(self.game)
            
            current_player = self.game.get_current_player()
            if not current_player:
                break
            
            # Check if this is a human player (for now, all are human)
            action = self.get_player_action(current_player.id)
            
            if action:
                result = self.game.execute_action(action)
                display_action_result(result)
                
                if not result.get("immediate_action", False):
                    Prompt.ask("\nPress Enter to continue")
    
    def get_player_action(self, player_id: int) -> Optional[object]:
        """Get action from player."""
        player = self.game.get_player(player_id)
        valid_actions = self.game.get_valid_actions(player_id)
        
        self.console.print(f"\n[cyan]{player.name}'s turn[/]")
        self.console.print("Available actions:")
        
        action_map = {}
        for i, action_type in enumerate(valid_actions, 1):
            action_map[i] = action_type
            self.console.print(f"  {i}. {action_type.replace('_', ' ').title()}")
        
        choice = IntPrompt.ask("Choose action", choices=[str(i) for i in action_map.keys()])
        action_type = action_map[choice]
        
        # Create appropriate action based on type
        if action_type == "PASS":
            return PassAction(player_id)
        
        elif action_type == "BASIC_INCOME":
            return BasicIncomeAction(player_id)
        
        elif action_type == "HIRE_WORKER":
            return HireWorkerAction(player_id)
        
        elif action_type == "SPECIAL_ELECTION":
            # Check if need to bump
            current = self.game.worker_placements.get("special_election")
            workers_needed = 1
            if current and current[0] != player_id:
                workers_needed = current[1] + 1
                self.console.print(f"Need {workers_needed} workers to bump current holder")
            
            if player.available_workers >= workers_needed:
                return SpecialElectionAction(player_id, workers_needed)
            else:
                self.console.print("[red]Not enough workers![/]")
                return None
        
        elif action_type == "MOVE_VESSEL":
            current_x = self.game.board.vessel_positions[player_id].x
            new_x = IntPrompt.ask(f"Move vessel to position (current: {current_x})", 
                                 choices=[str(i) for i in range(8)])
            return MoveVesselAction(player_id, new_x)
        
        elif action_type == "MOVE_SUBMERSIBLE":
            return self.get_submersible_action(player_id)
        
        elif action_type == "TOGGLE_LOCK":
            # Show available locks
            self.console.print("Available locks:")
            for x, is_open in self.game.board.locks.items():
                state = "open" if is_open else "closed"
                self.console.print(f"  Lock at x={x} ({state})")
            
            lock_x = IntPrompt.ask("Toggle which lock?", 
                                  choices=[str(x) for x in self.game.board.locks.keys()])
            return ToggleLockAction(player_id, lock_x)
        
        elif action_type == "LOAD_ROCKET":
            return self.get_load_rocket_action(player_id)
        
        elif action_type == "USE_DIESEL":
            return UseDieselAction(player_id)
        
        return None
    
    def get_submersible_action(self, player_id: int) -> Optional[MoveSubmersibleAction]:
        """Get submersible movement action."""
        player = self.game.get_player(player_id)
        
        # Show available submersibles
        self.console.print("Available submersibles:")
        for name, sub in sorted(self.game.board.submersibles.items()):
            pos_str = f"({sub.position.x},{sub.position.y})" if sub.position else "None"
            cargo_count = sub.cargo.total()
            
            # Check if controlled by another player
            controller = self.game.worker_placements.get(f"sub_{name}")
            status = ""
            if controller and controller[0] != player_id:
                status = f" [controlled by P{controller[0]}, need {controller[1]+1} workers]"
            
            self.console.print(f"  {name}: pos={pos_str}, cargo={cargo_count}/3{status}")
        
        sub_name = Prompt.ask("Choose submersible", 
                             choices=list(self.game.board.submersibles.keys()))
        
        # Calculate workers needed
        current = self.game.worker_placements.get(f"sub_{sub_name}")
        workers_needed = 1
        if current and current[0] != player_id:
            workers_needed = current[1] + 1
        
        if player.available_workers < workers_needed:
            self.console.print(f"[red]Need {workers_needed} workers![/]")
            return None
        
        # Get movement path
        sub = self.game.board.submersibles[sub_name]
        if not sub.position:
            self.console.print("[red]Submersible has no position![/]")
            return None
        
        self.console.print(f"Current position: ({sub.position.x},{sub.position.y})")
        self.console.print(f"You have {player.electricity} electricity (1 per move after first)")
        
        path = []
        current_pos = sub.position
        max_moves = player.electricity + 1  # First move is free
        
        for i in range(max_moves):
            if i == 0:
                self.console.print(f"\nMove {i+1} (free):")
            else:
                self.console.print(f"\nMove {i+1} (costs 1 electricity):")
            
            # Show valid moves
            valid_moves = []
            directions = [
                ("Up", Position(current_pos.x, current_pos.y - 1)),
                ("Down", Position(current_pos.x, current_pos.y + 1)),
                ("Left", Position(current_pos.x - 1, current_pos.y)),
                ("Right", Position(current_pos.x + 1, current_pos.y)),
                ("Stay", current_pos)
            ]
            
            for direction, pos in directions:
                if 0 <= pos.x < 8 and 0 <= pos.y < 10:
                    space = self.game.board.ocean[pos]
                    if pos == current_pos or space.can_enter() or space.resource:
                        valid_moves.append((direction, pos))
            
            self.console.print("Valid moves:")
            for j, (direction, pos) in enumerate(valid_moves, 1):
                space = self.game.board.ocean[pos]
                info = []
                if space.resource:
                    info.append(f"has {space.resource.value}")
                if pos.y == 9:  # Ocean floor
                    deposit_info = self.game.board.get_deposit_below(pos)
                    if deposit_info:
                        info.append("can excavate")
                if pos.y == 0 and space.has_water:
                    info.append("surface")
                
                info_str = f" ({', '.join(info)})" if info else ""
                self.console.print(f"  {j}. {direction} to ({pos.x},{pos.y}){info_str}")
            
            choice = IntPrompt.ask("Choose move (0 to finish)", 
                                  choices=[str(i) for i in range(len(valid_moves) + 1)])
            
            if choice == 0:
                break
            
            _, new_pos = valid_moves[choice - 1]
            path.append(new_pos)
            current_pos = new_pos
        
        if not path:
            return None
        
        # Create action
        action = MoveSubmersibleAction(player_id, sub_name, path, workers_needed)
        
        # Check for special actions at final position
        final_pos = path[-1]
        
        # Check excavation
        if final_pos.y == 9:
            deposit_info = self.game.board.get_deposit_below(final_pos)
            if deposit_info and sub.has_space():
                if Confirm.ask("Excavate mineral deposit?"):
                    action.excavate = True
        
        # Check docking
        if final_pos.y == 0 and self.game.board.ocean[final_pos].has_water:
            vessel_pos = self.game.board.vessel_positions[player_id]
            if vessel_pos.x == final_pos.x and not sub.is_empty():
                if Confirm.ask(f"Dock with vessel? (costs ${sub.cargo.total()})?"):
                    action.dock = True
        
        return action
    
    def get_load_rocket_action(self, player_id: int) -> Optional[LoadRocketAction]:
        """Get rocket loading action."""
        player = self.game.get_player(player_id)
        vessel_pos = self.game.board.vessel_positions[player_id]
        rocket = self.game.board.rockets[vessel_pos.x]
        
        self.console.print(f"\nRocket: {rocket.name}")
        self.console.print("Requirements:")
        for resource, needed in rocket.required_resources.items():
            loaded = rocket.loaded_resources.count(resource)
            has = player.cargo_bay.count(resource)
            self.console.print(f"  {resource.value}: {loaded}/{needed} (you have {has})")
        
        # Get resources to load
        resources_to_load = []
        
        while True:
            available = []
            for resource in ResourceType:
                if player.cargo_bay.has(resource):
                    needed = rocket.required_resources.get(resource, 0)
                    loaded = rocket.loaded_resources.count(resource)
                    if loaded < needed:
                        available.append(resource)
            
            if not available:
                break
            
            self.console.print("\nAvailable resources to load:")
            for i, resource in enumerate(available, 1):
                self.console.print(f"  {i}. {resource.value}")
            
            choice = IntPrompt.ask("Load which resource? (0 to finish)", 
                                  choices=[str(i) for i in range(len(available) + 1)])
            
            if choice == 0:
                break
            
            resource = available[choice - 1]
            resources_to_load.append(resource)
            
            # Temporarily remove from cargo to check what's left
            player.cargo_bay.remove(resource)
        
        # Restore cargo
        for resource in resources_to_load:
            player.cargo_bay.add(resource)
        
        if resources_to_load:
            return LoadRocketAction(player_id, resources_to_load)
        
        return None


def play_game(player_names: List[str]) -> None:
    """Play a game with the given players."""
    game = Game(player_names)
    cli = GameCLI(game)
    cli.run()
"""Game simulator for running automated Lineae games."""

import uuid
import time
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..core.game import Game
from ..core.constants import GamePhase
from .strategies import Strategy, create_strategy
from .logger import GameLogger

console = Console()

class GameSimulator:
    """Runs automated game simulations."""
    
    def __init__(self, logger: Optional[GameLogger] = None):
        """Initialize simulator with optional logger."""
        self.logger = logger or GameLogger()
        self.console = console
    
    def simulate_game(self, player_configs: List[Tuple[str, str]], 
                     show_progress: bool = False) -> Dict:
        """
        Simulate a single game.
        
        Args:
            player_configs: List of (name, strategy) tuples
            show_progress: Whether to show progress in console
        
        Returns:
            Game summary dictionary
        """
        game_id = str(uuid.uuid4())[:8]
        
        # Create players and strategies
        player_names = [config[0] for config in player_configs]
        strategies = {}
        
        for i, (name, strategy_name) in enumerate(player_configs):
            try:
                strategies[i] = create_strategy(strategy_name)
            except ValueError as e:
                self.logger.log_error(game_id, "strategy_creation", {
                    "player": name,
                    "strategy": strategy_name,
                    "error": str(e)
                })
                raise
        
        # Initialize game
        game = Game(player_names)
        game.setup_game()
        
        # Log game start
        self.logger.log_game_start(game_id, player_configs, {
            "board_size": "8x10",
            "max_rounds": 7,
            "num_players": len(player_names)
        })
        
        if show_progress:
            self.console.print(f"[cyan]Starting game {game_id}[/]")
        
        # Run game
        start_time = time.time()
        
        while not game.game_over:
            if not game.start_new_round():
                break
            
            self._simulate_round(game, game_id, strategies, show_progress)
        
        # Game ended
        elapsed_time = time.time() - start_time
        
        # Calculate final scores
        final_scores = game.calculate_final_scores()
        winner = game.get_winner()
        summary = game.get_game_summary()
        summary["elapsed_time"] = round(elapsed_time, 2)
        
        # Log game end
        self.logger.log_game_end(
            game_id,
            final_scores,
            winner.name if winner else "None",
            summary
        )
        
        if show_progress:
            self.console.print(f"[green]Game {game_id} completed in {elapsed_time:.1f}s[/]")
            if winner:
                self.console.print(f"[yellow]Winner: {winner.name} ({winner.victory_points} VP)[/]")
        
        return summary
    
    def _simulate_round(self, game: Game, game_id: str, 
                       strategies: Dict[int, Strategy], 
                       show_progress: bool) -> None:
        """Simulate a single round."""
        # Log round start
        self.logger.log_round_start(game_id, game.current_round, game.get_game_state())
        
        if show_progress:
            self.console.print(f"\n[blue]Round {game.current_round}[/]")
        
        # Sunlight phase
        electricity_generated = game.execute_sunlight_phase()
        self.logger.log_phase(game_id, "sunlight", {
            "electricity_generated": electricity_generated
        })
        
        # Action phase
        action_count = 0
        while game.current_phase == GamePhase.ACTION:
            current_player = game.get_current_player()
            if not current_player:
                break
            
            # Get AI action
            strategy = strategies[current_player.id]
            
            try:
                action = strategy.choose_action(game, current_player.id)
                
                if action:
                    # Log strategy decision
                    self.logger.log_strategy_decision(
                        game_id,
                        current_player.id,
                        strategy.name,
                        {
                            "action_type": action.action_type.name,
                            "player_state": current_player.get_state()
                        }
                    )
                    
                    # Execute action
                    result = game.execute_action(action)
                    
                    # Log action result
                    self.logger.log_action(
                        game_id,
                        current_player.id,
                        action.action_type.name,
                        {"workers": getattr(action, "workers_required", 0)},
                        result
                    )
                    
                    if show_progress and result.get("success"):
                        self.console.print(f"  {current_player.name}: {result.get('message', 'Action completed')}")
                    
                    action_count += 1
                    
                    # Prevent infinite loops
                    if action_count > 100:
                        self.logger.log_error(game_id, "infinite_loop", {
                            "round": game.current_round,
                            "actions": action_count
                        })
                        break
                else:
                    # No valid action, pass
                    from ..core.actions import PassAction
                    game.execute_action(PassAction(current_player.id))
            
            except Exception as e:
                self.logger.log_error(game_id, "action_error", {
                    "player": current_player.name,
                    "strategy": strategy.name,
                    "error": str(e)
                })
                # Force pass on error
                from ..core.actions import PassAction
                game.execute_action(PassAction(current_player.id))
        
        # Cleanup phase
        game.execute_cleanup_phase()
        self.logger.log_phase(game_id, "cleanup", {
            "jupiter_position": game.board.jupiter_position,
            "minerals_dissolved": True
        })
    
    def run_simulations(self, num_games: int, player_configs: List[Tuple[str, str]], 
                       parallel: bool = False) -> List[Dict]:
        """
        Run multiple game simulations.
        
        Args:
            num_games: Number of games to simulate
            player_configs: List of (name, strategy) tuples
            parallel: Whether to run games in parallel (not implemented)
        
        Returns:
            List of game summaries
        """
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(f"Simulating {num_games} games...", total=num_games)
            
            for i in range(num_games):
                try:
                    summary = self.simulate_game(player_configs, show_progress=False)
                    results.append(summary)
                    progress.update(task, advance=1)
                except Exception as e:
                    self.console.print(f"[red]Error in game {i+1}: {e}[/]")
                    progress.update(task, advance=1)
        
        return results
    
    def run_tournament(self, strategies: List[str], games_per_matchup: int = 10) -> Dict:
        """
        Run a tournament between different strategies.
        
        Args:
            strategies: List of strategy names
            games_per_matchup: Number of games per strategy matchup
        
        Returns:
            Tournament results
        """
        self.console.print(f"[bold]Running tournament with strategies: {', '.join(strategies)}[/]")
        
        results = {
            "strategies": strategies,
            "games_per_matchup": games_per_matchup,
            "matchups": {},
            "overall_wins": {s: 0 for s in strategies}
        }
        
        # Play all strategy combinations
        for i, strat1 in enumerate(strategies):
            for j, strat2 in enumerate(strategies[i:], i):
                if i == j and len(strategies) > 1:
                    continue  # Skip self-play unless only one strategy
                
                matchup_key = f"{strat1}_vs_{strat2}"
                self.console.print(f"\n[cyan]Playing {matchup_key}[/]")
                
                # Create player configs
                if i == j:
                    # Self-play
                    configs = [
                        (f"{strat1}_1", strat1),
                        (f"{strat1}_2", strat1)
                    ]
                else:
                    configs = [
                        (strat1, strat1),
                        (strat2, strat2)
                    ]
                
                # Run games
                matchup_results = {
                    "games": [],
                    "wins": {configs[0][0]: 0, configs[1][0]: 0},
                    "avg_vp": {configs[0][0]: 0, configs[1][0]: 0},
                    "avg_rounds": 0
                }
                
                summaries = self.run_simulations(games_per_matchup, configs)
                
                for summary in summaries:
                    if summary and "winner" in summary:
                        winner = summary["winner"]
                        matchup_results["games"].append({
                            "winner": winner,
                            "rounds": summary["total_rounds"],
                            "final_scores": summary.get("final_scores", {})
                        })
                        
                        # Update wins
                        for player_name in matchup_results["wins"]:
                            if winner == player_name:
                                matchup_results["wins"][player_name] += 1
                                
                                # Update overall wins
                                for strat_name, player in configs:
                                    if player == player_name:
                                        results["overall_wins"][strat_name] += 1
                        
                        matchup_results["avg_rounds"] += summary["total_rounds"]
                
                # Calculate averages
                if summaries:
                    matchup_results["avg_rounds"] /= len(summaries)
                
                results["matchups"][matchup_key] = matchup_results
        
        # Print summary
        self.console.print("\n[bold green]Tournament Results:[/]")
        for strategy, wins in results["overall_wins"].items():
            total_games = sum(len(m["games"]) for m in results["matchups"].values() 
                            if strategy in m["wins"])
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            self.console.print(f"  {strategy}: {wins} wins ({win_rate:.1f}%)")
        
        return results


def run_quick_simulation(num_players: int = 3, strategy: str = "random") -> None:
    """Run a quick simulation with the given parameters."""
    # Create player configs
    configs = [(f"Player_{i+1}", strategy) for i in range(num_players)]
    
    # Run simulation
    simulator = GameSimulator()
    summary = simulator.simulate_game(configs, show_progress=True)
    
    console.print("\n[bold]Game Summary:[/]")
    console.print(f"  Total rounds: {summary['total_rounds']}")
    console.print(f"  Total actions: {summary['total_actions']}")
    console.print(f"  Rockets launched: {summary['rockets_launched']}")
    
    if summary.get("final_scores"):
        console.print("\n[bold]Final Scores:[/]")
        for player, score in summary["final_scores"].items():
            console.print(f"  {player}: {score['victory_points']} VP")
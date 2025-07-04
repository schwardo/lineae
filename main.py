#!/usr/bin/env python3
"""Main entry point for Lineae game."""

import click
from typing import List, Optional

from lineae.cli.game_cli import play_game
from lineae.simulation.simulator import GameSimulator, run_quick_simulation
from lineae.simulation.logger import GameLogger, SimulationAnalyzer

@click.group()
def cli():
    """Lineae - Europa Board Game Implementation"""
    pass

@cli.command()
@click.option('--players', '-p', default=3, help='Number of players (1-5)')
@click.option('--names', '-n', multiple=True, help='Player names')
def play(players: int, names: List[str]):
    """Play an interactive game."""
    if not 1 <= players <= 5:
        click.echo("Error: Number of players must be between 1 and 5")
        return
    
    # Create player names
    player_names = list(names) if names else [f"Player {i+1}" for i in range(players)]
    
    # Ensure we have the right number of names
    if len(player_names) < players:
        for i in range(len(player_names), players):
            player_names.append(f"Player {i+1}")
    elif len(player_names) > players:
        player_names = player_names[:players]
    
    # Start game
    play_game(player_names)

@cli.command()
@click.option('--games', '-g', default=10, help='Number of games to simulate')
@click.option('--players', '-p', default=3, help='Number of players per game')
@click.option('--strategies', '-s', default='random,greedy,balanced', 
              help='Comma-separated list of strategies')
@click.option('--log-level', '-l', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
@click.option('--output', '-o', help='Output file for simulation summary')
def simulate(games: int, players: int, strategies: str, log_level: str, output: Optional[str]):
    """Run game simulations with AI players."""
    # Parse strategies
    strategy_list = [s.strip() for s in strategies.split(',')]
    
    # Validate strategies
    valid_strategies = ['random', 'greedy', 'balanced', 'aggressive']
    for strategy in strategy_list:
        if strategy not in valid_strategies:
            click.echo(f"Error: Invalid strategy '{strategy}'. Valid strategies: {', '.join(valid_strategies)}")
            return
    
    # Create player configs
    configs = []
    for i in range(players):
        strategy = strategy_list[i % len(strategy_list)]
        configs.append((f"{strategy.capitalize()}_{i+1}", strategy))
    
    # Create logger
    logger = GameLogger(log_level=log_level)
    
    # Run simulations
    click.echo(f"Running {games} simulations with {players} players...")
    click.echo(f"Strategies: {', '.join(strategy_list)}")
    click.echo(f"Logging to: {logger.log_file}")
    
    simulator = GameSimulator(logger)
    results = simulator.run_simulations(games, configs)
    
    # Show summary
    completed = len([r for r in results if r])
    click.echo(f"\nCompleted {completed}/{games} games")
    
    if completed > 0:
        avg_rounds = sum(r['total_rounds'] for r in results if r) / completed
        avg_actions = sum(r['total_actions'] for r in results if r) / completed
        total_rockets = sum(r['rockets_launched'] for r in results if r)
        
        click.echo(f"Average rounds: {avg_rounds:.1f}")
        click.echo(f"Average actions: {avg_actions:.1f}")
        click.echo(f"Total rockets launched: {total_rockets}")
    
    # Analyze and save results
    if output and completed > 0:
        analyzer = SimulationAnalyzer(str(logger.log_file))
        analyzer.export_summary(output)
        click.echo(f"\nSummary saved to: {output}")

@cli.command()
@click.option('--strategies', '-s', default='random,greedy,balanced,aggressive',
              help='Comma-separated list of strategies to test')
@click.option('--games-per-matchup', '-g', default=10,
              help='Number of games per strategy matchup')
@click.option('--log-level', '-l', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
def tournament(strategies: str, games_per_matchup: int, log_level: str):
    """Run a tournament between different AI strategies."""
    # Parse strategies
    strategy_list = [s.strip() for s in strategies.split(',')]
    
    # Validate strategies
    valid_strategies = ['random', 'greedy', 'balanced', 'aggressive']
    for strategy in strategy_list:
        if strategy not in valid_strategies:
            click.echo(f"Error: Invalid strategy '{strategy}'. Valid strategies: {', '.join(valid_strategies)}")
            return
    
    # Create logger
    logger = GameLogger(log_level=log_level)
    
    # Run tournament
    simulator = GameSimulator(logger)
    results = simulator.run_tournament(strategy_list, games_per_matchup)
    
    click.echo(f"\nLog file: {logger.log_file}")

@cli.command()
@click.argument('log_file')
@click.option('--output', '-o', help='Output file for analysis results')
def analyze(log_file: str, output: Optional[str]):
    """Analyze simulation results from a log file."""
    try:
        analyzer = SimulationAnalyzer(log_file)
        summary = analyzer.get_summary()
        
        click.echo("\nSimulation Analysis:")
        click.echo(f"Total games: {summary['total_games']}")
        click.echo(f"Completed games: {summary['completed_games']}")
        click.echo(f"Average rounds: {summary['average_rounds']}")
        click.echo(f"Total actions: {summary['total_actions']}")
        
        if summary['win_rates']:
            click.echo("\nWin rates:")
            for player, wins in summary['win_rates'].items():
                rate = (wins / summary['completed_games'] * 100) if summary['completed_games'] > 0 else 0
                click.echo(f"  {player}: {wins} wins ({rate:.1f}%)")
        
        if summary['action_counts']:
            click.echo("\nTop actions:")
            sorted_actions = sorted(summary['action_counts'].items(), 
                                  key=lambda x: x[1], reverse=True)[:5]
            for action, count in sorted_actions:
                click.echo(f"  {action}: {count}")
        
        if output:
            analyzer.export_summary(output)
            click.echo(f"\nAnalysis saved to: {output}")
    
    except FileNotFoundError:
        click.echo(f"Error: Log file '{log_file}' not found")
    except Exception as e:
        click.echo(f"Error analyzing log file: {e}")

@cli.command()
@click.option('--players', '-p', default=3, help='Number of players')
@click.option('--strategy', '-s', default='random',
              type=click.Choice(['random', 'greedy', 'balanced', 'aggressive']))
def quick(players: int, strategy: str):
    """Run a quick simulation with visualization."""
    click.echo(f"Running quick simulation: {players} players with {strategy} strategy")
    run_quick_simulation(players, strategy)

if __name__ == '__main__':
    cli()
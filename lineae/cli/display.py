"""Board display and visualization for CLI."""

from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns

from ..core.constants import RESOURCE_COLORS, RESOURCE_ABBREVIATIONS, ResourceType, BOARD_WIDTH, BOARD_HEIGHT, SUBMERSIBLE_CAPACITY, Position
from ..core.game import Game

console = Console()

# Unicode symbols for better display
SYMBOLS = {
    "water": "≈",
    "lock_open": "⎕",
    "lock_closed": "▣",
    "submersible": "◊",
    "vessel": "⛵",
    "resource": "●",
    "jupiter": "♃",
    "sun": "☀",
    "worker": "♟",
    "money": "$",
    "electricity": "⚡",
    "vp": "★"
}

# Resource color mapping for rich
RICH_COLORS = {
    ResourceType.SILICA: "white",
    ResourceType.SULFUR: "yellow",
    ResourceType.SALT: "cyan",
    ResourceType.IRON: "red",
    ResourceType.HYDROCARBON: "magenta"
}

def display_board(game: Game) -> None:
    """Display the game board."""
    board = game.board
    
    # Create board grid
    grid = []
    
    # Add header row with column numbers
    header = ["Y\\X"]  # Space for row labels
    for x in range(BOARD_WIDTH):
        header.append(f" {x} ")
    grid.append(header)
    
    # Add separator after column numbers
    separator = ["---"]
    for _ in range(BOARD_WIDTH):
        separator.append("---")
    grid.append(separator)
    
    # Add header row with sunlight/Jupiter
    sun_row = ["  "]  # Space for row labels
    for x in range(BOARD_WIDTH):
        if x >= BOARD_WIDTH - 2 - board.jupiter_position:
            sun_row.append(f"[bold yellow]{SYMBOLS['jupiter']}[/]")
        elif board.atmosphere.get(x, 0) > 0:
            sun_row.append(f"[magenta]●[/]")
        else:
            sun_row.append(f"[yellow]{SYMBOLS['sun']}[/]")
    grid.append(sun_row)
    
    # Add separator
    separator = ["---"]
    for _ in range(BOARD_WIDTH):
        separator.append("---")
    grid.append(separator)
    
    # Add ocean rows
    for y in range(BOARD_HEIGHT):
        row = [f" {y} "]  # Add row number
        for x in range(BOARD_WIDTH):
            pos = board.ocean[Position(x, y)]
            cell = ""
            
            # Check for vessel at surface
            if y == 0:
                for player_id, vessel_pos in board.vessel_positions.items():
                    if vessel_pos.x == x:
                        player = game.get_player(player_id)
                        cell += f"[bold]{SYMBOLS['vessel']}[/]"
            
            # Check for water
            if pos.has_water:
                cell += f"[blue]{SYMBOLS['water']}[/]"
            
            # Check for submersible
            if pos.submersible:
                cell += f"[green]{pos.submersible.name}[/]"
            
            # Check for resource
            if pos.resource:
                color = RICH_COLORS[pos.resource]
                cell += f"[{color}]{SYMBOLS['resource']}[/]"
            
            # Check for lock
            if y == 0 and x in board.locks:
                if board.locks[x]:
                    cell += f"[green]{SYMBOLS['lock_open']}[/]"
                else:
                    cell += f"[red]{SYMBOLS['lock_closed']}[/]"
            
            # Pad cell to consistent width and add borders
            cell_content = cell if cell else "   "
            row.append(cell_content)
        grid.append(row)
    
    # Add separator before deposits
    separator = ["---"]
    for _ in range(BOARD_WIDTH):
        separator.append("---")
    grid.append(separator)
    
    # Add deposits at bottom
    deposit_row = ["DEP"]  # Label for deposits
    for i in range(BOARD_WIDTH):
        deposit_idx = i // 2
        if i % 2 == 0 and deposit_idx < len(board.deposits):
            deposit = board.deposits[deposit_idx]
            if deposit:
                color = RICH_COLORS[deposit.resource_type]
                deposit_row.append(f"[{color}]▓▓▓[/]")
            else:
                deposit_row.append("   ")
        else:
            deposit_row.append("   ")
    grid.append(deposit_row)
    
    # Create table with grid lines
    from rich.box import SQUARE
    table = Table(show_header=False, show_edge=True, padding=0, box=SQUARE)
    for _ in range(BOARD_WIDTH + 1):  # +1 for row labels
        table.add_column(width=3)
    
    for row in grid:
        table.add_row(*row)
    
    console.print(Panel(table, title="Ocean Board", border_style="blue"))


def display_rockets(game: Game) -> None:
    """Display rocket cards."""
    rockets_table = Table(title="Rockets", show_header=True)
    rockets_table.add_column("Pos", style="cyan")
    rockets_table.add_column("Name", style="white")
    rockets_table.add_column("Requirements", style="yellow")
    rockets_table.add_column("Progress", style="green")
    
    for i, rocket in enumerate(game.board.rockets):
        if rocket and not rocket.completed_by:
            requirements = []
            for resource, count in rocket.required_resources.items():
                loaded = rocket.loaded_resources.count(resource)
                color = RICH_COLORS[resource]
                abbrev = RESOURCE_ABBREVIATIONS[resource]
                requirements.append(f"[{color}]{abbrev}: {loaded}/{count}[/]")
            
            progress = f"{rocket.loaded_resources.total()}/{sum(rocket.required_resources.values())}"
            rockets_table.add_row(
                str(i),
                rocket.name,
                " ".join(requirements),
                progress
            )
    
    console.print(rockets_table)


def display_player_status(game: Game) -> None:
    """Display all players' status."""
    players_table = Table(title="Players", show_header=True)
    players_table.add_column("Player", style="cyan")
    players_table.add_column("VP", style="yellow")
    players_table.add_column("$", style="green")
    players_table.add_column("⚡", style="blue")
    players_table.add_column("Workers", style="magenta")
    players_table.add_column("Resources", style="white")
    
    for player in game.players:
        # Format resources - show individual cubes
        resources = []
        for resource_type, count in player.cargo_bay.get_all().items():
            if count > 0:
                color = RICH_COLORS[resource_type]
                abbrev = RESOURCE_ABBREVIATIONS[resource_type]
                # Show each cube individually
                for _ in range(count):
                    resources.append(f"[{color}]{abbrev}[/]")
        
        # Add special markers
        markers = []
        if player.has_first_player_marker:
            markers.append("[bold yellow]1st[/]")
        if player.passed:
            markers.append("[dim]Pass[/]")
        
        name = player.name
        if markers:
            name += f" ({' '.join(markers)})"
        
        players_table.add_row(
            name,
            str(player.victory_points),
            str(player.money),
            str(player.electricity),
            f"{player.available_workers}/{player.total_workers}",
            " ".join(resources) if resources else "-"
        )
    
    console.print(players_table)


def display_submersibles(game: Game) -> None:
    """Display submersible status."""
    subs_table = Table(title="Submersibles", show_header=True)
    subs_table.add_column("ID", style="cyan")
    subs_table.add_column("Position", style="white")
    subs_table.add_column("Cargo", style="yellow")
    
    for name, sub in sorted(game.board.submersibles.items()):
        pos = f"({sub.position.x},{sub.position.y})" if sub.position else "None"
        
        cargo = []
        for resource_type, count in sub.cargo.get_all().items():
            if count > 0:
                color = RICH_COLORS[resource_type]
                abbrev = RESOURCE_ABBREVIATIONS[resource_type]
                # Show each cube individually
                for _ in range(count):
                    cargo.append(f"[{color}]{abbrev}[/]")
        # Show empty slots
        empty_slots = SUBMERSIBLE_CAPACITY - sub.cargo.total()
        for _ in range(empty_slots):
            cargo.append("__")
        
        subs_table.add_row(
            name,
            pos,
            " ".join(cargo) if cargo else "Empty"
        )
    
    console.print(subs_table)


def display_mineral_deposits(game: Game) -> None:
    """Display mineral deposit status."""
    deposits_table = Table(title="Mineral Deposits", show_header=True)
    deposits_table.add_column("Pos", style="cyan")
    deposits_table.add_column("Dissolves (x2)", style="white")
    deposits_table.add_column("Excavation", style="yellow")
    deposits_table.add_column("Setup Bonus", style="green")
    deposits_table.add_column("Excavation Track", style="magenta")
    
    for i, deposit in enumerate(game.board.deposits):
        if deposit:
            # Format dissolving resources (2 per round)
            dissolve_color = RICH_COLORS[deposit.resource_type]
            dissolve_abbrev = RESOURCE_ABBREVIATIONS[deposit.resource_type]
            dissolve_str = f"[{dissolve_color}]{dissolve_abbrev} {dissolve_abbrev}[/]"
            
            # Format excavation resource
            excavate_color = RICH_COLORS[deposit.resource_type]
            excavate_abbrev = RESOURCE_ABBREVIATIONS[deposit.resource_type]
            excavate_str = f"[{excavate_color}]{excavate_abbrev}[/]"
            
            # Format setup bonus
            setup_color = RICH_COLORS[deposit.setup_bonus]
            setup_abbrev = RESOURCE_ABBREVIATIONS[deposit.setup_bonus]
            setup_str = f"[{setup_color}]{setup_abbrev}[/]"
            
            # Format excavation track
            track_str = ""
            for pos, player_id in enumerate(deposit.excavation_track):
                if player_id is not None:
                    player = game.get_player(player_id)
                    if player:
                        track_str += f"P{player_id}({pos+1}) "
            
            if not track_str:
                track_str = "Empty"
            else:
                track_str += f"[{len(deposit.excavation_track)}/5]"
            
            deposits_table.add_row(
                f"x={i*2}",
                dissolve_str,
                excavate_str,
                setup_str,
                track_str
            )
    
    console.print(deposits_table)


def display_game_state(game: Game) -> None:
    """Display complete game state."""
    console.clear()
    
    # Game header
    header = f"[bold]Round {game.current_round}/7 - {game.current_phase.value.title()} Phase[/]"
    if game.get_current_player():
        header += f" - [cyan]{game.get_current_player().name}'s Turn[/]"
    console.print(Panel(header, style="bold blue"))
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="board"),
        Layout(name="info", size=15)
    )
    
    # Display components
    display_board(game)
    display_rockets(game)
    
    console.print("\n")
    
    # Display in columns
    display_player_status(game)
    display_submersibles(game)
    display_mineral_deposits(game)


def display_action_result(result: Dict) -> None:
    """Display the result of an action."""
    if result.get("success"):
        console.print(f"[green]✓[/] {result.get('message', 'Action completed')}")
        
        # Show additional details
        if result.get("vp_earned"):
            console.print(f"  [yellow]+{result['vp_earned']} VP[/]")
        if result.get("resources_collected"):
            console.print(f"  [cyan]Collected: {', '.join(result['resources_collected'])}[/]")
        if result.get("rocket_launched"):
            console.print(f"  [bold green]Rocket Launched: {result['rocket_launched']}![/]")
    else:
        console.print(f"[red]✗[/] {result.get('error', 'Action failed')}")


def display_final_scores(game: Game) -> None:
    """Display final game scores."""
    console.clear()
    console.print(Panel("[bold]GAME OVER[/]", style="bold red"))
    
    scores = game.calculate_final_scores()
    
    # Create scores table
    scores_table = Table(title="Final Scores", show_header=True)
    scores_table.add_column("Player", style="cyan")
    scores_table.add_column("Victory Points", style="yellow")
    scores_table.add_column("Money", style="green")
    scores_table.add_column("Resources", style="white")
    scores_table.add_column("Rockets", style="magenta")
    
    # Sort by VP
    sorted_players = sorted(
        game.players,
        key=lambda p: scores[p.name]["victory_points"],
        reverse=True
    )
    
    for i, player in enumerate(sorted_players):
        score_data = scores[player.name]
        
        # Add crown for winner
        name = player.name
        if i == 0:
            name = f"👑 {name}"
        
        scores_table.add_row(
            name,
            str(score_data["victory_points"]),
            f"${score_data['money']}",
            str(score_data["resources"]),
            str(score_data["rockets_launched"])
        )
    
    console.print(scores_table)
    
    winner = game.get_winner()
    if winner:
        console.print(f"\n[bold yellow]🎉 {winner.name} wins with {winner.victory_points} points! 🎉[/]")

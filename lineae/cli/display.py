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
    
    # Add header row with column numbers and locks
    header = ["Y\\X"]  # Space for row labels
    for x in range(BOARD_WIDTH):
        header.append(f" {x} ")
        # Add lock column after positions 2, 8, 14, 20
        if x in [2, 8, 14, 20]:
            header.append(" L ")
    grid.append(header)
    
    # Add separator after column numbers
    separator = ["---"]
    for x in range(BOARD_WIDTH):
        separator.append("---")
        if x in [2, 8, 14, 20]:
            separator.append("---")
    grid.append(separator)
    
    # Add header row with sunlight/Jupiter
    sun_row = ["  "]  # Space for row labels
    for x in range(BOARD_WIDTH):
        if x >= BOARD_WIDTH - 2 - board.jupiter_position:
            sun_row.append(f"[bold yellow]{SYMBOLS['jupiter']}[/]")
        elif board.atmosphere.get(x, 0) > 0:
            # Show pollution count
            count = board.atmosphere.get(x, 0)
            sun_row.append(f"[magenta]●{count}[/]")
        else:
            sun_row.append(f"[yellow]{SYMBOLS['sun']}[/]")
        # Empty lock column
        if x in [2, 8, 14, 20]:
            sun_row.append("   ")
    grid.append(sun_row)
    
    # Add separator
    separator = ["---"]
    for x in range(BOARD_WIDTH):
        separator.append("---")
        if x in [2, 8, 14, 20]:
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
                    # Vessel is at tile column, display at center mineral column
                    vessel_display_x = vessel_pos.x * 3 + 1
                    if vessel_display_x == x:
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
                abbrev = RESOURCE_ABBREVIATIONS[pos.resource]
                cell += f"[{color}]{abbrev}[/]"
            elif pos.submersible is None:
                # Empty mineral space (no resource, no submersible)
                cell += "__"
            
            # Pad cell to consistent width and add borders
            cell_content = cell if cell else "   "
            row.append(cell_content)
            
            # Add lock column if needed
            if x in [2, 8, 14, 20]:
                if y == 0:  # Only show locks at surface
                    if board.locks[x]:
                        row.append(f"[green]{SYMBOLS['lock_open']}[/]")
                    else:
                        row.append(f"[red]{SYMBOLS['lock_closed']}[/]")
                else:
                    row.append("   ")  # Empty for non-surface rows
        grid.append(row)
    
    # Add separator before deposits
    separator = ["---"]
    for x in range(BOARD_WIDTH):
        separator.append("---")
        if x in [2, 8, 14, 20]:
            separator.append("---")
    grid.append(separator)
    
    # Add deposits at bottom
    deposit_row = ["DEP"]  # Label for deposits
    for x in range(BOARD_WIDTH):
        deposit_idx = x // 6
        if deposit_idx < len(board.deposits):
            deposit = board.deposits[deposit_idx]
            if deposit:
                color = RICH_COLORS[deposit.resource_type]
                deposit_row.append(f"[{color}]▓▓▓[/]")
            else:
                deposit_row.append("   ")
        else:
            deposit_row.append("   ")
        # Empty lock column
        if x in [2, 8, 14, 20]:
            deposit_row.append("   ")
    grid.append(deposit_row)
    
    # Create table with grid lines
    from rich.box import SQUARE
    table = Table(show_header=False, show_edge=True, padding=0, box=SQUARE)
    num_cols = BOARD_WIDTH + 1 + 4  # +1 for row labels, +4 for lock columns
    for _ in range(num_cols):
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
            # Show specific requirements
            for resource, count in rocket.required_resources.items():
                loaded = rocket.loaded_resources.count(resource)
                # Don't count wildcard in specific progress
                if rocket.wildcard_resource == resource:
                    loaded -= 1
                color = RICH_COLORS[resource]
                abbrev = RESOURCE_ABBREVIATIONS[resource]
                requirements.append(f"[{color}]{abbrev}: {loaded}/{count}[/]")
            
            # Show wildcard slot
            if rocket.wildcard_filled:
                color = RICH_COLORS[rocket.wildcard_resource]
                abbrev = RESOURCE_ABBREVIATIONS[rocket.wildcard_resource]
                requirements.append(f"[white]Wild: [{color}]{abbrev}[/][/]")
            else:
                requirements.append("[white]Wild: __[/]")
            
            progress = f"{rocket.loaded_resources.total()}/5"
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
            # Format dissolving resources (2 per round - alternating pattern)
            primary_color = RICH_COLORS[deposit.resource_type]
            primary_abbrev = RESOURCE_ABBREVIATIONS[deposit.resource_type]
            secondary_color = RICH_COLORS[deposit.secondary_resource_type]
            secondary_abbrev = RESOURCE_ABBREVIATIONS[deposit.secondary_resource_type]
            dissolve_str = f"[{primary_color}]{primary_abbrev}[/]/[{secondary_color}]{secondary_abbrev}[/] x2"
            
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
                f"x={i*6}-{i*6+5}",
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

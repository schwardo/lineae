# Lineae - Europa Board Game Implementation

A Python implementation of the Lineae board game with command-line interface, automated simulations, and comprehensive testing.

## Overview

Lineae is a strategic board game where players compete as colonists on Europa, extracting minerals from the ocean when breaks in the ice surface (lineae) form. This implementation provides:

- **Command-line gameplay** for 1-5 players
- **AI opponents** with different strategies
- **Game simulations** with structured logging
- **Comprehensive unit tests**

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd lineae

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Play a Game

```bash
# Start an interactive game
python main.py play

# Start a game with AI opponents
python main.py play --players 3 --ai-players 2

# Start a solo game
python main.py play --players 1
```

### Run Simulations

```bash
# Run 100 simulations with random strategies
python main.py simulate --games 100

# Run simulations with specific strategies
python main.py simulate --games 50 --strategies random,greedy,balanced

# Output detailed logs
python main.py simulate --games 10 --log-level DEBUG
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lineae

# Run specific test file
pytest tests/test_game.py
```

## Project Structure

```
lineae/
├── core/               # Core game logic
│   ├── game.py        # Main game controller
│   ├── board.py       # Board state and mechanics
│   ├── player.py      # Player state and resources
│   ├── resources.py   # Resource management
│   ├── actions.py     # Game actions and validation
│   └── constants.py   # Game constants
├── cli/               # Command-line interface
│   ├── game_cli.py    # Interactive game interface
│   └── display.py     # Board visualization
├── simulation/        # Automated simulations
│   ├── simulator.py   # Simulation runner
│   ├── strategies.py  # AI strategies
│   └── logger.py      # Structured logging
└── tests/            # Unit tests
```

## Game Rules

Lineae follows the official board game rules:
- 1-5 players compete over 7 rounds
- Collect resources using submersibles
- Launch rockets for victory points
- Manage workers, electricity, and money
- Strategic water flow management with locks

## Features

### Command-Line Interface
- Interactive player turns
- Visual board representation
- Action validation
- Game state display

### AI Strategies
- **Random**: Makes random valid moves
- **Greedy**: Focuses on immediate resource gains
- **Balanced**: Balances resource collection and rocket launches
- **Aggressive**: Prioritizes rocket completion

### Structured Logging
- JSON-formatted logs for analysis
- Configurable log levels
- Game state tracking
- Action history
- Performance metrics

## Development

### Adding New Features

1. Implement core logic in `core/`
2. Add CLI support in `cli/`
3. Create tests in `tests/`
4. Update documentation

### Running Tests

```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_game.py::test_game_initialization
```

## License

This implementation is based on the Lineae board game. Please refer to the LICENSE file for details.
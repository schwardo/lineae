"""Structured logging for Lineae simulations."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class GameLogger:
    """Structured logger for game simulations."""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """Initialize logger with JSON formatting."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create unique log file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"lineae_sim_{timestamp}.json"
        
        # Configure logger
        self.logger = logging.getLogger("lineae_simulation")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(event)s",
            timestamp=True
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (optional)
        if log_level == "DEBUG":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_game_start(self, game_id: str, players: list, config: Dict[str, Any]) -> None:
        """Log game initialization."""
        self.logger.info(
            "Game started",
            extra={
                "event": "game_start",
                "game_id": game_id,
                "players": players,
                "config": config
            }
        )
    
    def log_round_start(self, game_id: str, round_num: int, 
                       game_state: Dict[str, Any]) -> None:
        """Log round start."""
        self.logger.info(
            "Round started",
            extra={
                "event": "round_start",
                "game_id": game_id,
                "round": round_num,
                "game_state": game_state
            }
        )
    
    def log_phase(self, game_id: str, phase: str, phase_data: Dict[str, Any]) -> None:
        """Log phase execution."""
        self.logger.info(
            f"{phase} phase",
            extra={
                "event": f"phase_{phase}",
                "game_id": game_id,
                "phase": phase,
                "phase_data": phase_data
            }
        )
    
    def log_action(self, game_id: str, player_id: int, action_type: str,
                  action_details: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log player action."""
        self.logger.info(
            "Player action",
            extra={
                "event": "player_action",
                "game_id": game_id,
                "player_id": player_id,
                "action_type": action_type,
                "action_details": action_details,
                "result": result
            }
        )
    
    def log_game_end(self, game_id: str, final_scores: Dict[str, Any],
                    winner: str, game_summary: Dict[str, Any]) -> None:
        """Log game completion."""
        self.logger.info(
            "Game ended",
            extra={
                "event": "game_end",
                "game_id": game_id,
                "final_scores": final_scores,
                "winner": winner,
                "summary": game_summary
            }
        )
    
    def log_error(self, game_id: str, error_type: str, 
                 error_details: Dict[str, Any]) -> None:
        """Log errors during simulation."""
        self.logger.error(
            "Simulation error",
            extra={
                "event": "error",
                "game_id": game_id,
                "error_type": error_type,
                "error_details": error_details
            }
        )
    
    def log_strategy_decision(self, game_id: str, player_id: int, 
                            strategy: str, decision_data: Dict[str, Any]) -> None:
        """Log AI strategy decisions."""
        self.logger.debug(
            "Strategy decision",
            extra={
                "event": "strategy_decision",
                "game_id": game_id,
                "player_id": player_id,
                "strategy": strategy,
                "decision_data": decision_data
            }
        )


class SimulationAnalyzer:
    """Analyze simulation results from logs."""
    
    def __init__(self, log_file: str):
        """Initialize analyzer with log file."""
        self.log_file = Path(log_file)
        self.games = []
        self._parse_logs()
    
    def _parse_logs(self) -> None:
        """Parse JSON logs into structured data."""
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    event = entry.get("event")
                    
                    if event == "game_start":
                        self.games.append({
                            "game_id": entry["game_id"],
                            "players": entry["players"],
                            "start_time": entry["timestamp"],
                            "actions": [],
                            "rounds": 0
                        })
                    
                    elif event == "game_end" and self.games:
                        game = self.games[-1]
                        game["end_time"] = entry["timestamp"]
                        game["final_scores"] = entry["final_scores"]
                        game["winner"] = entry["winner"]
                        game["summary"] = entry["summary"]
                    
                    elif event == "player_action" and self.games:
                        self.games[-1]["actions"].append({
                            "player": entry["player_id"],
                            "action": entry["action_type"],
                            "timestamp": entry["timestamp"]
                        })
                    
                    elif event == "round_start" and self.games:
                        self.games[-1]["rounds"] = entry["round"]
                
                except json.JSONDecodeError:
                    continue
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics from simulations."""
        if not self.games:
            return {}
        
        completed_games = [g for g in self.games if "winner" in g]
        
        # Win rates by player/strategy
        winners = {}
        for game in completed_games:
            winner = game["winner"]
            winners[winner] = winners.get(winner, 0) + 1
        
        # Average game length
        avg_rounds = sum(g.get("rounds", 0) for g in completed_games) / len(completed_games) if completed_games else 0
        
        # Action statistics
        action_counts = {}
        for game in self.games:
            for action in game.get("actions", []):
                action_type = action["action"]
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        return {
            "total_games": len(self.games),
            "completed_games": len(completed_games),
            "average_rounds": round(avg_rounds, 2),
            "win_rates": winners,
            "action_counts": action_counts,
            "total_actions": sum(action_counts.values())
        }
    
    def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific game."""
        for game in self.games:
            if game["game_id"] == game_id:
                return game
        return None
    
    def export_summary(self, output_file: str) -> None:
        """Export summary to JSON file."""
        summary = self.get_summary()
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
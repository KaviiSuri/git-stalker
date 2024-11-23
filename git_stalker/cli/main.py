from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from rich.console import Console
from typer import Typer, Argument, Option

from git_stalker.config import get_github_token
from git_stalker.core import ActivityTracker, GitHubActivitySource
from git_stalker.core.logging import setup_logging

app = Typer()
console = Console()

class ActivityJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Activity objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def activity_to_dict(activity) -> Dict[str, Any]:
    """Convert an activity to a dictionary for JSON serialization."""
    return {
        "source": activity.source,
        "timestamp": activity.timestamp,
        "type": activity.type,
        "details": activity.details,
        "message": activity.message,
    }

@app.command()
def track_activity(
    username: str = Argument(..., help="Username to track"),
    organization: str | None = Option(None, "--org", help="Filter by organization"),
    start_date: str | None = Option(None, "--start-date", help="Start date in YYYY-MM-DD format"),
    end_date: str | None = Option(None, "--end-date", help="End date in YYYY-MM-DD format"),
    output_format: str = Option("pretty", "--output-format", help="Output format (pretty/json)"),
    log_file: str | None = Option(None, "--log-file", help="Path to log file"),
):
    """Track user activity across configured sources."""
    # Setup logging
    log_path = Path(log_file) if log_file else None
    logger = setup_logging(log_file=log_path)
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    try:
        # Initialize tracker and add sources
        tracker = ActivityTracker()
        
        # Add GitHub source with optional organization
        github_token = get_github_token()
        github_source = GitHubActivitySource(token=github_token, organization=organization)
        tracker.add_source(github_source)

        # Get activities
        activities = tracker.get_all_activities(
            username=username,
            start_date=start,
            end_date=end,
        )

        # Display activities
        if output_format == "json":
            # Convert activities to JSON
            activities_json = [activity_to_dict(activity) for activity in activities]
            console.print(json.dumps(activities_json, cls=ActivityJSONEncoder, indent=2))
        else:
            # Pretty print format
            for activity in activities:
                console.print(f"[bold blue]{activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/bold blue]")
                console.print(f"[bold]{activity.source}[/bold]: {activity.message}")
                console.print()
    
    except Exception as e:
        logger.exception(f"Error in track_activity: {str(e)}")
        raise

def main():
    app()

if __name__ == "__main__":
    main() 
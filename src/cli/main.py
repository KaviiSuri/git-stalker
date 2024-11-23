from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from typer import Typer, Argument, Option

from ..config import get_github_token
from ..core import ActivityTracker, GitHubActivitySource
from ..core.logging import setup_logging

app = Typer()
console = Console()

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
        for activity in activities:
            if output_format == "pretty":
                console.print(f"[bold blue]{activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/bold blue]")
                console.print(f"[bold]{activity.source}[/bold]: {activity.message}")
                console.print()
            else:
                console.print(f"[bold]{activity.source}[/bold]: {activity.type}")
                console.print(f"  Time: {activity.timestamp}")
                console.print(f"  Details: {activity.details}\n")
    
    except Exception as e:
        logger.exception(f"Error in track_activity: {str(e)}")
        raise

def main():
    app()

if __name__ == "__main__":
    main() 
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import requests
from dotenv import load_dotenv
from rich.console import Console
from typer import Typer, Argument, Option

app = Typer()
console = Console()

def get_github_token() -> str:
    _ = load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token is missing. Please set it in the .env file.")
    return token

def fetch_github_data(url: str, headers: dict[str, str]) -> dict[str, Any]:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

@app.command()
def track_activity(
    username: str = Argument(..., help="GitHub username"),
    organization: str = Argument(..., help="Organization name"),
    start_date: str | None = Option(None, "--start-date", help="Start date in YYYY-MM-DD format"),
    end_date: str | None = Option(None, "--end-date", help="End date in YYYY-MM-DD format"),
    output_format: str = Option("pretty", "--output-format", help="Output format (pretty/json)")
):
    token = get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").isoformat() + "Z"
    else:
        end_date = datetime.now().isoformat() + "Z"

    if not end_date:
        end_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"

    url = f"https://api.github.com/orgs/{organization}/repos?per_page=100"
    repos = []
    while url:
        response = fetch_github_data(url, headers)
        repos.extend(response)
        if "next" in response.get("links", {}):
            url = response["links"]["next"]["url"]
        else:
            break

    for repo in repos:
        if repo["owner"]["login"] == username:
            console.print(f"[bold]{repo['name']}[/bold]")
            # Add more logic to fetch and display activity here
            break

if __name__ == "__main__":
    app()

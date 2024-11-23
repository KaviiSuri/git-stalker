# Git Stalker

Track GitHub activity for users within organizations.

![Demo](demo/demo.gif)

## Features

- Track user activity within specific organizations
- Filter by date range
- Pretty print or JSON output with links
- Configurable logging
- Multiple output formats (pretty/json)
- Rate limit handling
- Organization-specific activity filtering

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/git-stalker.git
   cd git-stalker
   ```

2. Install dependencies:
   ```sh
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   
   uv pip install -e ".[dev]"
   ```

3. Create a `.env` file with your GitHub token:
   ```
   GITHUB_TOKEN=your_github_token_here
   ```

## Usage

Basic usage:
```sh
# Track all activity
git-stalker username

# Track activity in a specific organization
git-stalker username --org organization

# Filter by date range
git-stalker username --org organization --start-date "2024-01-01" --end-date "2024-02-01"

# Get JSON output with links
git-stalker username --org organization --output-format json
```

## Environment Variables

- `GITHUB_TOKEN`: Your GitHub personal access token
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `GITHUB_RETRY_TOTAL`: Number of retries for failed requests (default: 0)
- `GITHUB_RETRY_BACKOFF`: Backoff factor between retries in seconds (default: 0.1)

## License

MIT


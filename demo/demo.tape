# Output the GIF
Output demo/demo.gif

# Setup terminal
Set FontSize 16
Set Width 1200
Set Height 600
Set Padding 20
Set Shell bash
Set Theme "Catppuccin Frappe"

# Start recording
Type "# Let's track GitHub activity for a user in an organization"
Enter
Sleep 1s

# Show help
Type "uv run git_stalker.py --help"
Enter
Sleep 3s

# Show basic usage
Type "# Track activity for a user"
Enter
Sleep 1s
Type "uv run git_stalker.py meowgorithm --org charmbracelet"
Enter
Sleep 5s

# Show JSON output
Type "# Get JSON output with links"
Enter
Sleep 1s
Type "uv run git_stalker.py meowgorithm --org charmbracelet --output-format json | head -n 20"
Enter
Sleep 4s

# Show date filtering
Type "# Filter by date range"
Enter
Sleep 1s
Type 'uv run git_stalker.py meowgorithm --org charmbracelet --start-date "2024-01-01" --end-date "2024-02-01"'
Enter
Sleep 4s 
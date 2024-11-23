from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import Activity
from .logging import logger
from ..config import get_env_var

class GitHubActivitySource:
    """GitHub implementation of ActivitySource protocol."""
    
    def __init__(self, token: str, organization: Optional[str] = None):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.organization = organization
        self.logger = logger.getChild(self.__class__.__name__)
        
        if organization:
            self.logger.info(f"Initialized GitHub source for organization: {organization}")
        
        # Configure session with optional retries
        self.session = requests.Session()
        
        # Get retry configuration from environment
        retry_total = int(get_env_var("GITHUB_RETRY_TOTAL", "0"))
        retry_backoff = float(get_env_var("GITHUB_RETRY_BACKOFF", "0.1"))
        
        if retry_total > 0:
            retry_strategy = Retry(
                total=retry_total,
                backoff_factor=retry_backoff,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
            
            self.logger.debug(
                f"Configured request retries: total={retry_total}, "
                f"backoff={retry_backoff}"
            )

    def _fetch_github_data(self, url: str) -> dict[str, Any]:
        """Fetch data from GitHub API."""
        self.logger.debug(f"Fetching data from: {url}")
        try:
            response = self.session.get(url, headers=self.headers)
            
            # Log rate limit information
            rate_limit = response.headers.get('X-RateLimit-Remaining', 'unknown')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset', 'unknown')
            self.logger.debug(f"GitHub API rate limit remaining: {rate_limit}")
            
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
                reset_time = datetime.fromtimestamp(int(rate_limit_reset))
                self.logger.error(f"GitHub API rate limit exceeded. Reset time: {reset_time}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching GitHub data: {str(e)}")
            raise
        
    def __del__(self):
        """Cleanup session on object destruction."""
        self.session.close()

    def _simplify_event_details(self, event_type: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify event details based on event type."""
        simplified = {}
        
        try:
            # Get repository name from the event
            repo = event.get("repo", {}).get("name", "unknown")
            payload = event.get("payload", {})
            
            # Base GitHub URL for constructing links
            base_url = "https://github.com"
            repo_url = f"{base_url}/{repo}"
            
            if event_type == "PushEvent":
                ref = payload.get("ref", "unknown")
                branch = ref.replace("refs/heads/", "")
                simplified = {
                    "repository": repo,
                    "repository_url": repo_url,
                    "ref": ref,
                    "commit_count": len(payload.get("commits", [])),
                    "commit_messages": [
                        commit.get("message", "").split("\n")[0]  # First line only
                        for commit in payload.get("commits", [])[:3]  # First 3 commits only
                    ],
                    "compare_url": f"{repo_url}/compare/{payload.get('before', '')}...{payload.get('head', '')}"
                }
            
            elif event_type == "PullRequestEvent":
                pr = payload.get("pull_request", {})
                simplified = {
                    "action": payload.get("action", "unknown"),
                    "title": pr.get("title", "unknown"),
                    "number": pr.get("number", "unknown"),
                    "repository": repo,
                    "repository_url": repo_url,
                    "state": pr.get("state", "unknown"),
                    "url": pr.get("html_url"),
                }
            
            elif event_type == "IssuesEvent":
                issue = payload.get("issue", {})
                simplified = {
                    "action": payload.get("action", "unknown"),
                    "title": issue.get("title", "unknown"),
                    "number": issue.get("number", "unknown"),
                    "repository": repo,
                    "repository_url": repo_url,
                    "url": issue.get("html_url"),
                }
            
            elif event_type == "IssueCommentEvent":
                simplified = {
                    "action": payload.get("action", "unknown"),
                    "issue_number": payload.get("issue", {}).get("number", "unknown"),
                    "repository": repo,
                    "repository_url": repo_url,
                    "comment_fragment": payload.get("comment", {}).get("body", "")[:100] + "...",
                    "url": payload.get("comment", {}).get("html_url"),
                    "issue_url": payload.get("issue", {}).get("html_url"),
                }
            
            elif event_type == "CreateEvent":
                ref_type = payload.get("ref_type", "unknown")
                ref = payload.get("ref", "unknown")
                simplified = {
                    "ref_type": ref_type,
                    "ref": ref,
                    "repository": repo,
                    "repository_url": repo_url,
                    "url": (
                        f"{repo_url}/tree/{ref}" if ref_type == "branch"
                        else f"{repo_url}/releases/tag/{ref}" if ref_type == "tag"
                        else repo_url
                    ),
                }
            
            elif event_type == "DeleteEvent":
                simplified = {
                    "ref_type": payload.get("ref_type", "unknown"),
                    "ref": payload.get("ref", "unknown"),
                    "repository": repo,
                    "repository_url": repo_url,
                }
            
            elif event_type == "WatchEvent":
                simplified = {
                    "action": payload.get("action", "unknown"),
                    "repository": repo,
                    "repository_url": repo_url,
                }
            
            else:
                # For other event types, include basic info
                simplified = {
                    "event_type": event_type,
                    "repository": repo,
                    "repository_url": repo_url,
                }
        except Exception as e:
            self.logger.warning(f"Error simplifying {event_type} event: {str(e)}")
            simplified = {"error": "Failed to process event details"}
        
        return simplified

    def _get_human_readable_message(self, event_type: str, details: Dict[str, Any]) -> str:
        """Generate human readable message for the event."""
        try:
            if event_type == "PushEvent":
                commit_count = details["commit_count"]
                repo = details["repository"]
                branch = details["ref"].replace("refs/heads/", "")
                commit_msg = ""
                if details["commit_messages"]:
                    commit_msg = f": {details['commit_messages'][0]}"
                return f"Pushed {commit_count} commit{'s' if commit_count > 1 else ''} to {repo}/{branch}{commit_msg}"
            
            elif event_type == "PullRequestEvent":
                action = details["action"]
                title = details["title"]
                number = details["number"]
                repo = details["repository"]
                return f"{action.capitalize()} PR #{number} in {repo}: {title}"
            
            elif event_type == "IssuesEvent":
                action = details["action"]
                title = details["title"]
                number = details["number"]
                repo = details["repository"]
                return f"{action.capitalize()} issue #{number} in {repo}: {title}"
            
            elif event_type == "IssueCommentEvent":
                repo = details["repository"]
                number = details["issue_number"]
                comment = details["comment_fragment"]
                return f"Commented on issue #{number} in {repo}: {comment}"
            
            elif event_type == "CreateEvent":
                ref_type = details["ref_type"]
                ref = details["ref"]
                repo = details["repository"]
                return f"Created {ref_type} {ref} in {repo}"
            
            elif event_type == "DeleteEvent":
                ref_type = details["ref_type"]
                ref = details["ref"]
                repo = details["repository"]
                return f"Deleted {ref_type} {ref} in {repo}"
            
            elif event_type == "WatchEvent":
                repo = details["repository"]
                return f"Starred repository {repo}"
            
            else:
                return f"Performed {event_type} on {details.get('repository', 'unknown repository')}"
                
        except Exception as e:
            self.logger.warning(f"Error creating message for {event_type}: {str(e)}")
            return f"Performed {event_type}"

    def validate_credentials(self) -> bool:
        """Validate GitHub token."""
        self.logger.debug("Validating GitHub credentials")
        try:
            self._fetch_github_data("https://api.github.com/user")
            self.logger.info("GitHub credentials validated successfully")
            return True
        except requests.RequestException as e:
            self.logger.error(f"GitHub credential validation failed: {str(e)}")
            return False

    def _is_org_event(self, event: Dict[str, Any]) -> bool:
        """Check if event is related to the configured organization."""
        if not self.organization:
            return True
            
        repo_name = event.get("repo", {}).get("name", "")
        return repo_name.startswith(f"{self.organization}/")

    def get_activities(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Activity]:
        """Get GitHub activities for a user."""
        self.logger.info(f"Fetching GitHub activities for user: {username}")
        if self.organization:
            self.logger.info(f"Filtering for organization: {self.organization}")

        # Convert dates to GitHub API format
        start_date_str = start_date.isoformat() + "Z" if start_date else None
        end_date_str = end_date.isoformat() + "Z" if end_date else None
        
        self.logger.debug(f"Date range: {start_date_str} to {end_date_str}")

        # Fetch events from GitHub API
        url = f"https://api.github.com/users/{username}/events"
        try:
            events_data = self._fetch_github_data(url)
        except Exception as e:
            self.logger.error(f"Failed to fetch GitHub events: {str(e)}")
            raise

        activities = []
        for event in events_data:
            try:
                # Skip events not related to the configured organization
                if not self._is_org_event(event):
                    continue
                    
                simplified_details = self._simplify_event_details(
                    event["type"],
                    event
                )
                
                human_message = self._get_human_readable_message(
                    event["type"],
                    simplified_details
                )
                
                activity = Activity(
                    source="github",
                    timestamp=datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")),
                    type=event["type"],
                    details=simplified_details,
                    message=human_message
                )
                activities.append(activity)
            except Exception as e:
                self.logger.warning(f"Failed to process event: {str(e)}")
                continue

        self.logger.info(f"Retrieved {len(activities)} GitHub activities")
        return activities 
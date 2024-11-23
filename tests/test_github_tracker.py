import pytest
from datetime import datetime
from src.core.github import GitHubActivitySource
from src.core.base import Activity

def test_github_source_initialization():
    token = "dummy_token"
    source = GitHubActivitySource(token)
    assert source.headers["Authorization"] == f"token {token}"
    assert source.headers["Accept"] == "application/vnd.github.v3+json"

@pytest.fixture
def mock_github_source(monkeypatch):
    def mock_fetch_data(*args, **kwargs):
        return [{
            "type": "PushEvent",
            "created_at": "2024-02-20T12:00:00Z",
            "payload": {"commits": [{"message": "test commit"}]}
        }]
    
    source = GitHubActivitySource("dummy_token")
    monkeypatch.setattr(source, "_fetch_github_data", mock_fetch_data)
    return source

def test_github_source_get_activities(mock_github_source):
    activities = mock_github_source.get_activities("testuser")
    assert len(activities) == 1
    assert isinstance(activities[0], Activity)
    assert activities[0].source == "github"
    assert activities[0].type == "PushEvent" 
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol, runtime_checkable
from .logging import logger

@dataclass(frozen=True)
class Activity:
    """Immutable activity data from any source."""
    source: str
    timestamp: datetime
    type: str
    details: Dict[str, Any]
    message: str  # Human readable description of the activity

@runtime_checkable
class ActivitySource(Protocol):
    """Protocol defining the interface for activity sources."""
    
    def get_activities(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Activity]:
        """Get activities for a user within the specified date range."""
        ...

    def validate_credentials(self) -> bool:
        """Validate that the credentials for this source are valid."""
        ...

class ActivityTracker:
    """Main class for tracking activities across multiple sources."""
    
    def __init__(self):
        self.sources: List[ActivitySource] = []
        self.logger = logger.getChild(self.__class__.__name__)

    def add_source(self, source: ActivitySource) -> None:
        """Add a new activity source."""
        self.logger.debug(f"Adding new source: {source.__class__.__name__}")
        
        if not isinstance(source, ActivitySource):
            self.logger.error(f"Invalid source type: {type(source)}")
            raise TypeError(f"Source must implement ActivitySource protocol")
        
        try:
            if source.validate_credentials():
                self.sources.append(source)
                self.logger.info(f"Successfully added source: {source.__class__.__name__}")
            else:
                self.logger.error(f"Invalid credentials for source: {source.__class__.__name__}")
                raise ValueError(f"Invalid credentials for source: {source.__class__.__name__}")
        except Exception as e:
            self.logger.exception(f"Error adding source: {str(e)}")
            raise

    def get_all_activities(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Activity]:
        """Get activities from all sources."""
        self.logger.info(f"Fetching activities for user: {username}")
        self.logger.debug(f"Date range: {start_date} to {end_date}")
        
        activities = []
        for source in self.sources:
            try:
                self.logger.debug(f"Fetching from source: {source.__class__.__name__}")
                source_activities = source.get_activities(username, start_date, end_date)
                activities.extend(source_activities)
                self.logger.debug(
                    f"Retrieved {len(source_activities)} activities from {source.__class__.__name__}"
                )
            except Exception as e:
                self.logger.error(
                    f"Error fetching activities from {source.__class__.__name__}: {str(e)}"
                )
                continue
        
        sorted_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)
        self.logger.info(f"Retrieved total of {len(sorted_activities)} activities")
        return sorted_activities 
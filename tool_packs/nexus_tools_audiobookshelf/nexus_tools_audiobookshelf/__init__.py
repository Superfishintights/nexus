"""Nexus Audiobookshelf tool pack.

Tool modules are discovered lazily by Nexus. Importing this package has no
network or registration side effects.
"""

from .client import AudiobookshelfClient, AudiobookshelfError, get_client

__all__ = ["AudiobookshelfClient", "AudiobookshelfError", "get_client"]

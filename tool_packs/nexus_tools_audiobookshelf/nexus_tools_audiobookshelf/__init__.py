"""Nexus Audiobookshelf tool pack.

Tool modules are discovered lazily by Nexus. Importing this package has no
network or registration side effects.
"""

NEXUS_NAMESPACES = [{"name": "audiobookshelf", "display_name": "Audiobookshelf", "description": "Browse and manage audiobooks, podcasts, libraries, playback sessions, and user progress in Audiobookshelf."}]

from .client import AudiobookshelfClient, AudiobookshelfError, get_client

__all__ = ["AudiobookshelfClient", "AudiobookshelfError", "get_client"]

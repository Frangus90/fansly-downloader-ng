"""OnlyFans Download Functions

Separate download module for OnlyFans scraping.
Currently supports:
- Timeline posts

Future support:
- Messages
- Collections/Vault
- Single posts
"""

from .timeline import download_timeline
from .account import get_creator_account_info

__all__ = [
    'download_timeline',
    'get_creator_account_info',
]

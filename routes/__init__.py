"""Routes package"""
from .auth import auth_ns
from .account import account_ns
from .files import files_ns
from .torrents import torrents_ns
from .vlc import vlc_ns

__all__ = ['auth_ns', 'account_ns', 'files_ns', 'torrents_ns', 'vlc_ns']

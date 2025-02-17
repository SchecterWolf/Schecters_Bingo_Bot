__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio

from functools import wraps
from typing import Callable, TypeVar, Any

# Note: Because the discord bot only runs using a single thread, I cannot WAIT for the game async function
# calls to finish, because this call stack already exist in an asyncio loop
# (initiated within the discord bot lib), and doing so will result in a deadlock.
# Some of the game operations may time out the initial interaction, so run the game calls in a different
# asyncio task.
T = TypeVar("T", bound=Callable[..., Any])
def sync_aware(fn: T) -> Callable[..., None]:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except Exception as e:
            loop = asyncio.get_event_loop()
            asyncio.set_event_loop(loop) # TODO SCH do I need this?
        loop.create_task(fn(*args, **kwargs))
    return wrapper


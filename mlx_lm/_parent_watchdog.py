# Copyright © 2026 Apple Inc.

import logging
import os
import threading
import time


logger = logging.getLogger(__name__)


def parent_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def start_parent_watchdog(
    parent_pid: int,
    poll_interval: float = 2.0,
    _exit=os._exit,
) -> threading.Thread:
    def watch_parent():
        while parent_is_alive(parent_pid):
            time.sleep(poll_interval)
        logger.info("Parent process %s is gone; exiting.", parent_pid)
        _exit(0)

    thread = threading.Thread(
        target=watch_parent,
        name="parent-pid-watchdog",
        daemon=True,
    )
    thread.start()
    return thread

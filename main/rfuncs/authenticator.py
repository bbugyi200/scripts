import logging
import time
from typing import Set

from .types import AccessRecord, AuthStatus


ATTEMPT_LIMIT = 10
ATTEMPT_PERIOD = 10  # In minutes


log = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, server_token: str) -> None:
        self.server_token = server_token
        self.access_records: Set[AccessRecord] = set()

    def check(self, client_addr: str, client_token: str) -> AuthStatus:
        now = time.time()

        for arec in self.access_records.copy():
            if (now - arec.time) > (ATTEMPT_PERIOD * 60):
                self.access_records.remove(arec)

        recent_failed_attempts = [
            arec
            for arec in self.access_records
            if arec.client_addr == client_addr
            and not arec.granted
        ]
        if len(recent_failed_attempts) > ATTEMPT_LIMIT:
            status = AuthStatus.SUSPENDED
        elif client_token == self.server_token:
            status = AuthStatus.GRANTED
        else:
            status = AuthStatus.DENIED

        arec = AccessRecord(client_addr, status == AuthStatus.GRANTED, now)
        log.info(f"Access {status}: {arec}")
        self.access_records.add(arec)

        return status

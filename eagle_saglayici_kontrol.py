"""Thread-safe provider cooldown management."""

import time
import threading
from datetime import timezone
from email.utils import parsedate_to_datetime

import requests


class SaglayiciKontrol:

    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._deadlines = {}
        self._active = set()

    def baslat(self, provider):
        with self._lock:
            if self._clock() < self._deadlines.get(
                provider, 0
            ):
                return False

            if provider in self._active:
                return False

            self._active.add(provider)
            return True

    def bitir(self, provider, delay=0):
        with self._lock:
            if delay > 0:
                self._deadlines[provider] = max(
                    self._deadlines.get(provider, 0),
                    self._clock() + delay
                )

            self._active.discard(provider)

    def kalan(self, provider):
        with self._lock:
            return max(
                0,
                self._deadlines.get(provider, 0)
                - self._clock()
            )


def hata_bekleme(exc):
    if isinstance(exc, requests.exceptions.HTTPError):
        response = exc.response

        if response is None:
            return 0

        status = response.status_code

        if status == 403:
            return 1800

        if status == 429:
            retry = response.headers.get(
                "Retry-After", "300"
            )

            try:
                return max(1, int(retry))
            except (ValueError, TypeError):
                try:
                    dt = parsedate_to_datetime(retry)

                    if dt.tzinfo is None:
                        dt = dt.replace(
                            tzinfo=timezone.utc
                        )

                    return max(
                        1, dt.timestamp() - time.time()
                    )
                except (ValueError, TypeError,
                        OverflowError):
                    return 300

        if 500 <= status <= 599:
            return 60

    if isinstance(
        exc,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        )
    ):
        return 30

    return 0

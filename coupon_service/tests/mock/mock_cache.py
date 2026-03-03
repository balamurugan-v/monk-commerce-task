from unittest.mock import MagicMock

class MockCacheManager:
    """
    A mock implementation of the CacheManager for testing purposes.
    Simulates Redis operations on an in-memory dictionary.
    """
    def __init__(self):
        self._cache = {}
        self.get = MagicMock(side_effect=self._mock_get)
        self.set = MagicMock(side_effect=self._mock_set)
        self.incr = MagicMock(side_effect=self._mock_incr)
        self.decr = MagicMock(side_effect=self._mock_decr)
        self.delete = MagicMock(side_effect=self._mock_delete)

    def _mock_get(self, key: str):
        return self._cache.get(key)

    def _mock_set(self, key: str, value, ex: int = None):
        self._cache[key] = value

    def _mock_incr(self, key: str) -> int:
        self._cache[key] = self._cache.get(key, 0) + 1
        return self._cache[key]

    def _mock_decr(self, key: str) -> int:
        self._cache[key] = self._cache.get(key, 0) - 1
        return self._cache[key]

    def _mock_delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

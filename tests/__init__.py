from libcloud.storage.drivers.dummy import DummyFileObject as BaseDummyFileObject


class DummyFile(BaseDummyFileObject):
    """Add size just for test purpose"""

    def __init__(self, yield_count=5, chunk_len=10):
        super().__init__(yield_count, chunk_len)
        self.size = len(self)
        self.filename = "dummy-file"
        self.content_type = "application/octet-stream"

class DataError(ValueError):
    def __init__(self, code, detail, status=422):
        super().__init__(detail)
        self.code = code
        self.status = status


class CaliberError(DataError):
    """A caliber switch failed while an older formal conclusion must stay open."""

    def __init__(self, code, detail, status=409, preserved=None):
        super().__init__(code, detail, status)
        self.preserved = preserved

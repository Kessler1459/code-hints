class TableNotFound(Exception):
    def __init__(self, message="Database tables are not initialized"):
        super().__init__(message)

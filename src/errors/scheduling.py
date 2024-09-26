class NoSuitableNodeException(Exception):
    """Raise if there are no nodes which match the user's requirements."""


class NoWindowAllocatedException(Exception):
    """Raise if allocating all possible windows fails."""


class JobTooLongException(Exception):
    """Raise if requested runtime exceeds timetable size."""

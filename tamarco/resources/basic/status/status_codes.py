class StatusCodes:
    NOT_STARTED = 0
    CONNECTING = 1
    STARTED = 2
    STOPPING = 3
    STOPPED = 4
    FAILED = 5

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

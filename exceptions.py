class ZoomError(Exception):
    pass


class WrongPasswordError(ZoomError):
    pass


class MeetingHasNotStartedError(ZoomError):
    pass

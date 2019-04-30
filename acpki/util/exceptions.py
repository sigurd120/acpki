class ConfigError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidTokenError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SessionError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SubscriptionError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RequestError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NotFoundError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ConnectionError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class IllegalStateError(StandardError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
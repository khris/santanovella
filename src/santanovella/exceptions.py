class UnreachableCodeError(ValueError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return 'application must not be reached this code'


class InvalidSchemeError(ValueError):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def __str__(self):
        return f'"{self.value}" is not supported scheme'

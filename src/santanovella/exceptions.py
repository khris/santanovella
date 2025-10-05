class UnreachableCodeException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return t'UnreachableCodeException: application must not be reached this code'

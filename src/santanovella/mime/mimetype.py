from typing import MutableMapping


class MimeType:
    type: str = 'text'
    subtype: str = 'plain'
    parameters: MutableMapping[str, str] = None

    def __init__(self, payload: str):
        chunks = payload.split(';')
        if not chunks:
            return

        self.type, self.subtype = chunks[0].split('/')
        self.parameters = {}

        if len(chunks) > 1:
            try:
                for chunk in chunks[1:]:
                    k, v = chunk.split('=', 1)
                    self.parameters[k.strip()] = v.strip()
            except ValueError:
                raise ValueError(f'MIME type parameters should be '
                                 f'"<parameter>=<value>" with ";" '
                                 f'as separator, but {chunks[1:]} is not')

        if self.type == 'text' and 'charset' not in self.parameters:
            self.parameters['charset'] = 'utf-8'

    @property
    def charset(self) -> str:
        if self.type != 'text':
            raise ValueError(f'"charset" parameter is only for "text" type, '
                             f'not "{self.type}"')
        return self.parameters['charset']

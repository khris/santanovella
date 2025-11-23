import importlib
import logging
import pathlib

module_path = pathlib.Path(__file__).parent.absolute()
logger = logging.getLogger(__name__)
for root, _, files in module_path.walk():
    for filename in files:
        if not filename.endswith('.py') or filename == '__init__.py':
            continue
        importlib.import_module(f'.{filename[:-3]}', package=__package__)
        logger.info(f'import {__package__}.{filename[:-3]}')

"""
This module defines public interface of ArgumentParser class.
See test/sample_app.py for example usage.
"""

from .data_types import Arguments, LibraryComponents


class ArgumentParserInterface:

    def parse_arguments(self) -> Arguments:
        """
        Method parses user arguments and returns filled Arguments container
        necessary for proper library integration.
        """
        raise NotImplementedError

    def get_library_components(self) -> LibraryComponents:
        """
        Method returns configured and initialized library components
        ready for use by integrator.
        """
        raise NotImplementedError

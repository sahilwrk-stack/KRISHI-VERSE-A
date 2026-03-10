#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "krishiverse.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed:\n"
            "    pip install Django==4.2.18\n"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

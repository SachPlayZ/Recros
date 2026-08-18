"""Central logging setup: line-buffered stderr so logs appear immediately."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any


class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def resolve_log_level(verbose: bool = False, quiet: bool = False) -> int:
    env = os.environ.get("RECROS_LOG_LEVEL", "").strip().upper()
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    if env in mapping:
        return mapping[env]
    if quiet:
        return logging.WARNING
    if verbose:
        return logging.DEBUG
    return logging.INFO


def configure_logging(
    *,
    level: int | None = None,
    verbose: bool = False,
    quiet: bool = False,
) -> None:
    lvl = level if level is not None else resolve_log_level(verbose, quiet)
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handler = FlushStreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt, datefmt))
    logging.basicConfig(level=lvl, handlers=[handler], force=True)


def add_log_arguments(parser: Any) -> Any:
    parser.add_argument("-v", "--verbose", action="store_true", help="DEBUG logs")
    parser.add_argument("-q", "--quiet", action="store_true", help="Warnings only")
    return parser


def setup_logging_args(args: Any) -> None:
    configure_logging(verbose=args.verbose, quiet=args.quiet)

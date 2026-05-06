# ============================================
# Nexus-Graph AI Service — Structured Logger
# ============================================
# Coloured, timestamped console logger matching
# the gateway's visual style.
# ============================================

import logging
import sys
from datetime import datetime, timezone


class _ColourFormatter(logging.Formatter):
    """Custom formatter with ANSI colours and ISO timestamps."""

    COLOURS = {
        "DEBUG":    "\033[2m",       # dim
        "INFO":     "\033[32m",      # green
        "WARNING":  "\033[33m",      # yellow
        "ERROR":    "\033[31m",      # red
        "EVENT":    "\033[36m",      # cyan
        "GRAPH":    "\033[35m",      # magenta
        "AI":       "\033[34m",      # blue
    }
    RESET = "\033[0m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        level = record.levelname
        colour = self.COLOURS.get(level, self.COLOURS["INFO"])
        msg = record.getMessage()

        # Include extra metadata if present
        meta = ""
        if hasattr(record, "meta") and record.meta:
            meta = f" {self.DIM}{record.meta}{self.RESET}"

        return (
            f"{self.DIM}[{ts}]{self.RESET} "
            f"{colour}{level:<7}{self.RESET} "
            f"{msg}{meta}"
        )


# Register custom log levels
EVENT_LEVEL = 25
GRAPH_LEVEL = 26
AI_LEVEL = 27

logging.addLevelName(EVENT_LEVEL, "EVENT")
logging.addLevelName(GRAPH_LEVEL, "GRAPH")
logging.addLevelName(AI_LEVEL, "AI")


def get_logger(name: str = "nexus-ai") -> logging.Logger:
    """Create or retrieve a structured logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_ColourFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Add convenience methods for custom levels
        def _event(msg, *args, **kwargs):
            meta = kwargs.pop("meta", None)
            logger.log(EVENT_LEVEL, msg, *args, extra={"meta": meta}, **kwargs)

        def _graph(msg, *args, **kwargs):
            meta = kwargs.pop("meta", None)
            logger.log(GRAPH_LEVEL, msg, *args, extra={"meta": meta}, **kwargs)

        def _ai(msg, *args, **kwargs):
            meta = kwargs.pop("meta", None)
            logger.log(AI_LEVEL, msg, *args, extra={"meta": meta}, **kwargs)

        logger.event = _event
        logger.graph = _graph
        logger.ai = _ai

    return logger

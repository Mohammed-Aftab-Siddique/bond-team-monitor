"""
Entry point for the Bond Team Monitor Dynatrace Extension.
"""

from __future__ import annotations

import platform
import logging

from dynatrace_extension import Extension, Status, StatusValue

from . import linux_collector, windows_collector
from .metrics import report

logger = logging.getLogger(__name__)


class BondTeamMonitorExtension(Extension):
    """
    Dynatrace Extension implementation for monitoring
    Linux Bonding and Windows NIC Teaming.
    """

    def initialize(self) -> None:
        """
        Called once when the extension starts.
        """
        logger.info("Initializing Bond Team Monitor extension.")

    def query(self) -> None:
        """
        Collect and report metrics.
        """

        logger.info("Starting collection...")

        members = []

        system = platform.system()

        if system == "Linux":
            logger.info("Running Linux collector.")
            members.extend(linux_collector.collect())

        elif system == "Windows":
            logger.info("Running Windows collector.")
            members.extend(windows_collector.collect())

        else:
            logger.warning("Unsupported operating system: %s", system)

        report(self, members)

    def fastcheck(self) -> Status:
        """
        Verify that the extension is healthy.
        """
        return Status(StatusValue.OK)


def main() -> None:
    """
    Start the extension.
    """
    BondTeamMonitorExtension().run()


if __name__ == "__main__":
    main()

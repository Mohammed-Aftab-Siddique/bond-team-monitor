"""
Metric reporting for the Bond Team Monitor extension.
"""

from __future__ import annotations

from .topology import NetworkMember


def report(extension, members: list[NetworkMember]) -> None:
    """
    Report all collected metrics to Dynatrace.

    Args:
        extension:
            Running Extension instance.

        members:
            Collected network members.
    """

    for member in members:
        dimensions = {
            "group": member.group_name,
            "interface": member.interface_name,
            "ip_address": member.ip_address,
            "mac_address": member.mac_address,
            "operating_system": member.operating_system,
            "duplex": member.duplex,
        }

        extension.report_metric(
            "bond_team.status",
            int(member.status),
            dimensions,
        )

        extension.report_metric(
            "bond_team.active",
            int(member.active),
            dimensions,
        )

        extension.report_metric(
            "bond_team.speed",
            member.speed_mbps,
            dimensions,
        )

        extension.report_metric(
            "bond_team.rx.bytes",
            member.rx_bytes,
            dimensions,
        )

        extension.report_metric(
            "bond_team.tx.bytes",
            member.tx_bytes,
            dimensions,
        )

        extension.report_metric(
            "bond_team.rx.errors",
            member.rx_errors,
            dimensions,
        )

        extension.report_metric(
            "bond_team.tx.errors",
            member.tx_errors,
            dimensions,
        )

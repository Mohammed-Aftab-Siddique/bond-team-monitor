"""
Data models for the Bond Team Monitor extension.

These models represent the normalized data collected from both Linux
Bonding and Windows NIC Teaming before it is reported to Dynatrace.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NetworkMember:
    """
    Represents a physical network interface that belongs to a bond or team.
    """

    group_name: str
    interface_name: str

    ip_address: str

    status: bool
    active: bool

    speed_mbps: int
    duplex: str

    mac_address: str

    rx_bytes: int
    tx_bytes: int

    rx_errors: int
    tx_errors: int

    link_failure_count: int
    bond_mode: str
    aggregator_id: str

    operating_system: str

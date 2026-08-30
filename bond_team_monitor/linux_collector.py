"""
Linux collector for Bond Team Monitor.

This module discovers Linux bonding interfaces and parses their
member interfaces into normalized NetworkMember objects.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .topology import NetworkMember
from .utils import read_file, read_int_file, run_command

logger = logging.getLogger(__name__)

BONDING_DIRECTORY = Path("/proc/net/bonding")
STATISTICS_DIRECTORY = Path("/sys/class/net")
TEAMD_DIRECTORY = Path("/var/run/teamd")


def collect() -> list[NetworkMember]:
    """
    Collect all bonded network members on the host.

    Returns:
        List of discovered NetworkMember objects enriched with
        interface statistics and bond IP addresses.
    """

    logger.info("Scanning /proc/net/bonding")

    members: list[NetworkMember] = []

    # Discover and parse all bond interfaces.
    for bond_file in _discover_bonds():
        members.extend(_parse_bond_file(bond_file))

    for team_name in _discover_teams():
        members.extend(_parse_team(team_name))

    # Cache bond IP addresses to avoid repeated "ip" command executions.
    ip_cache: dict[str, str] = {}

    # Enrich each discovered member.
    for member in members:
        if member.group_name not in ip_cache:
            ip_cache[member.group_name] = _get_bond_ip(member.group_name)

        member.ip_address = ip_cache[member.group_name]

        _populate_statistics(member)

    logger.info(
        "Collected %d network member(s) across %d bond(s).",
        len(members),
        len(ip_cache),
    )

    return members


def _discover_bonds() -> list[Path]:
    """
    Discover Linux bond interfaces.

    Returns:
        List of bond information files.
    """
    if not BONDING_DIRECTORY.exists():
        logger.info("No Linux bonding interfaces found.")
        return []

    bonds = [path for path in BONDING_DIRECTORY.iterdir() if path.is_file()]

    logger.info("Discovered %d bond(s).", len(bonds))

    return bonds


def _discover_teams() -> list[str]:
    """
    Discover Linux teamd interfaces.

    Returns:
        List of team interface names.
    """
    if not TEAMD_DIRECTORY.exists():
        logger.info("No teamd directory found.")
        return []

    teams = [path.stem for path in TEAMD_DIRECTORY.glob("*.pid") if path.is_file()]

    logger.info("Discovered %d team(s).", len(teams))

    return teams


def _parse_bond_file(bond_file: Path) -> list[NetworkMember]:
    """
    Parse a Linux bonding file.

    Args:
        bond_file: Path to /proc/net/bonding/<bond>

    Returns:
        List of NetworkMember objects.
    """
    contents = read_file(str(bond_file))

    if contents is None:
        return []

    bond_name = bond_file.name

    active_slave = ""
    bond_mode = "unknown"
    aggregator_id = ""

    members: list[NetworkMember] = []

    current: dict[str, str | int] | None = None

    for raw_line in contents.splitlines():
        line = raw_line.strip()

        if line.startswith("Currently Active Slave:"):
            active_slave = line.split(":", 1)[1].strip()

        if line.startswith("Bonding Mode:"):
            bond_mode = line.split(":", 1)[1].strip()

        if line.startswith("Aggregator ID:"):
            aggregator_id = line.split(":", 1)[1].strip()

        elif line.startswith("Slave Interface:"):
            if current:
                members.append(
                    _build_member(
                        bond_name,
                        active_slave,
                        bond_mode,
                        aggregator_id,
                        current,
                    )
                )

            current = {"interface": line.split(":", 1)[1].strip()}

        elif current is None:
            continue

        elif line.startswith("MII Status:"):
            current["status"] = line.split(":", 1)[1].strip()

        elif line.startswith("Speed:"):
            current["speed"] = line.split(":", 1)[1].strip()

        elif line.startswith("Duplex:"):
            current["duplex"] = line.split(":", 1)[1].strip()

        elif line.startswith("Permanent HW addr:"):
            current["mac"] = line.split(":", 1)[1].strip()
        elif line.startswith("Link Failure Count:"):
            current["link_failure_count"] = int(line.split(":", 1)[1].strip())

    if current:
        members.append(
            _build_member(
                bond_name,
                active_slave,
                bond_mode,
                aggregator_id,
                current,
            )
        )

    logger.info(
        "Bond '%s' contains %d member(s).",
        bond_name,
        len(members),
    )

    return members


def _parse_team(team_name: str) -> list[NetworkMember]:
    """
    Parse a teamd team using teamdctl state dump.

    Args:
        team_name: Name of the team interface (e.g. team0).

    Returns:
        List of NetworkMember objects.
    """
    output = run_command(
        [
            "teamdctl",
            team_name,
            "state",
            "dump",
        ]
    )

    if output is None:
        logger.warning(
            "Unable to retrieve teamd state for '%s'.",
            team_name,
        )
        return []

    try:
        team_data = json.loads(output)
    except json.JSONDecodeError:
        logger.exception(
            "Failed to parse teamd state dump for '%s'.",
            team_name,
        )
        return []

    setup = team_data.get("setup", {})
    bond_mode = setup.get("runner_name", "unknown")
    active_port = team_data.get("runner", {}).get("active_port", "")

    ports = team_data.get("ports", {})

    members: list[NetworkMember] = []

    for interface, port_data in ports.items():
        link = port_data.get("link", {})
        ifinfo = port_data.get("ifinfo", {})
        link_watches = port_data.get("link_watches", {}).get("list", {})

        link_failure_count = 0

        for watcher in link_watches.values():
            down_count = watcher.get("down_count", 0)

            if isinstance(down_count, int):
                link_failure_count = max(
                    link_failure_count,
                    down_count,
                )

        members.append(
            NetworkMember(
                group_name=team_name,
                interface_name=interface,
                ip_address="",
                status=link.get("up", False),
                active=interface == active_port,
                speed_mbps=link.get("speed", 0),
                duplex=link.get("duplex", "unknown").lower(),
                mac_address=ifinfo.get("dev_addr", ""),
                rx_bytes=0,
                tx_bytes=0,
                rx_errors=0,
                tx_errors=0,
                link_failure_count=link_failure_count,
                bond_mode=bond_mode,
                aggregator_id="NA",
                operating_system="linux",
            )
        )

    logger.info(
        "Team '%s' contains %d member(s).",
        team_name,
        len(members),
    )

    return members


def _build_member(
    bond_name: str,
    active_slave: str,
    bond_mode: str,
    aggregator_id: str,
    data: dict[str, str],
) -> NetworkMember:
    """
    Convert parsed bond data into a NetworkMember.
    """
    speed = data.get("speed", "0").replace(" Mbps", "")

    try:
        speed_mbps = int(speed)
    except ValueError:
        speed_mbps = 0

    interface = data["interface"]

    return NetworkMember(
        group_name=bond_name,
        interface_name=interface,
        ip_address="",
        status=_is_up(data.get("status", "")),
        active=interface == active_slave,
        speed_mbps=speed_mbps,
        duplex=data.get("duplex", "unknown").lower(),
        mac_address=data.get("mac", ""),
        rx_bytes=0,
        tx_bytes=0,
        rx_errors=0,
        tx_errors=0,
        link_failure_count=data.get("link_failure_count", 0),
        bond_mode=bond_mode,
        aggregator_id=aggregator_id,
        operating_system="linux",
    )


def _is_up(value: str) -> bool:
    return value.strip().lower() == "up"


def _populate_statistics(member: NetworkMember) -> None:
    """
    Populate interface statistics for a network member.
    """

    stats_path = STATISTICS_DIRECTORY / member.interface_name / "statistics"

    member.rx_bytes = read_int_file(str(stats_path / "rx_bytes"))

    member.tx_bytes = read_int_file(str(stats_path / "tx_bytes"))

    member.rx_errors = read_int_file(str(stats_path / "rx_errors"))

    member.tx_errors = read_int_file(str(stats_path / "tx_errors"))


def _get_bond_ip(bond_name: str) -> str:
    """
    Get the IPv4 address assigned to a bond interface.

    Args:
        bond_name: Name of the bond interface (e.g. bond0, bseip).

    Returns:
        IPv4 address if found, otherwise an empty string.
    """
    empty_ip_address = ""

    output = run_command(
        [
            "ip",
            "-j",
            "addr",
            "show",
            bond_name,
        ]
    )

    if output is None:
        return ""

    try:
        interfaces = json.loads(output)

        if not interfaces:
            logger.warning(
                "No interface information found for '%s'.",
                bond_name,
            )
            return ""

        addr_info = interfaces[0].get("addr_info", [])

        for address in addr_info:
            if address.get("family") == "inet":
                return address.get("local", "")

        logger.info(
            "No IPv4 address assigned to bond '%s'.",
            bond_name,
        )

    except json.JSONDecodeError:
        logger.exception(
            "Failed to parse JSON output for bond '%s'.",
            bond_name,
        )

    return empty_ip_address

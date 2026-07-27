"""
Windows NIC Teaming (LBFO) collector.
"""

from __future__ import annotations

import json
import logging
import subprocess

from .topology import NetworkMember

logger = logging.getLogger(__name__)


PS_SCRIPT = r"""
$team = Get-NetLbfoTeam
$members = Get-NetLbfoTeamMember
$ips = Get-NetIPAddress
$adapters = Get-NetAdapter
$stats = Get-NetAdapterStatistics

@{
    Team = $team
    Members = $members
    IPs = $ips
    Adapters = $adapters
    Stats = $stats
} | ConvertTo-Json -Depth 10 -Compress
"""

TEAMING_MODES = {
    0: "Static",
    1: "SwitchIndependent",
    2: "LACP",
}

LOAD_BALANCING = {
    0: "TransportPorts",
    1: "IPAddresses",
    2: "MacAddresses",
    3: "HyperVPort",
    4: "Dynamic",
}

def _run_powershell() -> dict:
    """Execute PowerShell and return parsed JSON."""

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            PS_SCRIPT,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def _as_list(value):
    """PowerShell returns an object instead of a list when only one exists."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def collect() -> list[NetworkMember]:
    """Collect Windows NIC Team information."""

    try:
        data = _run_powershell()
    except Exception:
        logger.exception("Unable to collect Windows Teaming information.")
        return []

    teams = _as_list(data.get("Team"))
    members = _as_list(data.get("Members"))
    adapters = _as_list(data.get("Adapters"))
    ips = _as_list(data.get("IPs"))
    stats = _as_list(data.get("Stats"))

    adapter_lookup = {
        adapter["Name"]: adapter
        for adapter in adapters
    }

    stats_lookup = {
        stat["Name"]: stat
        for stat in stats
    }

    collected = []

    for team in teams:

        team_name = team["Name"]

        team_ip = ""

        for ip in ips:
            logger.info("IP object: %s", ip)
            if (
                ip.get("InterfaceAlias") == team_name
                and ip.get("AddressFamily") == 2
            ):
                team_ip = ip["IPAddress"]
                break

        for member in members:

            if member["Team"] != team_name:
                continue

            adapter = adapter_lookup.get(member["InterfaceAlias"], {})
            stat = stats_lookup.get(member["InterfaceAlias"], {})

            speed = 0

            try:
                speed_str = adapter.get("LinkSpeed", "0 Gbps")

                if "Gbps" in speed_str:
                    speed = int(float(speed_str.split()[0]) * 1000)

                elif "Mbps" in speed_str:
                    speed = int(float(speed_str.split()[0]))

            except Exception:
                pass


            collected.append(
                NetworkMember(
                    group_name=team_name,
                    interface_name=member["InterfaceAlias"],
                    ip_address=team_ip,

                    status=member.get("OperationalStatus") == 0,
                    active=member.get("OperationalStatus") == 0,

                    speed_mbps=speed,
                    duplex="full",

                    mac_address=adapter.get("MacAddress", ""),

                    rx_bytes=int(stat.get("ReceivedBytes", 0)),
                    tx_bytes=int(stat.get("SentBytes", 0)),

                    rx_errors=int(stat.get("ReceivedPacketErrors", 0)),
                    tx_errors=int(stat.get("OutboundPacketErrors", 0)),

                    link_failure_count=int(member.get("NumberOfFailures") or 0),
                    bond_mode=TEAMING_MODES.get(
                        team.get("TeamingMode"),
                        str(team.get("TeamingMode", "")),
                    ),
                    aggregator_id=LOAD_BALANCING.get(
                        team.get("LoadBalancingAlgorithm"),
                        str(team.get("LoadBalancingAlgorithm", "")),
                    ),

                    operating_system="windows",
                )
            )

    logger.info("Collected %d Windows team members.", len(collected))

    return collected

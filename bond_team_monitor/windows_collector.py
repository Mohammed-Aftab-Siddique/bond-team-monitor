"""
Windows NIC Teaming (LBFO) collector.
"""

from __future__ import annotations

import json
import logging
import subprocess

logger = logging.getLogger(__name__)


PS_SCRIPT = r"""
$team = Get-NetLbfoTeam
$members = Get-NetLbfoTeamMember
$ips = Get-NetIPAddress
$adapters = Get-NetAdapter

@{
    Team = $team
    Members = $members
    IPs = $ips
    Adapters = $adapters
} | ConvertTo-Json -Depth 10 -Compress
"""


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


def collect() -> list[dict]:
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

    adapter_lookup = {
        adapter["Name"]: adapter
        for adapter in adapters
    }

    collected = []

    for team in teams:

        team_name = team["Name"]

        team_ip = ""

        for ip in ips:
            if (
                ip.get("InterfaceAlias") == team_name
                and ip.get("AddressFamily") == "IPv4"
            ):
                team_ip = ip["IPAddress"]
                break

        for member in members:

            if member["Team"] != team_name:
                continue

            adapter = adapter_lookup.get(member["InterfaceAlias"], {})

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
                {
                    "group": team_name,
                    "interface": member["InterfaceAlias"],
                    "status": 1 if member["OperationalStatus"] == "Active" else 0,
                    "speed": speed,
                    "ip_address": team_ip,
                    "mac_address": adapter.get("MacAddress", ""),
                    "duplex": "full",
                    "operating_system": "windows",
                }
            )

    logger.info("Collected %d Windows team members.", len(collected))

    return collected

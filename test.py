import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import bond_team_monitor.linux_collector as lc

# ============================================================
# Customer's actual teamdctl team0 state dump
# ============================================================

team_json = r"""
{
    "ports": {
        "eno12399": {
            "ifinfo": {
                "dev_addr": "9c:63:c0:bd:7d:5e",
                "dev_addr_len": 6,
                "ifindex": 4,
                "ifname": "eno12399"
            },
            "link": {
                "duplex": "full",
                "speed": 10000,
                "up": true
            },
            "link_watches": {
                "list": {
                    "link_watch_0": {
                        "delay_down": 0,
                        "delay_up": 0,
                        "down_count": 0,
                        "name": "ethtool",
                        "up": true
                    }
                },
                "up": true
            }
        },
        "ens1f0": {
            "ifinfo": {
                "dev_addr": "9c:63:c0:bd:7d:5e",
                "dev_addr_len": 6,
                "ifindex": 6,
                "ifname": "ens1f0"
            },
            "link": {
                "duplex": "full",
                "speed": 10000,
                "up": true
            },
            "link_watches": {
                "list": {
                    "link_watch_0": {
                        "delay_down": 0,
                        "delay_up": 0,
                        "down_count": 0,
                        "name": "ethtool",
                        "up": true
                    }
                },
                "up": true
            }
        }
    },
    "setup": {
        "daemonized": false,
        "dbus_enabled": true,
        "debug_level": 0,
        "kernel_team_mode_name": "roundrobin",
        "pid": 4057316,
        "pid_file": "/var/run/teamd/team0.pid",
        "runner_name": "roundrobin",
        "zmq_enabled": false
    },
    "team_device": {
        "ifinfo": {
            "dev_addr": "9c:63:c0:bd:7d:5e",
            "dev_addr_len": 6,
            "ifindex": 8,
            "ifname": "team0"
        }
    }
}
"""


# ============================================================
# Test 1: _discover_teams() when teamd does not exist
# ============================================================

with patch.object(
    lc,
    "TEAMD_DIRECTORY",
    Path("/tmp/definitely-does-not-exist-teamd"),
):
    result = lc._discover_teams()

assert result == []

print("TEST 1 PASS: No teamd directory -> []")


# ============================================================
# Test 2: _discover_teams() with multiple teams
# ============================================================

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)

    (temp_path / "team0.pid").touch()
    (temp_path / "team1.pid").touch()
    (temp_path / "team2.pid").touch()

    # Should be ignored
    (temp_path / "not-a-team.txt").touch()

    with patch.object(lc, "TEAMD_DIRECTORY", temp_path):
        result = lc._discover_teams()

expected = {"team0", "team1", "team2"}

assert set(result) == expected

print("TEST 2 PASS: Multiple team*.pid files discovered correctly")


# ============================================================
# Test 3: _parse_team() using customer's exact JSON
# ============================================================

with patch.object(
    lc,
    "run_command",
    return_value=team_json,
):
    members = lc._parse_team("team0")

assert len(members) == 2

members_by_interface = {member.interface_name: member for member in members}

eno12399 = members_by_interface["eno12399"]
ens1f0 = members_by_interface["ens1f0"]

for member in members:
    assert member.group_name == "team0"
    assert member.status is True
    assert member.active is False
    assert member.speed_mbps == 10000
    assert member.duplex == "full"
    assert member.mac_address == "9c:63:c0:bd:7d:5e"
    assert member.link_failure_count == 0
    assert member.bond_mode == "roundrobin"
    assert member.aggregator_id == "NA"
    assert member.operating_system == "linux"

print("TEST 3 PASS: Customer team0 JSON parsed correctly")


# ============================================================
# Test 4: active_port handling
#
# This is an additional synthetic case to verify that:
# interface == active_port -> active=True
# ============================================================

active_team_data = json.loads(team_json)

active_team_data["runner"] = {"active_port": "eno12399"}

active_team_json = json.dumps(active_team_data)

with patch.object(
    lc,
    "run_command",
    return_value=active_team_json,
):
    members = lc._parse_team("team0")

members_by_interface = {member.interface_name: member for member in members}

assert members_by_interface["eno12399"].active is True
assert members_by_interface["ens1f0"].active is False

print("TEST 4 PASS: active_port mapping works correctly")


# ============================================================
# Test 5: teamdctl failure handling
# ============================================================

with patch.object(
    lc,
    "run_command",
    return_value=None,
):
    members = lc._parse_team("team0")

assert members == []

print("TEST 5 PASS: teamdctl failure -> []")


# ============================================================
# Test 6: invalid JSON handling
# ============================================================

with patch.object(
    lc,
    "run_command",
    return_value="this is not json",
):
    members = lc._parse_team("team0")

assert members == []

print("TEST 6 PASS: Invalid teamd JSON -> []")


# ============================================================
# Test 7: Full collect() flow
#
# We simulate:
#
#   bond0
#       eth0
#
#   team0
#       eno12399
#       ens1f0
#
# We DO NOT modify the actual filesystem.
# ============================================================

bond_contents = """
Ethernet Channel Bonding Driver: v5.15.0

Bonding Mode: IEEE 802.3ad Dynamic link aggregation
Currently Active Slave: eth0
MII Status: up
Speed: 10000 Mbps
Duplex: full
Permanent HW addr: aa:bb:cc:dd:ee:ff
Link Failure Count: 0

Slave Interface: eth0
MII Status: up
Speed: 10000 Mbps
Duplex: full
Permanent HW addr: aa:bb:cc:dd:ee:ff
Link Failure Count: 0
"""

fake_bond_file = Path("/tmp/bond0")


def fake_discover_bonds():
    return [fake_bond_file]


def fake_discover_teams():
    return ["team0"]


def fake_read_file(path):
    if path == str(fake_bond_file):
        return bond_contents
    return None


def fake_run_command(command):
    # teamdctl team0 state dump
    if command == [
        "teamdctl",
        "team0",
        "state",
        "dump",
    ]:
        return team_json

    # ip -j addr show bond0
    if command == [
        "ip",
        "-j",
        "addr",
        "show",
        "bond0",
    ]:
        return json.dumps(
            [
                {
                    "ifname": "bond0",
                    "addr_info": [
                        {
                            "family": "inet",
                            "local": "192.168.1.10",
                        }
                    ],
                }
            ]
        )

    # ip -j addr show team0
    if command == [
        "ip",
        "-j",
        "addr",
        "show",
        "team0",
    ]:
        return json.dumps(
            [
                {
                    "ifname": "team0",
                    "addr_info": [
                        {
                            "family": "inet",
                            "local": "192.168.1.20",
                        }
                    ],
                }
            ]
        )

    return None


def fake_read_int_file(path):
    statistics = {
        "/sys/class/net/eth0/statistics/rx_bytes": 1000,
        "/sys/class/net/eth0/statistics/tx_bytes": 2000,
        "/sys/class/net/eth0/statistics/rx_errors": 3,
        "/sys/class/net/eth0/statistics/tx_errors": 4,
        "/sys/class/net/eno12399/statistics/rx_bytes": 5000,
        "/sys/class/net/eno12399/statistics/tx_bytes": 6000,
        "/sys/class/net/eno12399/statistics/rx_errors": 1,
        "/sys/class/net/eno12399/statistics/tx_errors": 2,
        "/sys/class/net/ens1f0/statistics/rx_bytes": 7000,
        "/sys/class/net/ens1f0/statistics/tx_bytes": 8000,
        "/sys/class/net/ens1f0/statistics/rx_errors": 5,
        "/sys/class/net/ens1f0/statistics/tx_errors": 6,
    }

    return statistics.get(path, 0)


with (
    patch.object(lc, "_discover_bonds", fake_discover_bonds),
    patch.object(lc, "_discover_teams", fake_discover_teams),
    patch.object(lc, "read_file", fake_read_file),
    patch.object(lc, "run_command", fake_run_command),
    patch.object(lc, "read_int_file", fake_read_int_file),
):
    members = lc.collect()


# ------------------------------------------------------------
# Verify total members
# ------------------------------------------------------------

assert len(members) == 3

print("TEST 7A PASS: Full collect() returned 3 members")


# ------------------------------------------------------------
# Separate bond and team members
# ------------------------------------------------------------

bond_members = [member for member in members if member.group_name == "bond0"]

team_members = [member for member in members if member.group_name == "team0"]

assert len(bond_members) == 1
assert len(team_members) == 2

print("TEST 7B PASS: Bond and team members coexist")


# ------------------------------------------------------------
# Verify existing bond behavior
# ------------------------------------------------------------

bond = bond_members[0]

assert bond.interface_name == "eth0"
assert bond.ip_address == "192.168.1.10"
assert bond.status is True
assert bond.active is True
assert bond.speed_mbps == 10000
assert bond.duplex == "full"
assert bond.mac_address == "aa:bb:cc:dd:ee:ff"
assert bond.rx_bytes == 1000
assert bond.tx_bytes == 2000
assert bond.rx_errors == 3
assert bond.tx_errors == 4
assert bond.bond_mode == "IEEE 802.3ad Dynamic link aggregation"

print("TEST 7C PASS: Existing bond behavior preserved")


# ------------------------------------------------------------
# Verify team IP enrichment
# ------------------------------------------------------------

for member in team_members:
    assert member.ip_address == "192.168.1.20"

print("TEST 7D PASS: Team IP enrichment works")


# ------------------------------------------------------------
# Verify team statistics enrichment
# ------------------------------------------------------------

team_by_interface = {member.interface_name: member for member in team_members}

assert team_by_interface["eno12399"].rx_bytes == 5000
assert team_by_interface["eno12399"].tx_bytes == 6000
assert team_by_interface["eno12399"].rx_errors == 1
assert team_by_interface["eno12399"].tx_errors == 2

assert team_by_interface["ens1f0"].rx_bytes == 7000
assert team_by_interface["ens1f0"].tx_bytes == 8000
assert team_by_interface["ens1f0"].rx_errors == 5
assert team_by_interface["ens1f0"].tx_errors == 6

print("TEST 7E PASS: Team RX/TX statistics enrichment works")


# ============================================================
# Final summary
# ============================================================

print()
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)

for member in members:
    print(
        f"{member.group_name:6} / "
        f"{member.interface_name:10} | "
        f"status={member.status} | "
        f"active={member.active} | "
        f"speed={member.speed_mbps} | "
        f"duplex={member.duplex} | "
        f"mode={member.bond_mode} | "
        f"aggregator={member.aggregator_id} | "
        f"ip={member.ip_address}"
    )

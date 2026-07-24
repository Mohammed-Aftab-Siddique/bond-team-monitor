# Bond Team Monitor

> A Dynatrace Extensions 2.0 extension for monitoring Linux Bonding and Windows NIC Teaming.

## Overview

Bond Team Monitor extends Dynatrace's infrastructure monitoring by exposing the health and status of the physical network interfaces that make up a bonded or teamed network interface.

While Dynatrace monitors logical network interfaces, many enterprise environments rely on Linux Bonding or Windows NIC Teaming for redundancy and high availability. This extension discovers the underlying physical interfaces and reports their health as custom metrics.

Supported technologies include:

- Linux Bonding
- Windows NIC Teaming (LBFO)

---

## Features

### Linux

- Discover bonded interfaces
- Discover slave NICs
- Monitor link status
- Monitor active slave
- Monitor interface speed
- Monitor duplex mode
- Monitor RX/TX bytes
- Monitor RX/TX errors

### Windows

- Discover NIC Teams
- Discover team members
- Monitor member status
- Monitor active/standby members
- Monitor interface speed
- Monitor RX/TX statistics

---

## Planned Metrics

| Metric | Description |
|---------|-------------|
| bond_team.status | Link status of a physical NIC |
| bond_team.active | Whether the NIC is currently active |
| bond_team.speed | Link speed |
| bond_team.duplex | Duplex mode |
| bond_team.rx.bytes | Received bytes |
| bond_team.tx.bytes | Transmitted bytes |
| bond_team.rx.errors | Receive errors |
| bond_team.tx.errors | Transmit errors |
| bond_team.health | Overall bond/team health |

---

## Project Structure

```
bond-team-monitor/
├── extension/
│   ├── extension.yaml
│   ├── activationSchema.json
│   ├── requirements.txt
│   └── lib/
│       ├── linux_collector.py
│       ├── windows_collector.py
│       ├── metrics.py
│       ├── topology.py
│       └── utils.py
├── README.md
└── LICENSE
```

---

## Requirements

- Dynatrace Extensions 2.0
- Python runtime supported by Dynatrace Extension Execution Controller (EEC)
- Linux (Bonding)
- Windows Server (NIC Teaming)

---

## Roadmap

- [ ] Project scaffold
- [ ] Linux collector
- [ ] Windows collector
- [ ] Metric reporting
- [ ] Documentation
- [ ] First public release (v1.0.0)

---

## Contributing

Contributions, feature requests, bug reports, and improvements are welcome.

Please open an issue before submitting major changes.

---

## License

This project is licensed under the MIT License.

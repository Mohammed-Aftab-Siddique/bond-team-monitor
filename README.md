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

# Team / Bond Monitor

Dynatrace extension for monitoring **Team/Bond network interfaces and their member interfaces**.

This guide explains how to build, install, and configure the Team / Bond Monitor extension in a Dynatrace environment.

---

## Installation Overview

The installation consists of the following steps:

1. Clone the repository
2. Build the extension
3. Add the signing certificate to Dynatrace Credential Vault
4. Upload the extension to Dynatrace
5. Install the certificate on the OneAgent host
6. Restart the Extension Execution Controller
7. Create the extension configuration from the Dynatrace UI

---

## Prerequisites

Before starting, make sure you have:

* Access to a Dynatrace environment
* Permission to upload and configure custom extensions
* A Linux or Windows host running Dynatrace OneAgent
* Visual Studio Code with the Dynatrace Extensions extension **or** the Dynatrace Extensions SDK/CLI
* Access to the Team / Bond Monitor source code

---

## 1. Clone the Repository

Clone the repository:

```bash
git clone https://github.com/Mohammed-Aftab-Siddique/bond-team-monitor.git
```

Navigate to the repository:

```bash
cd bond-team-monitor
```

---

## 2. Build the Extension

The extension can be built using either **Visual Studio Code** or the **Dynatrace Extensions SDK CLI**.

### Option A — Build using Visual Studio Code

Open the repository in Visual Studio Code:

```bash
code .
```

Open the Command Palette:

```text
Ctrl + Shift + P
```

Search for:

```text
Dynatrace extensions: Build
```

The Dynatrace VS Code extension will build and package the extension into a signed ZIP file.

The resulting package is placed in the `dist` directory.

Dynatrace documentation:

[Build and develop Dynatrace extensions](https://docs.dynatrace.com/docs/ingest-from/extensions/develop-your-extensions?utm_source=chatgpt.com)

### Option B — Build using the CLI

If the Dynatrace Extensions SDK is installed, run:

```bash
dt-sdk build
```

The generated extension package will be available in the `dist` directory.

You can also validate the extension before building:

```bash
dt-sdk lint
```

For more information about the Dynatrace Extensions SDK and build process, see the official documentation:

[Dynatrace Extensions documentation](https://docs.dynatrace.com/docs/ingest-from/extensions?utm_source=chatgpt.com)

---

## 3. Add the Certificate to Dynatrace Credential Vault

The extension package must be signed with a trusted certificate before Dynatrace will execute it.

Add the **root/CA certificate** used to sign the extension to the Dynatrace Credential Vault.

In Dynatrace:

1. Open **Credential Vault**.

2. Create a new credential.

3. Select:

   ```text
   Credential type: Public certificate
   ```

4. Set the credential scope to:

   ```text
   Extension validation
   ```

5. Upload the root certificate.

6. Save the credential.

> **Important:** The certificate must be added under the **Public certificate** category with the **Extension validation** scope.

Dynatrace documentation:

[Sign extensions and distribute certificates](https://docs.dynatrace.com/docs/ingest-from/extensions/develop-your-extensions/sign-extensions?utm_source=chatgpt.com)

---

## 4. Upload the Extension to Dynatrace

After successfully building the extension, upload the generated ZIP package to Dynatrace.

In the Dynatrace UI:

```text
Extensions → Upload custom extension
```

Select the generated ZIP file from the `dist` directory.

For example:

```text
dist/
└── custom:bond-team-monitor-<version>.zip
```

Dynatrace will validate the extension package and make it available for configuration after a successful upload.

Dynatrace documentation:

[Manage Extensions — Upload a custom extension](https://docs.dynatrace.com/docs/ingest-from/extensions/manage-extensions?utm_source=chatgpt.com)

---

## 5. Place the Certificate on the OneAgent Host

For a **local extension** running on a OneAgent host, the signing certificate must also be available locally on the host.

### Linux

Copy the `root.pem` certificate to:

```text
/var/lib/dynatrace/oneagent/agent/config/certificates/
```

The final path should be:

```text
/var/lib/dynatrace/oneagent/agent/config/certificates/root.pem
```

For example:

```bash
sudo cp root.pem /var/lib/dynatrace/oneagent/agent/config/certificates/root.pem
```

### Windows

Place the certificate at:

```text
%PROGRAMDATA%\dynatrace\oneagent\agent\config\certificates\
```

For example:

```text
%PROGRAMDATA%\dynatrace\oneagent\agent\config\certificates\root.pem
```

### Certificate Permissions

The certificate must be accessible by the account used by the Extension Execution Controller.

For **Linux OneAgent**, the certificate must be accessible by:

```text
dtuser
```

Verify the permissions:

```bash
ls -l /var/lib/dynatrace/oneagent/agent/config/certificates/root.pem
```

If required, adjust the ownership/permissions so that `dtuser` can read the certificate.

For **Windows OneAgent**, the certificate must be accessible by:

```text
LOCAL_SYSTEM
```

Dynatrace documentation:

[Sign extensions — Certificate locations and permissions](https://docs.dynatrace.com/docs/ingest-from/extensions/develop-your-extensions/sign-extensions?utm_source=chatgpt.com)

> **Note:** The certificate on the OneAgent host must correspond to the root/CA certificate used to sign the extension.

---

## 6. Restart the Extension Execution Controller

After placing or changing the certificate on the OneAgent host, restart the **Extension Execution Controller** so that the certificate can be picked up.

A restart of the complete OneAgent service may also be performed if required.

> **Optional:** A complete OneAgent restart is generally not required just for the certificate update. Restart the Extension Execution Controller first. If the extension continues to report certificate or permission errors, restart OneAgent.

Refer to the Dynatrace documentation for restarting OneAgent:

[Stop/restart OneAgent on Linux](https://docs.dynatrace.com/docs/ingest-from/dynatrace-oneagent/installation-and-operation/linux/operation/stop-restart-oneagent-on-linux?utm_source=chatgpt.com)

---

## 7. Create the Extension Configuration

Once the extension has been uploaded and the certificate has been distributed:

1. Open the **Extensions** app in Dynatrace.
2. Locate **Team / Bond Monitor**.
3. Select **Add monitoring configuration**.
4. Configure the required parameters.
5. Select the appropriate execution location/host.
6. Provide the required connection and monitoring details.
7. Save and activate the configuration.

The extension will then start collecting Team/Bond interface information from the configured host.

Dynatrace documentation:

[Manage Extensions](https://docs.dynatrace.com/docs/ingest-from/extensions/manage-extensions?utm_source=chatgpt.com)

---

## Installation Flow

```text
┌─────────────────────┐
│  Clone Repository   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Build Extension   │
│ VS Code / dt-sdk    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Add Root Certificate│
│  to Credential Vault│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Upload Extension to │
│      Dynatrace      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Copy root.pem to    │
│     OneAgent        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Set Required        │
│    Permissions      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Restart Extension   │
│ Execution Controller│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Create Monitoring   │
│ Configuration in DT │
└─────────────────────┘
```

---

## Troubleshooting

### Extension fails certificate validation

Verify that:

* The extension was signed with the expected certificate.
* The corresponding root/CA certificate exists in Dynatrace Credential Vault.
* The Credential Vault entry uses **Public certificate**.
* The credential scope is **Extension validation**.
* The same root certificate is present on the OneAgent host.
* The certificate file is readable by `dtuser` on Linux or `LOCAL_SYSTEM` on Windows.

### Linux certificate permission error

Check:

```bash
ls -l /var/lib/dynatrace/oneagent/agent/config/certificates/root.pem
```

Make sure the OneAgent Extension Execution Controller can read the file.

If the permissions are correct but the extension still fails, restart the Extension Execution Controller and retry.

### Extension is uploaded but not collecting data

Check:

1. The extension is enabled in Dynatrace.
2. A monitoring configuration has been created.
3. The configuration is active.
4. The target host has OneAgent installed and running.
5. The certificate is available on the target host.
6. The certificate permissions are correct.
7. The Extension Execution Controller is running.

---

## Dynatrace Documentation

* [Dynatrace Extensions](https://docs.dynatrace.com/docs/ingest-from/extensions?utm_source=chatgpt.com)
* [Sign and distribute extensions](https://docs.dynatrace.com/docs/ingest-from/extensions/develop-your-extensions/sign-extensions?utm_source=chatgpt.com)
* [Manage Extensions](https://docs.dynatrace.com/docs/ingest-from/extensions/manage-extensions?utm_source=chatgpt.com)

---

## Contributing

Contributions, feature requests, bug reports, and improvements are welcome.

Please open an issue before submitting major changes.

---

## License

This project is licensed under the MIT License.

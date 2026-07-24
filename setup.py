from pathlib import Path

from setuptools import find_packages, setup


def find_version() -> str:
    version = "0.1.0"
    extension_yaml_path = Path(__file__).parent / "extension" / "extension.yaml"

    try:
        with open(extension_yaml_path, encoding="utf-8") as file:
            for line in file:
                if line.startswith("version"):
                    version = line.split(":", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass

    return version


setup(
    name="bond_team_monitor",
    version=find_version(),
    description="Dynatrace Extension 2.0 for Linux Bonding and Windows NIC Teaming monitoring.",
    author="Mohammed Aftab Siddique",
    packages=find_packages(),
    python_requires=">=3.10",
    include_package_data=True,
    install_requires=[
        "dt-extensions-sdk",
    ],
    extras_require={
        "dev": [
            "dt-extensions-sdk[cli]",
        ],
    },
)

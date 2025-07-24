# OKS-CLI

[![Project Incubating](https://docs.outscale.com/fr/userguide/_images/Project-Incubating-blue.svg)](https://docs.outscale.com/en/userguide/Open-Source-Projects.html)
[![](https://dcbadge.limes.pink/api/server/HUVtY5gT6s?style=flat&theme=default-inverted)](https://discord.gg/HUVtY5gT6s)

<p align="center">
  <img alt="Kubernetes" src="https://upload.wikimedia.org/wikipedia/commons/3/39/Kubernetes_logo_without_workmark.svg" width="120px">
</p>

---

## 🌐 Links

* 📘 [OKS-CLI Documentation](https://docs.outscale.com/fr/userguide/Installer-et-configurer-OKS-CLI.html)
* 📘 [OKS API Reference](https://docs.outscale.com/oks.html)
* 🐛 [GitHub Issues](https://github.com/outscale/oks-cli/issues)

---

## 📄 Table of Contents

* [Overview](#-overview)
* [Requirements](#-requirements)
* [Installation](#-installation)

  * [Standard Installation](#standard-installation)
  * [User Installation](#user-installation)
* [Usage](#-usage)

  * [Commands](#commands)
  * [Examples](#examples)
* [Development](#-development)

  * [Editable Mode](#editable-mode)
  * [Project Structure](#project-structure)
  * [Dependencies](#dependencies)
* [Contributing](#-contributing)
* [License](#-license)
* [Support](#-support)

---

## 🧭 Overview

**OKS-CLI** is a command-line interface that allows you to deploy and manage Kubernetes clusters on top of OUTSCALE infrastructure.

---

## ✅ Requirements

* Python 3.11 or later
* `pip` (Python package manager)
* `kubectl` (required for commands that interact with the Kubernetes API)

---

## 📦 Installation

### Standard Installation

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install the CLI
pip install oks-cli

# Check version of oks-cli
oks-cli version
```

---

## 🚀 Usage

Display all available commands:

```bash
oks-cli fullhelp
```

### Commands

| Command                              | Description                                                   |
|--------------------------------------|---------------------------------------------------------------|
| profile list                         | List existing profiles                                        |
| profile add                          | Add AK/SK or username/password new profile                    |
| profile delete                       | Delete a profile by name                                      |
| profile update                       | Update an existing profile                                    |
| project list                         | List all projects                                             |
| project create                       | Create a new project                                          |
| project get                          | Get default project or the project by name                    |
| project update                       | Update a project by name                                      |
| project delete                       | Delete a project by name                                      |
| project login                        | Set a default project by name                                 |
| project logout                       | Unset default project                                         |
| project quotas                       | Get project quotas                                            |
| project snapshots                    | Get project snapshots                                         |
| project publicips                    | Get project public ips                                        |
| cluster list                         | List all clusters                                             |
| cluster create                       | Create a new cluster                                          |
| cluster get                          | Get a cluster by name                                         |
| cluster update                       | Update a cluster by name                                      |
| cluster upgrade                      | Upgrade a cluster by name                                     |
| cluster delete                       | Delete a cluster by name                                      |
| cluster login                        | Set a default cluster                                         |
| cluster logout                       | Unset default cluster                                         |
| cluster kubeconfig                   | Fetch the kubeconfig for a cluster                            |
| cluster kubectl                      | Fetch kubeconfig and run kubectl against it                   |
| cluster nodepool list                | List nodepools in the specified cluster                       |
| cluster nodepool create              | Create a new nodepool in the cluster                          |
| cluster nodepool delete              | Delete a nodepool by name from the cluster                    |
| cache clear                          | Clear cache                                                   |
| cache kubeconfigs                    | List cached kubeconfigs                                       |
| quotas                               | Get quotas                                                    |
| fullhelp                             | Display detailed help information for all commands            |
| version                              | Show the current CLI version                                  |
| install-completion                   | Install shell completion scripts                              |

---

### Examples

```bash
# List all projects
oks-cli project list

# Dry run project creation
oks-cli project create --project-name my-project --description "Test project" --dry-run

# Dry run cluster creation
oks-cli cluster create \
  --cluster-name my-cluster \
  --project-name my-project \
  --description "My test cluster" \
  --version "1.32" \
  --dry-run

# Set a default project profile
oks-cli project login --project-name my-project
```

---

## 🛠 Development

### Editable Mode

Install the CLI in editable mode with development dependencies

```bash
# Clone the repository
git clone https://github.com/outscale/oks-cli.git
cd oks-cli

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# CLI in editable mode
pip install -e ".[dev]"
```

Changes in the `oks_cli/` directory will be immediately reflected without reinstalling.

### Tests

Run the test suite using `pytest` to ensure code correctness and stability:

```bash
pytest
```

### Project Structure

```
oks-cli/
├── oks_cli/              # Source code
│   ├── cache.py
│   ├── cluster.py
│   ├── main.py
│   ├── profile.py
│   ├── project.py
│   ├── quotas.py
│   └── utils.py
├── setup.py              # Packaging configuration
├── requirements.txt      # Dependencies
└── README.md             # Project documentation
```

### Dependencies

Dependencies are managed via `setup.py` and `requirements.txt`.

To reinstall or update:

```bash
pip install -e .
```

---

## 🤝 Contributing

OKS-CLI is open source software licensed under BSD-3-Clause.

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines and instructions.

---

## 📜 License

**BSD-3-Clause**
© Outscale SAS

---

## 🆘 Support

* [Official Documentation](https://docs.outscale.com/fr/userguide/Installer-et-configurer-OKS-CLI.html)
* [GitHub Issues](https://github.com/outscale/oks-cli/issues)

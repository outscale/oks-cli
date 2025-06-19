Here is your rewritten `README.md` for **OKS-CLI**, fully aligned with the schema and tone of your reference project:

---

# OKS-CLI

[![Project Incubating](https://docs.outscale.com/fr/userguide/_images/Project-Incubating-blue.svg)](https://docs.outscale.com/en/userguide/Open-Source-Projects.html)

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

---

## 📦 Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/outscale/oks-cli.git
cd oks-cli

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the CLI in editable mode
pip install -e .
```

### User Installation

Install globally without a virtual environment (Python 3.11):

```bash
pip3.11 install -e --user .
```

> **Note:** Ensure `~/Library/Python/3.11/bin` (macOS) or the equivalent path is in your `PATH`.

---

## 🚀 Usage

Display all available commands:

```bash
oks-cli fullhelp
```

### Commands

| Command          | Description                             |
| ---------------- | --------------------------------------- |
| `profile list`   | List available profiles                 |
| `cluster list`   | List deployed clusters                  |
| `project list`   | List projects                           |
| `project create` | Create a new project (supports dry run) |
| `cluster create` | Create a new cluster (supports dry run) |
| `project login`  | Set a default project profile           |

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

Install the CLI in development mode:

```bash
pip install -e .
```

Changes in the `oks_cli/` directory will be immediately reflected without reinstalling.

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
© 2024 Outscale SAS

---

## 🆘 Support

* [Official Documentation](https://docs.outscale.com/fr/userguide/Installer-et-configurer-OKS-CLI.html)
* [GitHub Issues](https://github.com/outscale/oks-cli/issues)

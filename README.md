# OKS-CLI

OKS-CLI is an interface that allows you to deploy your Kubernetes cluster on top of Outscale infrastructure.

## Prerequisites

- Python 3.11 or newer
- pip

## Installation

### Standard Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/outscale/oks-cli.git
cd oks-cli

# Create a virtual environment
python -m venv venv

# Activate your virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .
```

### User Installation (Python 3.11)

For a user-level installation without virtual environment:

```bash
pip3.11 install -e --user .
```

**Note:** Make sure `~/Library/Python/3.11/bin` (macOS) or the equivalent path on your system is in your PATH.

## Usage

To see all available commands:

```bash
oks-cli fullhelp
```

### Usage Examples

```bash
# List profiles
oks-cli profile list

# List clusters
oks-cli cluster list

# List projects
oks-cli project list

# Test project creation (dry run)
oks-cli project create --project-name my-first-project --description "I create my first project" --dry-run

# Test cluster creation (dry run)
oks-cli cluster create --cluster-name my-first-cluster --project-name my-first-project --description "I create my first cluster" --version "1.32" --dry-run

# Set a default profile
oks-cli project login --project-name NAME_OF_YOUR_PROJECT
```

## Development

### Development Installation

To contribute to the project, install in editable mode:

```bash
pip install -e .
```

The `-e` (or `--editable`) flag allows you to modify the source code without reinstalling the package. Changes in `oks_cli/` are immediately reflected.

### Project Structure

```
oks-cli/
├── oks_cli/              # Main source code
│   ├── __pycache__/      # Compiled Python files
│   ├── __init__.py       # Package initialization
│   ├── cache.py          # Cache management functionality
│   ├── cluster.py        # Cluster operations
│   ├── main.py           # Main CLI entry point
│   ├── profile.py        # Profile management
│   ├── project.py        # Project configuration
│   ├── quotas.py         # Quota management
│   └── utils.py          # Utility functions
├── setup.py              # Dependencies configuration
├── requirements.txt      # Dependencies list
└── README.md             # This file
```

### Dependencies

Dependencies are defined in `setup.py`. To update them:

```bash
pip install -e .
```

## Contributing

OKS-CLI is an open source software licensed under BSD-3-Clause.

Patches and discussions are welcome about bugs you've found or features you think are missing. If you would like to help making OKS-CLI better, take a look to CONTRIBUTING.md file.

## License

BSD-3-Clause

## Support

- [OKS-CLI Documentation](https://docs.outscale.com/fr/userguide/Installer-et-configurer-OKS-CLI.html)
- [OKS-API Documentation](https://docs.outscale.com/oks.html)
- [Link to GitHub issues](https://github.com/outscale/oks-cli/issues)
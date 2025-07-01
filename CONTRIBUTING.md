# Contribution Guide

Thank you for your interest in contributing to the OKS-CLI Project ! This document describes how you can participate and help us improve the project.

## Table of Contents

- [How to contribute](#how-to-contribute)
- [Report bugs](#report-bugs)
- [Suggest features](#suggest-features)
- [Development](#development)
- [Pull request process](#pull-request-process)
- [Code standards](#code-standards)

## How to contribute

There are several ways to contribute to this project:

- **Report bugs** - Help us identify and fix issues
- **Suggest new features** - Propose improvements and new functionality
- **Improve the documentation** - Make our guides clearer and more helpful

## Report bugs

Before reporting a bug, check that it has not already been reported by consulting existing issues.

### How to report a bug

Suggestions for improvements are welcome! Before reporting a bug :

1. Check if the Bug has already been reported
1. Use the "Bug Report" issue template
2. Provide a clear and concise description of the problem
3. Include steps to reproduce the bug
4. Describe the actual behavior
5. Describe the expected behavior
6. Specify your environment (OS, oks-cli version, terminal, etc.)
7. Attach any relevant logs, screenshots, or error messages

## Suggest features

Suggestions for improvements are welcome! Before proposing a feature :

1. Check if the Feture has already been reported
2. Use the "Feature Request" issue template
3. Clearly describe the problem your proposal solves
4. Explain your proposed solution
5. Mention any alternatives you considered
6. Wait for feedback from the team — or, if you're ready, implement the feature yourself by opening a pull request

## Development

### Prerequisites

Before you start development, make sure you have :

- Python 3.11 or newer
- Pip

### Environment configuration

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
├── CONTRIBUTING.md       # This file
└── README.md             # Documentation
```

## Pull request process

### Before submitting

1. Fork the repository
2. Create a branch for your feature (git checkout -b feature)
3. Commit your changes (git commit -m 'Adding my feature')
4. Push it to your branch (git push origin feature)
5. Open a Pull Request

### Acceptance criteria

- The code follows the project's Python conventions and CLI architecture
- Documentation is updated as needed
- Commits are well formatted
- No merge conflicts

### Description of PR

Use the provided template and include:

- **Summary** of changes
- **Type of change** (bug fix, new feature, breaking change, etc.)
- **Tests** performed
- **Screenshots** if applicable
- **Related issues** (e.g., "Fixes #123")

## Code standards

### Code style

- Follow project naming conventions
- Use configured linting tools (PEP8)
- Respect existing indentation and formatting
- Comment out complex code

### Commit message

Use the conventional format :

```
git commit -m "feat: brief description of your functionality"
```

Accepted types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`

### Documentation

- Update documentation as needed
- Use **docstrings** for public functions and classes
- Keep README.md up to date

## Review process

1. **Manual testing** : The CLI should be tested locally. Verify that the commands work and do not generate errors.
2. **Review by someone from our team** :  A member of our team will review the PR to ensure the code is clear and consistent.
3. **Merge** : A maintainer merges the PR after validation.

## Questions ?

If you have questions not covered in this guide :

- Consult [existing issues](https://github.com/outscale/oks-cli/issues)
- Contact [support](https://docs.outscale.com/fr/userguide/Support-technique.html)

## Thanks

Thank you to all the contributors who help improve this project! 🚀

---

By contributing to this project, you agree that your contributions are licensed under the same license as the project.
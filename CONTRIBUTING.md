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
- **Fix existing bugs** - Resolve reported issues
- **Implement new features** - Turn approved ideas into working code
- **Improve the documentation** - Make our guides clearer and more helpful

## Report bugs

Before reporting a bug, check that it has not already been reported by consulting existing issues.

### How to report a bug

1. Use the "Bug Report" issue template
2. Provide a clear and concise description of the problem
3. Include steps to reproduce the bug
4. Specify your environment (OS, software version, etc.)
5. Add screenshots if relevant

### Information to include

- **Summary**: Short description of the problem
- **Reproduction Steps**: List of actions
- **Expected Behavior**: What should happen
- **Current Behavior**: What is actually happening
- **Environment**: Technical details of your configuration

## Suggest features

Suggestions for improvements are welcome! Before proposing a feature:

1. Check if the feature already exists
2. Review existing issues to avoid duplication
3. Choose the right issue template based on your intent :
  - **Suggest a New Feature** : Use this template if you have an idea for a feature but do not plan to implement it yourself. This helps the community discuss and evaluate it.
  - **Implement a New Feature** : Use this template if you have both a feature idea and plan to submit a pull request to implement it. This allows better coordination and avoids duplicated efforts.

### Proposal process

1. Open an issue using the "Feature Request" template
2. Clearly describe the problem your proposal solves
3. Explain your proposed solution
4. Mention the alternatives considered
5. Wait for feedback from the team

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

- The code complies with the project's coding standards
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
- Use configured linting tools (Black, PEP8, etc.)
- Respect existing indentation and formatting
- Comment out complex code

### Commit message

Use the conventional format :

```
type(scope): short description

More detailed message body if needed.

Fix #123
```

Accepted types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Documentation

- Update documentation as needed
- Use **docstrings** for public functions and classes
- Keep README.md up to date

## Processus de review

1. **Manual testing** : The CLI should be tested locally. Verify that the commands work and do not generate errors.
2. **Review by a member of our team** : At least one person must approve the PR. The code must be readable and consistent.
3. **Merge** : A maintainer merges the PR after validation.

## Questions ?

If you have questions not covered in this guide :

- Consult [existing issues](../../issues)
- Open a new issue labeled "question"

## Thanks

Thank you to all the contributors who help improve this project! 🚀

---

By contributing to this project, you agree that your contributions are licensed under the same license as the project.
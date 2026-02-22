# Welcome to `oks-cli`

[![Project Incubating](https://docs.outscale.com/fr/userguide/_images/Project-Incubating-blue.svg)](https://docs.outscale.com/en/userguide/Open-Source-Projects.html)
[![](https://dcbadge.limes.pink/api/server/HUVtY5gT6s?style=flat&theme=default-inverted)](https://discord.gg/HUVtY5gT6s)

<p align="center">
  <img alt="Kubernetes" src="https://upload.wikimedia.org/wikipedia/commons/3/39/Kubernetes_logo_without_workmark.svg" width="120px">
</p>

## 🧭 Overview

**`oks-cli`** is a command-line interface that allows you to deploy and manage Kubernetes clusters on top of OUTSCALE infrastructure using [OKS](https://docs.outscale.com/en/userguide/OUTSCALE-Kubernetes-as-a-Service-OKS.html) (OUTSCALE Kubernetes as a Service).

## 🚀 Usage

Display all available commands:

```bash
oks-cli fullhelp
```

### Commands

A complete description and available options for each commands is available in the [Commands](./commands.md) page

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
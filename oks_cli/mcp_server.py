#!/usr/bin/env python3
import subprocess
import json
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("oks-cli", instructions="OKS (Outscale Kubernetes Service) management tools")


def _run(args: List[str]) -> str:
    cmd = ["oks-cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()
        return json.dumps({"error": error})
    return result.stdout.strip() or json.dumps({"success": True})


# ─── PROJECT ────────────────────────────────────────────────────────────────

@mcp.tool()
def project_list(
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """List all OKS projects. Returns a JSON array of projects."""
    args = ["project", "list", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_get(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """Get details of a specific OKS project by name."""
    args = ["project", "get", "--project-name", project_name, "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_create(
    project_name: str,
    description: Optional[str] = None,
    cidr: Optional[str] = None,
    tags: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Create a new OKS project.

    tags: comma-separated key=value pairs, e.g. 'env=prod,team=ops'.
    cidr: IP range for the project network (e.g. '10.0.0.0/16').
    """
    args = ["project", "create", "--project-name", project_name, "--output", "json"]
    if description:
        args += ["--description", description]
    if cidr:
        args += ["--cidr", cidr]
    if tags:
        args += ["--tags", tags]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_update(
    project_name: str,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    disable_api_termination: Optional[bool] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Update an existing OKS project.

    tags: comma-separated key=value pairs. Pass an empty string to clear all tags.
    disable_api_termination: when True, prevents deletion via API.
    """
    args = ["project", "update", "--project-name", project_name, "--output", "json"]
    if description is not None:
        args += ["--description", description]
    if tags is not None:
        args += ["--tags", tags]
    if disable_api_termination is not None:
        args += ["--disable-api-termination", str(disable_api_termination).lower()]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_delete(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """
    Delete an OKS project by name. This action is irreversible.

    All clusters inside the project must be deleted first.
    """
    args = ["project", "delete", "--project-name", project_name, "--force", "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_quotas(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """Get resource quotas (max/used values) for an OKS project."""
    args = ["project", "quotas", "--project-name", project_name, "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_snapshots(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """List volume snapshots associated with an OKS project."""
    args = ["project", "snapshots", "--project-name", project_name, "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_publicips(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """List public IP addresses allocated to an OKS project."""
    args = ["project", "publicips", "--project-name", project_name, "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def project_nets(
    project_name: str,
    profile: Optional[str] = None,
) -> str:
    """List nets (VPCs) associated with an OKS project."""
    args = ["project", "nets", "--project-name", project_name, "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


# ─── CLUSTER ────────────────────────────────────────────────────────────────

@mcp.tool()
def cluster_list(
    project_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    all_projects: bool = False,
    profile: Optional[str] = None,
) -> str:
    """
    List OKS clusters.

    Set all_projects=True to list clusters across all projects.
    Filter by project_name or cluster_name for narrower results.
    """
    args = ["cluster", "list", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if cluster_name:
        args += ["--cluster-name", cluster_name]
    if all_projects:
        args += ["--all"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_get(
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """Get detailed information about a specific OKS cluster."""
    args = ["cluster", "get", "--cluster-name", cluster_name, "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_create(
    cluster_name: str,
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    admin_whitelist: Optional[str] = None,
    control_plane: Optional[str] = None,
    cidr_pods: Optional[str] = None,
    cidr_service: Optional[str] = None,
    tags: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Create a new OKS Kubernetes cluster.

    admin_whitelist: comma-separated CIDRs allowed to reach the API server.
                     Use 'my-ip' to automatically include your current public IP.
    control_plane: control plane size/plan (e.g. 'small', 'medium').
    cidr_pods: CIDR block for pod networking (e.g. '10.244.0.0/16').
    cidr_service: CIDR block for service networking (e.g. '10.96.0.0/12').
    tags: comma-separated key=value pairs, e.g. 'env=prod,team=ops'.
    """
    args = ["cluster", "create", "--cluster-name", cluster_name, "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if description:
        args += ["--description", description]
    if version:
        args += ["--version", version]
    if admin_whitelist:
        args += ["--admin", admin_whitelist]
    if control_plane:
        args += ["--control-plane", control_plane]
    if cidr_pods:
        args += ["--cidr-pods", cidr_pods]
    if cidr_service:
        args += ["--cidr-service", cidr_service]
    if tags:
        args += ["--tags", tags]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_update(
    cluster_name: str,
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    admin_whitelist: Optional[str] = None,
    control_plane: Optional[str] = None,
    tags: Optional[str] = None,
    disable_api_termination: Optional[bool] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Update an existing OKS cluster configuration.

    admin_whitelist: comma-separated CIDRs. Use 'my-ip' for your current IP.
                     Pass an empty string to clear the whitelist.
    tags: comma-separated key=value pairs. Pass empty string to clear.
    """
    args = ["cluster", "update", "--cluster-name", cluster_name, "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if description is not None:
        args += ["--description", description]
    if version is not None:
        args += ["--version", version]
    if admin_whitelist is not None:
        args += ["--admin", admin_whitelist]
    if control_plane is not None:
        args += ["--control-plane", control_plane]
    if tags is not None:
        args += ["--tags", tags]
    if disable_api_termination is not None:
        args += ["--disable-api-termination", str(disable_api_termination).lower()]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_upgrade(
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Upgrade an OKS cluster to the latest supported Kubernetes version.

    This triggers a rolling upgrade of the control plane and nodes.
    The operation is irreversible — you cannot downgrade after upgrading.
    """
    args = ["cluster", "upgrade", "--cluster-name", cluster_name, "--force", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_delete(
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Delete an OKS cluster by name. This action is irreversible.

    All nodepools and workloads inside the cluster will be destroyed.
    """
    args = ["cluster", "delete", "--cluster-name", cluster_name, "--force", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def cluster_kubeconfig(
    cluster_name: str,
    project_name: Optional[str] = None,
    user: Optional[str] = None,
    group: Optional[str] = None,
    ttl: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Fetch the kubeconfig for an OKS cluster. Returns YAML content.

    ttl: certificate validity duration in human-readable format (e.g. '5h', '1d', '1w').
    user: request a kubeconfig scoped to a specific EIM user.
    group: request a kubeconfig scoped to a specific group.
    """
    args = ["cluster", "kubeconfig", "--cluster-name", cluster_name, "--output", "yaml"]
    if project_name:
        args += ["--project-name", project_name]
    if user:
        args += ["--user", user]
    if group:
        args += ["--group", group]
    if ttl:
        args += ["--ttl", ttl]
    if profile:
        args += ["--profile", profile]
    return _run(args)


# ─── NODEPOOL ───────────────────────────────────────────────────────────────

@mcp.tool()
def nodepool_list(
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """List nodepools in an OKS cluster (uses kubectl under the hood)."""
    args = ["cluster", "--cluster-name", cluster_name]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    args += ["nodepool", "list"]
    return _run(args)


@mcp.tool()
def nodepool_create(
    cluster_name: str,
    nodepool_name: str,
    zones: List[str],
    project_name: Optional[str] = None,
    count: int = 2,
    vmtype: str = "tinav6.c2r4p3",
    profile: Optional[str] = None,
) -> str:
    """
    Create a new nodepool in an OKS cluster.

    zones: list of availability zone names (e.g. ['eu-west-2a']).
    vmtype: VM instance type (default: tinav6.c2r4p3).
    count: desired number of nodes (default: 2).
    """
    args = ["cluster", "--cluster-name", cluster_name]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    args += [
        "nodepool", "create",
        "--nodepool-name", nodepool_name,
        "--count", str(count),
        "--type", vmtype,
    ]
    for zone in zones:
        args += ["--zone", zone]
    return _run(args)


@mcp.tool()
def nodepool_delete(
    cluster_name: str,
    nodepool_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """Delete a nodepool from an OKS cluster. This action is irreversible."""
    args = ["cluster", "--cluster-name", cluster_name]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    args += ["nodepool", "delete", "--nodepool-name", nodepool_name, "--force"]
    return _run(args)


# ─── NETPEERING ─────────────────────────────────────────────────────────────

@mcp.tool()
def netpeering_list(
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """List NetPeerings attached to an OKS cluster (uses kubectl under the hood)."""
    args = ["netpeering", "list", "--cluster-name", cluster_name, "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def netpeering_get(
    netpeering_id: str,
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """Get details of a specific NetPeering by its ID."""
    args = [
        "netpeering", "get",
        "--netpeering-id", netpeering_id,
        "--cluster-name", cluster_name,
        "--output", "json",
    ]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def netpeering_create(
    source_project: str,
    source_cluster: str,
    target_project: str,
    target_cluster: str,
    netpeering_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Create a NetPeering between two OKS clusters.

    A NetPeering connects the networks of two clusters so their pods can communicate.
    Both source and target clusters must be in a Ready state.
    """
    args = [
        "netpeering", "create",
        "--project-name", source_project,
        "--cluster-name", source_cluster,
        "--target-project", target_project,
        "--target-cluster", target_cluster,
        "--force",
        "--output", "json",
    ]
    if netpeering_name:
        args += ["--netpeering-name", netpeering_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def netpeering_delete(
    netpeering_id: str,
    cluster_name: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """Delete a NetPeering by ID. This action is irreversible."""
    args = [
        "netpeering", "delete",
        "--netpeering-id", netpeering_id,
        "--cluster-name", cluster_name,
        "--force",
    ]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


# ─── USER ───────────────────────────────────────────────────────────────────

@mcp.tool()
def user_list(
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """List EIM users provisioned for an OKS project."""
    args = ["user", "list", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def user_create(
    user_type: str,
    project_name: Optional[str] = None,
    ttl: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Create a new EIM user for an OKS project.

    user_type: OKS user role/type (e.g. 'admin', 'viewer').
    ttl: credential validity duration (e.g. '5h', '1d', '1w'). Default is 1w.
    """
    args = ["user", "create", "--user", user_type, "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if ttl:
        args += ["--ttl", ttl]
    if profile:
        args += ["--profile", profile]
    return _run(args)


@mcp.tool()
def user_delete(
    username: str,
    project_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:
    """Delete an EIM user from an OKS project. This action is irreversible."""
    args = ["user", "delete", "--user", username, "--force", "--output", "json"]
    if project_name:
        args += ["--project-name", project_name]
    if profile:
        args += ["--profile", profile]
    return _run(args)


# ─── QUOTAS ─────────────────────────────────────────────────────────────────

@mcp.tool()
def quotas_get(
    profile: Optional[str] = None,
) -> str:
    """Get global OKS resource quotas for the current account."""
    args = ["quotas", "--output", "json"]
    if profile:
        args += ["--profile", profile]
    return _run(args)


def main():
    mcp.run()


if __name__ == "__main__":
    main()

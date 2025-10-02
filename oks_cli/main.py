#!/usr/bin/env python3
import click
import os
import json
import logging
from .project import project
from .cluster import cluster
from .profile import profile
from .cache import cache
from .quotas import quotas

from .utils import ctx_update, install_completions, profile_completer, cluster_completer, project_completer

# Main CLI entry point
@click.group(invoke_without_command=True)
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--verbose', '-v', count=True, help="Increase verbosity")
@click.pass_context
def cli(ctx, project_name, cluster_name, profile, verbose):
    """
    CLI tool to manage projects and clusters.

    You can run commands on two scopes: 'project' and 'cluster'.
    Each scope has several actions like 'list', 'get', 'create', etc.
    """
    ctx_update(ctx, project_name, cluster_name, profile)

    LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()

    if verbose >= 1:
        LOGLEVEL = "INFO"

    if verbose >= 2:
        LOGLEVEL = "DEBUG"

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s',
        level=LOGLEVEL,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("Set loglevel to %s", LOGLEVEL)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

    if not hasattr(ctx, 'obj') or not ctx.obj:
        ctx.obj = dict()

    if project_name != None:
        ctx.obj['project_name'] = project_name

    if cluster_name != None:
        ctx.obj['cluster_name'] = cluster_name

# Register the project and cluster groups with the main CLI
cli.add_command(project)
cli.add_command(cluster)
cli.add_command(profile)
cli.add_command(cache)
cli.add_command(quotas)

def recursive_help(cmd, parent=None):
    """Recursively prints help for all commands and subcommands."""
    ctx = click.core.Context(cmd, info_name=cmd.name, parent=parent)
    click.echo(cmd.get_help(ctx))
    commands = getattr(cmd, 'commands', {})
    for sub in commands.values():
        recursive_help(sub, ctx)

@cli.command('fullhelp', help="Display detailed help information for all commands.")
def fullhelp():
    """Display comprehensive help for all CLI commands."""
    recursive_help(cli)

@cli.command('version', help="Show the current CLI version.")
def version():
    """Display the current CLI version."""
    import importlib.metadata
    click.echo(importlib.metadata.version(__package__))

@cli.command("install-completion", help="Install shell completion scripts.")
@click.option('--type', help="Shell, supported [bash,zsh]")
def install_completion(type):
    """Install shell completion scripts for the CLI."""
    install_completions(type)

if __name__ == '__main__':
    cli()

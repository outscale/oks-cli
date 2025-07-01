import click
from .utils import clear_cache, find_project_id_by_name, find_cluster_id_by_name, get_all_cache, get_expiration_date, ctx_update, login_profile, profile_completer
import prettytable

# DEFINE THE CACHE COMMAND GROUP
@click.group(help="Cache related commands.")
@click.option('--project-name', '-p', required = False, help="Project Name")
@click.option('--cluster-name', '-c', required = False, help="Cluster Name")
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cache(ctx, project_name, cluster_name, profile):
    """CLI command group for cache-related operations."""
    ctx_update(ctx, project_name, cluster_name, profile)

@cache.command('clear', help="Clear cache")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
def delete_cache(force):
    """Clear all cached data, optionally without confirmation."""
    if force or click.confirm("Are you sure you want to clear all cache?", abort=True):
        clear_cache()

@cache.command('kubeconfigs', help="List cached kubeconfigs")
@click.option('--project-name', '-p', required=False, help="Project Name")
@click.option('--cluster-name', '-c', required=False, help="Cluster Name")
@click.option('--plain', is_flag=True, help="Plain table format")
@click.option('--msword', is_flag=True, help="Microsoft Word table format")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def list_kubeconfigs(ctx, project_name, cluster_name, plain, msword, profile):
    """Display cached kubeconfigs with expiration dates in table format."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)

    result = get_all_cache(project_id, cluster_id, "kubeconfig")

    table = prettytable.PrettyTable()
    table.field_names = ["user",  "group", "expiration date"]

    if plain:
        table.set_style(prettytable.PLAIN_COLUMNS)

    if msword:
        table.set_style(prettytable.MSWORD_FRIENDLY)

    for element in result:
        kubeconfig = None
        user = click.style(element['user'], bold=True)
        group = click.style(element['group'], bold=True)

        if element.get("cache_path"):
            with open(element.get("cache_path")) as f:
                kubeconfig = f.read()

        if kubeconfig:
            exp = get_expiration_date(kubeconfig)
            row = user, group, exp

            table.add_row(row)

    click.echo(table)

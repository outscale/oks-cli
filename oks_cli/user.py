import click
import prettytable
from prettytable import TableStyle

from .utils import do_request, print_output, ctx_update, login_profile, profile_completer, \
                   find_project_id_by_name, project_completer


@click.group(help="User related commands.")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def user(ctx, project_name, profile):
    """Group of commands related to user management."""
    ctx_update(ctx, project_name, None, profile)


@user.command('types', help="List available user types")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format")
@click.option('--plain', is_flag=True, help="Plain table format")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def user_types(ctx, project_name, output, plain, profile):
    """Display available user types."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    data = do_request("GET", f'projects/{project_id}/eim_users/types')

    if output:
        print_output(data, output)
        return

    table = prettytable.PrettyTable()
    table.field_names = ["USER TYPE", "DESCRIPTION"]

    if plain:
        table.set_style(TableStyle.PLAIN_COLUMNS)

    for entry in data:
        table.add_row([
            entry.get("UserType", ""),
            entry.get("Description") or "-"
        ])

    click.echo(table)
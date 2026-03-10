import click
import time
from datetime import datetime
import dateutil.parser
import human_readable
import prettytable
import json
import os
from prettytable import TableStyle
from nacl.public import PrivateKey, SealedBox
from nacl.encoding import Base64Encoder

from .utils import do_request, print_output, print_table, find_project_id_by_name, get_project_id, set_project_id, \
                   detect_and_parse_input, transform_tuple, ctx_update, set_cluster_id, get_template, get_project_name, \
                   format_changed_row, is_interesting_status, login_profile, profile_completer, project_completer, \
                   format_row, apply_set_fields

# DEIFNE THE USER COMMAND GROUP
@click.group(help="EIM users related commands.")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def user(ctx, project_name, profile):
    """Group of commands related to project management."""
    ctx_update(ctx, project_name, None, profile)

# LIST USERS
@user.command('list', help="List EIM users")
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--profile', help="Configuration profile to use")
@click.pass_context
def user_list(ctx, output, project_name, profile):
    """List users"""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    data = do_request("GET", f'projects/{project_id}/eim_users')

    if output:
        print_output(data, output)
        return

    field_names = ["USER", "ACCESS KEY", "STATE", "CREATED", "EXPIRATION DATE"]
    table = prettytable.PrettyTable()
    table.field_names = field_names

    for user in data:
        access_keys = user.get("AccessKeys", [])
        access_key = access_keys[0] if access_keys else {}


        state =  access_key.get("State", "N/A")
        if state == 'ACTIVE':
            state = click.style(state, fg='green')
        elif state == "INACTIVE":
            state = click.style(state, fg='red')

        created_at = dateutil.parser.parse(user.get("CreationDate"))
        exp_at = dateutil.parser.parse(access_key.get("ExpirationDate"))
        now = datetime.now(tz=created_at.tzinfo)

        row = [
            user.get("UserName"),
            access_key.get("AccessKeyId", "N/A"),
            state,
            human_readable.date_time(now - created_at),
            human_readable.date_time(now - exp_at)
        ]
        table.add_row(row)

    click.echo(table)
    

@user.command('create', help="Create a new cluster")
@click.option('--project-name', '-p', help="Name of project", type=click.STRING, shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use")
@click.option('--user', '-u', required=True, help="OKS User type")
@click.option('--ttl', type=click.STRING, help="TTL in human readable format (5h, 1d, 1w)")
@click.option('--nacl', is_flag=True, help="Use public key encryption on wire")
@click.pass_context
def user_create(ctx, project_name, output, profile, user, ttl, nacl):
    """Create a new EIM user."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    params = {
        "user": user
    }
    if ttl:
        params["ttl"] = ttl

    if nacl:
        ephemeral = PrivateKey.generate()
        unsealbox = SealedBox(ephemeral)

        headers = {
            'x-encrypt-nacl': ephemeral.public_key.encode(Base64Encoder).decode('ascii')
        }

        raw_data = do_request(
            "POST",
            f'projects/{project_id}/eim_users',
            params=params,
            headers=headers
        )

        decrypted = unsealbox.decrypt(
            raw_data.encode('ascii'),
            encoder=Base64Encoder
        ).decode('ascii')

        data = json.loads(decrypted)

    else:
        data = do_request(
            "POST",
            f'projects/{project_id}/eim_users',
            params=params
        )

    print_output(data, output)

# DELETE USER
@user.command('delete', help="Delete an EIM user")
@click.option('--project-name', '-p', required=False, help="Project name", shell_complete=project_completer)
@click.option('--user', '-u', required=True, help="User name")
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format")
@click.option('--dry-run', is_flag=True, help="Run without any action")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def user_delete(ctx, project_name, user, output, dry_run, force, profile):
    """CLI command to delete an EIM user."""
    
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    if dry_run:
        message = {"message": f"Dry run: The user '{user}' would be deleted."}
        print_output(message, output)
        return

    if force or click.confirm(f"Are you sure you want to delete the user '{user}'?", abort=True):
        data = do_request("DELETE", f"projects/{project_id}/eim_users/{user}")
        print_output(data, output)
    

import click
import time
import datetime
import dateutil.parser
import human_readable
import prettytable
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
@click.option('--project', 'project_name', required = False, help="Project Name")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def user(ctx, project_name, profile):
    """Group of commands related to project management."""
    ctx_update(ctx, project_name, None, profile)

# LIST USERS
@user.command('list', help="List EIM users")
@click.option('--project-name', '-p', help="Name of project", type=click.STRING, shell_complete=project_completer)
@click.option('--output', '-o',  type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use")
@click.pass_context
def user_list(ctx, project_name, output, profile):
    """List users"""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = get_project_id()


    data = do_request("GET", f'projects/{project_id}/eim_users')

    if output:
        print_output(data, output)
        return
    

@user.command('create', help="Create a new cluster")
@click.option('--project-name', '-p', help="Name of project", type=click.STRING, shell_complete=project_completer)
@click.option('--output', '-o',  type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use")
@click.option('--user', required=True, help="OKS User type")
@click.option('--ttl', type=click.STRING, help="TTL in human readable format (5h, 1d, 1w)")
@click.option('--nacl', is_flag=True, help="Use public key encryption on wire")
def user_create(ctx, project_name, output, profile, user, ttl, nacl):
    """List projects with filtering, formatting, and live watch capabilities."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = get_project_id()

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
        raw_data = do_request("POST", f'project/{project_id}/kubeconfig', params = params, headers = headers)['data']['kubeconfig']
        

    if output:
        print_output(data, output)
        return
    
    # print_output(cluster_tdatamplate, output)
    

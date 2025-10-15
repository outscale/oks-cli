import click
import json
import time
from datetime import datetime
import ipaddress
import uuid

from .utils import cluster_completer, do_request, print_output,                 \
                   find_project_id_by_name, find_cluster_id_by_name,            \
                   profile_list, login_profile, cluster_create_in_background,   \
                   ctx_update, set_cluster_id, get_cluster_id, get_project_id,  \
                   get_template, get_cluster_name, format_changed_row,          \
                   is_interesting_status, profile_completer, project_completer, \
                   kubeconfig_parse_fields, print_table, get_project_by_id,     \
                   get_netpeering_acceptance_template, get_netpeering_request_template
from .cluster import _run_kubectl

@click.group(help="NetPeering related commands.")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.pass_context
def netpeering(ctx, profile, project_name, cluster_name, user, group):
    """Group of commands related to netpeering management"""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    ctx.obj['project_id'] = find_project_id_by_name(project_name)
    ctx.obj['cluster_id'] = find_cluster_id_by_name(
        ctx.obj['project_id'], cluster_name)
    ctx.obj['user'] = user
    ctx.obj['group'] = group


@netpeering.command('list', help="List NetPeering")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "wide"]), help="Specify output format")
@click.pass_context
# def netpeering_list(ctx, project_name, cluster_name, user, group, profile):
def netpeering_list(ctx, output):
    """List netpeering in the specified cluster"""
    cmd = ['get', 'netpeerings']
    if output:
        cmd.extend(['-o', output])
    _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'], cmd)

@netpeering.command('delete')
@click.option('--netpeering-id', required=True, type=click.STRING, help="NetPeering to remove")
@click.option('--dry-run', required=False, is_flag=True, help="Run without any action")
@click.pass_context
def netpeering_delete(ctx, netpeering_id, dry_run):
    """Delete a NetPeering between 2 projects"""
    if dry_run:
        message = {"message": f"Dry run: The netpeering {netpeering_id} would be deleted."}
        print_output(message, 'json')
        return
    _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'],
                 ['delete', 'netpeering', netpeering_id])

@netpeering.command('create', help="Create a NetPeering between 2 projects")
@click.option('--from-project', required=True, type=click.STRING, help="Source project name to create netpeering from")
@click.option('--from-cluster', required=True, type=click.STRING, help="Source cluster to create netpeering from")
@click.option('--to-project', required=True, type=click.STRING, help="Project name to create netpeering to")
@click.option('--to-cluster', required=True, type=click.STRING, help="Target cluster to create netpeering to")
@click.option('--netpeering-name', required=False, type=click.STRING, help="Name of the NetPeeringRequest, default to '{from-project}-to-{to-project}",
              default=None)
@click.option('--auto-approve', required=False, is_flag=True, help="Automatically confirm NetPeering acceptance")
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.option('--dry-run', is_flag=True, help="Client dry-run, only print the object that would be sent, without sending it")
@click.option('--output', '-o', type=click.Choice(['json', 'yaml']), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def netpeering_create(ctx, from_project, from_cluster, to_project, to_cluster, netpeering_name, auto_approve,
                      user, group, dry_run, output, profile):
    """Create NetPeering between 2 projects"""
    from_project, from_cluster, profile = ctx_update(ctx, from_project, from_cluster, profile)
    login_profile(profile)

    # First check CIDRs do not overlap
    from_project_id = find_project_id_by_name(from_project)
    to_project_id = find_project_id_by_name(to_project)

    from_project_data = get_project_by_id(from_project_id)
    to_project_data = get_project_by_id(to_project_id)

    from_cidr = ipaddress.ip_network(from_project_data['cidr'])
    to_cidr = ipaddress.ip_network(to_project_data['cidr'])

    if from_cidr.overlaps(to_cidr):
        click.BadParameter("Networks overlap, you can't create netpeering")

    from_cluster_id = find_cluster_id_by_name(from_project_id, from_cluster)
    to_cluster_id = find_cluster_id_by_name(to_project_id, to_cluster)

    # We need VPC ID (network_id) and Account id from target project
    to_nodepool = json.loads(_run_kubectl(to_project_id, to_cluster_id, user, group,
                                 ['get', 'nodepool', '-o', 'json'], capture=True).stdout.decode('utf-8'))
    to_network_id = to_nodepool['items'][0]['metadata']['labels']['oks.network_id']
    to_account_id = to_nodepool['items'][0]['metadata']['labels']['oks.account-id'] #### Be carreful subject to change in near future

    # Generate name
    if not netpeering_name:
        netpeering_name = f"{from_project}-to-{to_project}"
    netpeering_name += f"-{str(uuid.uuid4().fields[-1])[:6]}"
    netpeering_request_name = f"{netpeering_name}-npr"
    netpeering_acceptance_name = f"{netpeering_name}-npa"

    # Create NetPeeringRequest
    netpeering_request = get_netpeering_request_template()
    netpeering_request['metadata']['name'] = f"{netpeering_request_name}"
    netpeering_request['spec']['accepterNetId'] = to_network_id
    netpeering_request['spec']['accepterOwnerId'] = to_account_id

    if dry_run:
        print_output(netpeering_request, output)
        return
    else:
        _run_kubectl(from_project_id, from_cluster_id, "", "",
                     ['create', '-f', '-'], input=json.dumps(netpeering_request))

    # Get the NetPeeringID
    # For security, we wait a bit for the status to be availabe
    time.sleep(3)
    netpeering_request = json.loads(_run_kubectl(from_project_id, from_cluster_id, user, group,
                                    ['get', 'netpeeringrequests', '-o', 'json', f"{netpeering_request_name}"],
                                    capture=True).stdout.decode('utf-8'))

    # Create NetPeeringAcceptance
    netpeering_acceptance = get_netpeering_acceptance_template()
    netpeering_id = netpeering_request['status']['netPeeringId']
    netpeering_acceptance['metadata']['name'] = f"{netpeering_acceptance_name}"
    netpeering_acceptance['spec']['netPeeringId'] = netpeering_id

    netpeering_request_status = netpeering_request['status']['netPeeringState']
    if netpeering_request_status != 'pending-acceptance':
        raise click.ClickException(f"NetPeeringAcceptance is in wrong state: {netpeering_request_status}")

    if auto_approve or click.confirm(f"Are you sure you want to create NetPeering between projects {from_project} and {to_project}?", abort=True):

        _run_kubectl(to_project_id, to_cluster_id, user, group,
                    ["create", "-f", "-"], input=json.dumps(netpeering_acceptance))

        netpeering = _run_kubectl(to_project_id, to_cluster_id, user, group,
                                 ['get', 'netpeering', netpeering_id, '-o', 'json'],
                                 capture=True)

        while netpeering.returncode:
            time.sleep(3)
            netpeering = _run_kubectl(to_project_id, to_cluster_id, user, group,
                                 ['get', 'netpeering', netpeering_id, '-o', 'json'],
                                 capture=True)
        
        netpeering_status = json.loads(netpeering.stdout.decode('utf-8')).get('status').get('netPeeringState')
        if netpeering_status != 'active':
            raise click.ClickException(f"NetPeering is in wrong state: {netpeering_status}")

        click.echo(f"NetPeering {netpeering_id} created between projects '{from_project}' and '{to_project}'")

    else:
        # Delete NetPeeringRequest
        _run_kubectl(from_project, from_cluster, user, group,
                     ["delete", "netpeeringrequests", f"{netpeering_request_name}"])
        click.echo(f"NetPeering {netpeering_request_name} deleted due to abort.")

    return
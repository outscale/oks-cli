import click
import json
import time
from datetime import datetime
import ipaddress
import uuid
from subprocess import CalledProcessError

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


@netpeering.command('list', help="List NetPeering between 2 projects")
@click.option('--status', default="active", type=click.Choice(["active", "deleted", "all"]), help="List NetPeering with this status, default 'active'. Not supported with wide output")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "wide"]), help="Specify output format, default json")
@click.pass_context
def netpeering_list(ctx, status, output):
    """List netpeering in the specified cluster"""
    cmd = ['get', 'netpeerings']
    if output == 'wide':
        cmd.extend(['-o', output])
    else:
        cmd.extend(['-o', 'json'])

    netpeerings = _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'],
                                          cmd, capture=True).stdout.decode('utf-8')
    if output == 'wide':
        click.echo(netpeerings)
        return

    netpeerings = json.loads(netpeerings)
    if status != 'all':
        cnt = 0
        for item in netpeerings.get('items'):
            if item.get('status').get('netPeeringState') != status:
                netpeerings.get('items').pop(cnt)
            cnt+=1

    print_output(netpeerings, output)
    return


@netpeering.command('delete')
@click.option('--netpeering-id', required=True, type=click.STRING, help="NetPeering to remove")
@click.option('--dry-run', required=False, is_flag=True, help="Run without any action")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
@click.pass_context
def netpeering_delete(ctx, netpeering_id, dry_run, force):
    """Delete a NetPeering between 2 projects"""
    if dry_run:
        message = {"message": f"Dry run: The netpeering {netpeering_id} would be deleted."}
        print_output(message, 'json')
        return

    if force or click.confirm(f"Are you sure you want to delet NetPeering with id {netpeering_id}?", abort=True):
        try:
            cmd = _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'],
                        ['delete', 'netpeering', netpeering_id], capture=True)
            if cmd.returncode:
                raise click.ClickException(f"Could not delete NetPeering {netpeering_id}: {cmd.stderr.decode('utf-8')}")
            click.echo(f"It may take some times for NetPeering {netpeering_id} to automatically disappear from both projects. Please be patient")
        except CalledProcessError as e:
            raise click.ClickException(f"Could not delete NetPeering {netpeering_id}: {e}")

def _gather_info(project: str=None, cluster: str=None) -> dict:
    """
        Gather information about project and cluster required to create a NetPeering
        Set:
        - cluster_name
        - project_name
        - project_id
        - cluster_id
        - project_cidr
    """
    info = dict()

    if not project or not cluster:
        raise click.ClickException("Project and cluster name are required")

    info.update({'cluster_name': cluster, 'project_name': project})
    info.update({'project_id': find_project_id_by_name(info.get('project_name'))})
    info.update({'cluster_id': find_cluster_id_by_name(info.get('project_id'), info.get('cluster_name'))})
    info.update({'project_cidr': get_project_by_id(info.get('project_id')).get('cidr')})
    return info

def _check_existing_netpeering(source: dict=None, target: dict=None, user: str=None, group: str=None) -> bool:
    """
        Checks if an existing NetPeering already exists between similar project/cluster id
    """
    # We check if there's not already a NetPeering available and active
    try:
        netpeerings = json.loads(_run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                                            ['get', 'netpeering', '-o', 'json'],
                                            capture=True).stdout.decode('utf-8'))
        for item in netpeerings.get('items'):
            status = item.get('status')
            if status.get('accepterNetId') == target.get('network_id')   and \
               status.get('accepterOwnerId') == target.get('account_id') and \
               status.get('sourceNetId') == source.get('network_id')     and \
               status.get('sourceOwnerId') == source.get('account_id')   and \
               status.get('netPeeringState') == 'active':
               
               click.echo(f"A NetPeering {item.get('spec').get('netPeeringId')} already exists between projects {source.get('project_name')} and {target.get('project_name')}. Aborting!",
                            err=True)
               return True
    except CalledProcessError as e:
        raise click.ClickException(f"Cannot list NetPeerings: {e}")

    return False


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

    source = _gather_info(project=from_project, cluster=from_cluster)
    target = _gather_info(project=to_project, cluster=to_cluster)

    source_cidr = ipaddress.ip_network(source.get('project_cidr'))
    target_cidr = ipaddress.ip_network(target.get('project_cidr'))

    if source_cidr.overlaps(target_cidr) or target_cidr.overlaps(source_cidr):
        click.BadParameter(f"Source network {source.get('project_cidr')} and target network {target.get('project_cidr')} overlap, you can't create netpeering")

    # We need VPC ID (network_id) and Account id from target project
    source_nodepool = json.loads(_run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                                 ['get', 'nodepool', '-o', 'json'], capture=True).stdout.decode('utf-8'))

    target_nodepool = json.loads(_run_kubectl(target.get('project_id'), target.get('cluster_id'), user, group,
                                            ['get', 'nodepool', '-o', 'json'], capture=True).stdout.decode('utf-8'))

    source.update({'network_id': source_nodepool['items'][0]['metadata']['labels']['oks.network_id'],
                   'account_id': source_nodepool['items'][0]['metadata']['labels']['oks.account-id']})

    target.update({'network_id': target_nodepool['items'][0]['metadata']['labels']['oks.network_id'],
                   'account_id': target_nodepool['items'][0]['metadata']['labels']['oks.account-id']})

    if _check_existing_netpeering(source=source, target=target, user=user, group=user):
        return

    # Generate name
    if not netpeering_name:
        netpeering_name = f"{source.get('project_name')}-to-{target.get('project_name')}"
    netpeering_name += f"-{str(uuid.uuid4().fields[-1])[:6]}"
    netpeering_request_name = f"{netpeering_name}-npr"
    netpeering_acceptance_name = f"{netpeering_name}-npa"

    # Create NetPeeringRequest
    netpeering_request = get_netpeering_request_template()
    netpeering_request['metadata']['name'] = f"{netpeering_request_name}"
    netpeering_request['spec']['accepterNetId'] = target.get('network_id')
    netpeering_request['spec']['accepterOwnerId'] = target.get('account_id')

    if dry_run:
        print_output(netpeering_request, output)
        return
    else:
        _run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                     ['create', '-f', '-'], input=json.dumps(netpeering_request))

    # Get the NetPeeringID
    # For security, we wait a bit for the status to be availabe
    time.sleep(3)

    try:
        netpeering_request_cmd = _run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                                        ['get', 'netpeeringrequests', '-o', 'json', f"{netpeering_request_name}"],
                                        capture=True)
        netpeering_request_cmd.check_returncode()
        netpeering_request = json.loads(netpeering_request_cmd.stdout.decode('utf-8'))
    except CalledProcessError as e:
        raise click.ClickException(f"Cannot create NetPeeringRequest: {e}\n{netpeering_request_cmd.stderr}")

    # Create NetPeeringAcceptance
    netpeering_acceptance = get_netpeering_acceptance_template()
    netpeering_id = netpeering_request.get('status').get('netPeeringId')
    netpeering_acceptance['metadata']['name'] = f"{netpeering_acceptance_name}"
    netpeering_acceptance['spec']['netPeeringId'] = netpeering_id

    netpeering_request_status = netpeering_request['status']['netPeeringState']
    if netpeering_request_status != 'pending-acceptance':
        raise click.ClickException(f"NetPeeringAcceptance is in wrong state: {netpeering_request_status}")

    if auto_approve or \
        click.confirm(f"Are you sure you want to create NetPeering between projects {source.get('project_name')} and {target.get('project_name')}?", abort=True):

        try:
            _run_kubectl(target.get('project_id'), target.get('cluster_id'), user, group,
                        ["create", "-f", "-"], input=json.dumps(netpeering_acceptance))

        except CalledProcessError as e:
            raise click.ClickException(f"Could not create netpeering {netpeering_id}: {e}")
        
        # Wait a bit for NetPeering to appear
        netpeering_status = 'pending-acceptance' #json.loads(netpeering.stdout.decode('utf-8')).get('status').get('netPeeringState')
        while netpeering_status != 'active':
            time.sleep(3)
            try:
                netpeering = _run_kubectl(target.get('project_id'), target.get('cluster_id'), user, group,
                                    ['get', 'netpeering', netpeering_id, '-o', 'json'],
                                    capture=True)
                netpeering.check_returncode()
                netpeering_status = json.loads(netpeering.stdout.decode('utf-8')).get('status').get('netPeeringState')
            except CalledProcessError as e:
                raise click.ClickException(f"Could not get NetPeering {netpeering_id} status: {e}")

        print_output(json.loads(netpeering.stdout.decode('utf-8')), output)
        click.echo(f"NetPeering {netpeering_id} successfully created and {netpeering_status} between projects '{source.get('project_name')}' and '{target.get('project_name')}'")

    else:
        # Delete NetPeeringRequest
        _run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                     ["delete", "netpeeringrequests", f"{netpeering_request_name}"])
        click.echo(f"NetPeering {netpeering_request_name} deleted due to abort.")

    return
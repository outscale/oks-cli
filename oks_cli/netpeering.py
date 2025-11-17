import click
import json
import time
import ipaddress
import uuid
from subprocess import CalledProcessError

from .utils import cluster_completer, print_output, find_project_id_by_name,   \
                   find_cluster_id_by_name, login_profile, ctx_update,         \
                   profile_completer, project_completer, find_project_by_name, \
                   do_request, get_cluster_name, get_project_name, get_template
from .cluster import _run_kubectl
from json import JSONDecodeError

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

@netpeering.command('list', help="List NetPeering from a project/cluster")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "wide"]), help="Specify output format")
@click.pass_context
def netpeering_list(ctx, output):
    """List netpeering in the specified cluster"""

    cmd = ['get', 'netpeerings']
    if output:
        cmd.extend(['-o', output])

    _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'], cmd)


@netpeering.command('get', help="Get information about a NetPeering")
@click.option('--netpeering-id', '--name', required=True, type=click.STRING, help="NetPeering to get information from")
@click.option('--output', '-o', default='json', required=False, type=click.Choice(["json", "yaml", "wide"]), help="Specify output format, default json")
@click.pass_context
def netpeering_get(ctx, netpeering_id, output):
    """Retrieve information about a NetPeering"""

    _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'],
                   ['get', 'netpeering', netpeering_id, '-o', output])


@netpeering.command('delete', help="Delete a NetPeering from a project/cluster")
@click.option('--netpeering-id', '--name', required=True, type=click.STRING, help="NetPeering to remove")
@click.option('--dry-run', required=False, is_flag=True, help="Run without any action")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
@click.pass_context
def netpeering_delete(ctx, netpeering_id, dry_run, force):
    """Delete a NetPeering between 2 projects"""
    if dry_run:
        message = {"message": f"Dry run: The netpeering {netpeering_id} would be deleted."}
        print_output(message, 'json')
        return

    if force or click.confirm(f"Are you sure you want to delete NetPeering with id {netpeering_id}?", abort=True):
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

    project_data = find_project_by_name(project)
    info.update({'cluster_name': cluster, 'project_name': project})
    info.update({'project_id': project_data.get('id'), 'project_cidr': project_data.get('cidr')})
    info.update({'cluster_id': find_cluster_id_by_name(info.get('project_id'), info.get('cluster_name'))})
    return info


def _netpeering_exists(source: dict=None, target: dict=None, user: str=None, group: str=None) -> bool:
    """
        Checks if an existing NetPeering already exists between similar project/cluster id
    """
    # We check if there's not already a NetPeering available and active
    if not source or not target:
        raise AttributeError("source and target must be passesd as dict")

    try:
        netpeerings = json.loads(_run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                                            ['get', 'netpeering', '-o', 'json'],
                                            capture=True).stdout.decode('utf-8'))

        for item in netpeerings.get('items'):
            status = item.get('status')
            if status.get('accepterNetId')   == target.get('network_id') and \
               status.get('accepterOwnerId') == target.get('account_id') and \
               status.get('sourceNetId')     == source.get('network_id') and \
               status.get('sourceOwnerId')   == source.get('account_id') and \
               status.get('netPeeringState') == 'active':

                return True

    except CalledProcessError as e:
        raise click.ClickException(f"Cannot list NetPeerings: {e}")

    return False

def _get_vpc_id(project_id: str):
    response = do_request("GET", f"projects/{project_id}/nets")

    if len(response) == 0:
        raise click.ClickException("Cannot get vpc id")

    return response[0]["NetId"]

def _get_iaas_owner_id(project_id: str):
    response = do_request("GET", f"projects/{project_id}/quotas")["data"]

    if len(response["quotas"]) == 0:
        raise click.ClickException("Cannot get iaas owner id")

    return response["quotas"][0]["AccountId"]

def _create_netpeering_request(name: str, source: dict, target: dict, user, group):
    netpeering_request = get_template("netpeeringrequest")
    netpeering_request['metadata']['name'] = name
    netpeering_request['spec']['accepterNetId'] = target.get('network_id')
    netpeering_request['spec']['accepterOwnerId'] = target.get('account_id')

    _run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                    ['create', '-o', 'json', '-f', '-'], input=json.dumps(netpeering_request), capture=True)

    # For security, we wait a bit for the status to be availabe
    time.sleep(3)

    netpeering_request_cmd = _run_kubectl(source.get('project_id'), source.get('cluster_id'), user, group,
                                    ['get', 'netpeeringrequests', '-o', 'json', f"{name}"],
                                    capture=True)
    if netpeering_request_cmd.returncode:
        raise click.ClickException(f"Cannot create NetPeeringRequest: {netpeering_request_cmd.stderr}")

    netpeering_request = json.loads(netpeering_request_cmd.stdout.decode('utf-8'))

    return netpeering_request

def _create_netpeering_acceptance(name: str, netpeering_request_status: dict, target: dict, user, group):

    netpeering_acceptance = get_template("netpeeringacceptance")
    netpeering_id = netpeering_request_status.get('netPeeringId')
    netpeering_acceptance['metadata']['name'] = name
    netpeering_acceptance['spec']['netPeeringId'] = netpeering_id

    netpeering_request_status = netpeering_request_status.get('netPeeringState')
    if netpeering_request_status != 'pending-acceptance':
        raise click.ClickException(f"NetPeeringAcceptance is in wrong state: {netpeering_request_status}")

    netpeering_acceptance_cmd = _run_kubectl(target.get('project_id'), target.get('cluster_id'), user, group,
                                            ["create", "-f", "-"], input=json.dumps(netpeering_acceptance),
                                            capture=True)

    if netpeering_acceptance_cmd.returncode:
        raise click.ClickException(f"Could not create NetPeeringAcceptance object {netpeering_id}: {netpeering_acceptance_cmd.stderr}")

@netpeering.command('create', help="Create a NetPeering between 2 projects")
@click.option('--project-name', '--source-project', '-p', required=False, type=click.STRING, help="Source project name to create netpeering from", shell_complete=project_completer)
@click.option('--cluster-name', '--source-cluster', '-c', required=False, type=click.STRING, help="Source cluster to create netpeering from", shell_complete=cluster_completer)
@click.option('--target-project', required=True, type=click.STRING, help="Project name to create netpeering to", shell_complete=project_completer)
@click.option('--target-cluster', required=True, type=click.STRING, help="Target cluster to create netpeering to")
@click.option('--netpeering-name', required=False, type=click.STRING, help="Name of the NetPeeringRequest, default to '{from-project}-to-{to-project}",
              default=None)
@click.option('--force', required=False, is_flag=True, help="Create netpeering resources without confirmation")
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.option('--dry-run', is_flag=True, help="Client dry-run, only print the object that would be sent, without sending it")
@click.option('--output', '-o', type=click.Choice(['json', 'yaml']), default="json", help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def netpeering_create(ctx, project_name, cluster_name, target_project, target_cluster, netpeering_name, force,
                      user, group, dry_run, output, profile):
    """Create NetPeering between 2 projects"""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_name = get_project_name(project_name)
    cluster_name = get_cluster_name(cluster_name)

    source = _gather_info(project=project_name, cluster=cluster_name)
    target = _gather_info(project=target_project, cluster=target_cluster)

    source_cidr = ipaddress.ip_network(source.get('project_cidr'))
    target_cidr = ipaddress.ip_network(target.get('project_cidr'))

    if source_cidr.overlaps(target_cidr) or target_cidr.overlaps(source_cidr):
        raise click.ClickException(f"Source network {source.get('project_cidr')} and target network {target.get('project_cidr')} overlap, you can't create netpeering. Aborted!")

    source_vpc_id = _get_vpc_id(source.get('project_id'))
    source_iaas_owner_id = _get_iaas_owner_id(source.get('project_id'))

    target_vpc_id = _get_vpc_id(target.get('project_id'))
    target_iaas_owner_id = _get_iaas_owner_id(target.get('project_id'))

    source.update({'network_id': source_vpc_id, 'account_id': source_iaas_owner_id})
    target.update({'network_id': target_vpc_id, 'account_id': target_iaas_owner_id})

    if _netpeering_exists(source=source, target=target, user=user, group=group):
        raise click.ClickException(f"A NetPeering already exists between projects {source.get('project_name')} and {target.get('project_name')}. Aborting!")

    # Generate name
    if not netpeering_name:
        netpeering_name = f"{source.get('project_name')}-to-{target.get('project_name')}"

    netpeering_name += f"-{str(uuid.uuid4().fields[-1])[:6]}"
    netpeering_request_name = f"{netpeering_name}-npr"
    netpeering_acceptance_name = f"{netpeering_name}-npa"

    
    if not force and \
        not click.confirm(f"Are you sure you want to create NetPeering between projects {source.get('project_name')} and {target.get('project_name')}?", abort=False):
        return "Abort."

    netpeering_request = _create_netpeering_request(netpeering_request_name, source, target, user, group)
    netpeering_id = netpeering_request.get('status').get('netPeeringId')

    _create_netpeering_acceptance(netpeering_acceptance_name, netpeering_request.get('status'), target, user, group)

    # Wait a bit for NetPeering to appear
    time.sleep(3)

    _run_kubectl(target.get('project_id'), target.get('cluster_id'), user, group,
                                        ['get', 'netpeering', '-o', output, netpeering_id,])


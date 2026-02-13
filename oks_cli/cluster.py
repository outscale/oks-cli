import click
import subprocess
import json
from nacl.public import PrivateKey, SealedBox
from nacl.encoding import Base64Encoder

import time
import os
from datetime import datetime
import dateutil.parser
import human_readable
import pathlib
import prettytable
import logging
import yaml

from prettytable import TableStyle
from .utils import cluster_completer, do_request, print_output,                 \
                   find_project_id_by_name, find_cluster_id_by_name,            \
                   get_cache, save_cache, detect_and_parse_input,               \
                   verify_certificate, shell_completions, transform_tuple,      \
                   profile_list, login_profile, cluster_create_in_background,   \
                   ctx_update, set_cluster_id, get_cluster_id, get_project_id,  \
                   get_template, get_cluster_name, format_changed_row,          \
                   is_interesting_status, profile_completer, project_completer, \
                   kubeconfig_parse_fields, print_table, format_row, apply_set_fields

from .profile import add_profile
from .project import project_create, project_login

# DEFINE THE CLUSTER GROUP
@click.group(help="Cluster related commands.")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster(ctx, project_name, cluster_name, profile):
    """Group of commands related to cluster management."""
    ctx_update(ctx, project_name, cluster_name, profile)

# LOGIN ON CLUSTER
@cluster.command('login', help="Set a default cluster")
@click.option('--cluster-name', '--name', '-c', required=False, help="Name of cluster", shell_complete=cluster_completer)
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_login(ctx, cluster_name, profile):
    """Set the specified cluster as the default active cluster."""
    _, cluster_name, profile = ctx_update(ctx, None, cluster_name, profile)
    login_profile(profile)

    project_id = get_project_id()
    data = do_request("GET", 'clusters', params={"name": cluster_name, "project_id": project_id})


    if len(data) != 1:
        raise click.BadParameter(
            f"{len(data)} clusters found by name: {cluster_name}")
    cluster = data.pop()

    cluster_id = cluster['id']
    cluster_name = cluster['name']

    set_cluster_id(cluster_id)

    cluster_name = click.style(cluster_name, bold=True)

    click.echo(f"Logged into cluster: {cluster_name}")

# LOGOUT ON CLUSTER
@cluster.command('logout', help="Unset default cluster")
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_logout(ctx, profile):
    """Clear the current default cluster selection."""
    _, _, profile = ctx_update(ctx, None, None, profile)
    login_profile(profile)
    
    current_cluster = get_cluster_id() 

    if not current_cluster:
        click.echo("You are not connected to any cluster.")
        return
    
    set_cluster_id("")
    click.echo("Logged out from the current cluster")

# LIST CLUSTERS
@cluster.command('list', help="List all clusters")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--deleted', '-x', is_flag=True, deprecated="List deleted clusters - Will be removed")  # x pour "deleted" / "removed"
@click.option('--plain', is_flag=True, help="Plain table format")
@click.option('--msword', is_flag=True, help="Microsoft Word table format")
@click.option('--watch', '-w', is_flag=True, help="Watch the changes")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "wide"]), help="Specify output format")
@click.option('--profile', help="Configuration profile to use")
@click.option('--all', '-A', is_flag=True, help="List clusters from all projects")
@click.pass_context
def cluster_list(ctx, project_name, cluster_name, deleted, plain, msword, watch, output, profile, all):
    """Display clusters with optional filtering and real-time monitoring."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    profile_name = os.getenv('OKS_PROFILE')
    region_name = os.getenv('OKS_REGION')
    params = {}

    if not all:
        project_id = find_project_id_by_name(project_name)
        params['project_id'] = project_id

    cluster_id = get_cluster_id()

    if cluster_name:
        params['name'] = cluster_name
    if deleted:
        params['deleted'] = True

    field_names = ["CLUSTER", "PROFILE", "REGION", "CREATED", "UPDATED", "STATUS", "DEFAULT"]

    if all:
        field_names.insert(0, "PROJECT")

        projects = {project["id"]: project for project in do_request("GET", "projects")}
        data = do_request("GET", "clusters/all", params=params)

        for cluster in data:
            project = projects.get(cluster.get("project_id"))
            cluster["project_name"] = project.get("name")
    else:
        data = do_request("GET", "clusters", params=params)

    if output == "wide":
        field_names.insert(0, "ID")
        field_names.append("VERSION")
        field_names.append("CONTROL PLANE")
    elif output:
        print_output(data, output)
        return

    table = prettytable.PrettyTable()
    table.field_names = field_names

    table._min_width = {"CREATED": 13, "UPDATED": 13, "STATUS": 10}

    if plain or watch:
        table.set_style(TableStyle.PLAIN_COLUMNS)

    if msword:
        table.set_style(TableStyle.MSWORD_FRIENDLY)

    initial_clusters = {}

    for cluster in data:
        row, _, name = format_row(cluster.get('statuses'), cluster.get('name'), cluster_id == cluster.get('id'))
        row.insert(1, profile_name)
        row.insert(2, region_name)
        if all:
            project_name = click.style(cluster.get("project_name"), bold=True)
            row.insert(0, project_name)
        if output == "wide":
            row.insert(0, cluster.get('id'))
            row.append(cluster.get('version'))
            row.append(cluster.get('control_planes'))

        table.add_row(row)
        initial_clusters[cluster.get("id")] = cluster

    click.echo(table)

    if watch:
        total_sleep = 0
        try:
            while True:
                time.sleep(2)
                total_sleep += 2

                try:
                    if all:
                        projects = {project["id"]: project for project in do_request("GET", "projects")}
                        data = do_request("GET", "clusters/all", params=params)

                        for cluster in data:
                            project = projects.get(cluster.get("project_id"))
                            cluster["project_name"] = project.get("name")
                    else:
                        data = do_request("GET", 'clusters', params=params)
                except click.ClickException as err:
                    click.echo(f"Error during watch: {err}")
                    continue

                current_cluster_ids = {cluster.get('id') for cluster in data}

                for id, cluster in list(initial_clusters.items()):
                    if id not in current_cluster_ids:
                        deleted_cluster = cluster.copy()
                        deleted_cluster['statuses']['status'] = 'deleted'

                        row, current_status, _ = format_row(deleted_cluster.get('statuses'), deleted_cluster.get('name'), cluster_id == deleted_cluster.get('id'))
                        row.insert(1, profile_name)
                        row.insert(2, region_name)
                        if all:
                            project_name = click.style(cluster.get("project_name"), bold=True)
                            row.insert(0, project_name)

                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        
                        del initial_clusters[id]

                for cluster in data:
                    row, current_status, name = format_row(cluster.get('statuses'), cluster.get('name'), cluster_id == cluster.get('id'))
                    row.insert(1, profile_name)
                    row.insert(2, region_name)
                    if all:
                        project_name = click.style(cluster.get("project_name"), bold=True)
                        row.insert(0, project_name)

                    cl_id = cluster.get('id')

                    if cl_id not in initial_clusters:
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_clusters[cl_id] = cluster
                        continue

                    stored_cluster = initial_clusters[cl_id]
                    cluster_status = stored_cluster.get('statuses').get('status')
                    if cluster_status != current_status:
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_clusters[cl_id] = cluster
                        continue

                    if total_sleep % 10 == 0 and is_interesting_status(current_status):
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_clusters[cl_id] = cluster

        except KeyboardInterrupt:
            click.echo("\nWatch stopped.")


# GET CLUSTER BY NAME
@cluster.command('get', help="Get a cluster by name")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_get_command(ctx, project_name, cluster_name, output, profile):
    """Retrieve and display detailed information about a specific cluster."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)

    data = do_request("GET", f'clusters/{cluster_id}')

    print_output(data, output)


def prepare_cluster_template(cluster_config):
    cluster_template = get_template("cluster")

    if cluster_template.get("project_id") == "":
        cluster_template.pop("project_id", None)

    admin_whitelist = cluster_config.get("admin_whitelist") or []
    if isinstance(admin_whitelist, str):
        admin_whitelist = [admin_whitelist]

    final_whitelist = []

    for entry in admin_whitelist:
        if entry == "my-ip":
            final_whitelist.extend(cluster_template.get("admin_whitelist", []))
        else:
            final_whitelist.append(entry)

    cluster_config["admin_whitelist"] = list(dict.fromkeys(final_whitelist))

    cluster_template.update(cluster_config)
    return cluster_template

def _create_cluster(project_name, cluster_config, output):
    """Create a new cluster with interactive setup for missing profiles/projects."""
    profiles = profile_list()
    ctx = click.get_current_context()

    if profiles == {} and click.confirm("Looks like there is no profile set.\nWould you like to add a profile to proceed with cluster creation?"):

        profile_name = "default"
        region = click.prompt("Choose the region", type=click.Choice(['eu-west-2', 'cloudgouv-eu-west-1'], case_sensitive=False))
        endpoint = None

        if click.confirm("Do you want to use a custom endpoint?"):
            endpoint = click.prompt("Endpoint")

        profile_type = click.prompt("Choose the profile type", type=click.Choice(['ak/sk', 'username'], case_sensitive=False))

        if profile_type == "ak/sk":
            access_key = click.prompt("AccessKey")
            secret_key = click.prompt("SecretKey")
            ctx.invoke(add_profile,
                    profile_name=profile_name,
                    access_key=access_key,
                    secret_key=secret_key,
                    region=region,
                    endpoint=endpoint)
        else:
            username = click.prompt("Username")
            password = click.prompt("Password")
            ctx.invoke(add_profile,
                    profile_name=profile_name,
                    username=username,
                    password=password,
                    region=region,
                    endpoint=endpoint)

        login_profile(profile_name)

        project_name = project_name or "default"
        projects = do_request("GET", 'projects', params={"name": project_name})

        cluster_template = prepare_cluster_template(cluster_config)
        print_output(cluster_template, output)

        project_name_styled = click.style(project_name, bold=True)
        cluster_name_styled = click.style(cluster_template.get("name"), bold=True)

        msg = f"\nYour cluster {cluster_name_styled} is currently being created.\n"

        if len(projects) != 1 and click.confirm(f"Unable to find project: {project_name_styled}\nDo you want create a new project for your cluster?"):
            ctx.invoke(project_create, project_name = project_name, output="silent")
            msg = f"\nYour cluster {cluster_name_styled} and project {project_name_styled} are currently being created.\n"


        project_id = find_project_id_by_name(project_name)
        ctx.invoke(project_login, project_name = project_name)

        cluster_template['project_id'] = project_id

        text = f"{msg}To monitor the progress, please use the following commands.\n\nTo check the progress of project provisioning:\n$ oks-cli project list\n\nAnd to check the progress after cluster provisioning:\n$ oks-cli cluster list\n"

        cluster_create_in_background(cluster_template, text)

    else:
        project_id = find_project_id_by_name(project_name)

        cluster_template = prepare_cluster_template(cluster_config)
        do_request("GET", f'projects/{project_id}')
        cluster_template['project_id'] = project_id

        data = do_request("POST", 'clusters', json=cluster_template)
        print_output(data, output)


# CLUSTER CREATE BY NAME
@cluster.command('create', help="Create a new cluster")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--description', '-d', help="Description of the cluster")
@click.option('--admin', '-a', help="Admin Whitelist ips. you can use 'my-ip' to automatically use your current IP.")
@click.option('--version', '-v', shell_complete=shell_completions, help="Kubernetes version")
@click.option('--cidr-pods', help="CIDR of pods")
@click.option('--cidr-service', help='CIDR of services')
@click.option('--control-plane', shell_complete=shell_completions, help="Controlplane plan")
@click.option('--zone', '-z', multiple=True, shell_complete=shell_completions, help="List of Control Plane availability zones")
@click.option('--enable-admission-plugins', help="List of admission plugins, separated by commas")
@click.option('--disable-admission-plugins', help="List of admission plugins, separated by commas")
@click.option('--quirk', '-q', multiple=True, help="Quirk")
@click.option('--tags', '-t', help="Comma-separated list of tags, example: 'key1=value1,key2=value2'")
@click.option('--disable-api-termination', type=click.BOOL, help="Disable delete action by API")
@click.option('--cp-multi-az', '-m', is_flag=True, help="Enable control plane multi AZ")
@click.option('--dry-run', is_flag=True, help="Client dry-run, only print the object that would be sent, without sending it")
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--filename', '-f', type=click.File("r"), help="Path to file to use to create the cluster ")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.option('--set', 'set_fields', multiple=True, help="Set arbitrary nested fields, e.g. auth.oidc.issuer-url=value")
@click.pass_context
def cluster_create_command(ctx, project_name, cluster_name, description, admin, version, cidr_pods, cidr_service, control_plane, zone, enable_admission_plugins, disable_admission_plugins, quirk, tags, disable_api_termination, cp_multi_az, dry_run, output, filename, profile, set_fields):
    """CLI command to create a new Kubernetes cluster with optional configuration parameters."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    cluster_config = {}

    if filename:
        input_data = filename.read()
        cluster_config = detect_and_parse_input(input_data)

    if not cluster_name and "name" not in cluster_config:
        raise click.BadArgumentUsage("Missing option '--cluster-name' / '-c'.")

    if cluster_name:
        cluster_config['name'] = cluster_name

    if description:
        cluster_config['description'] = description

    if admin:
        cluster_config['admin_whitelist'] = admin.split(',')

    if version:
        cluster_config['version'] = version

    if cidr_pods:
        cluster_config['cidr_pods'] = cidr_pods

    if cidr_service:
        cluster_config['cidr_service'] = cidr_service

    if control_plane:
        cluster_config['control_planes'] = control_plane

    if zone:
        if len(zone) > 1:
            cluster_config['cp_multi_az'] = True
        cluster_config['cp_subregions'] = list(zone) # see kube_quirks section

    if enable_admission_plugins is not None or disable_admission_plugins is not None:
        cluster_config['admission_flags'] = {}

    if enable_admission_plugins is not None:
        cluster_config['admission_flags']['enable_admission_plugins'] = enable_admission_plugins.split(',')

    if disable_admission_plugins is not None:
        cluster_config['admission_flags']['disable_admission_plugins'] = disable_admission_plugins.split(',')
    
    if tags:
        parsed_tags = {}

        pairs = tags.split(',')
        for pair in pairs:
            if '=' not in pair:
                raise click.ClickException(f"Malformed tags: '{pair}' (expected key=value)")
            key, value = pair.split('=', 1)
            parsed_tags[key.strip()] = value.strip()

        cluster_config['tags'] = parsed_tags

    if quirk:
        # Convert the tuple to a list because multiple=True in the decorator returns a tuple
        cluster_config['quirks'] = transform_tuple(quirk)

    if disable_api_termination is not None:
        cluster_config["disable_api_termination"] = disable_api_termination
    
    if cp_multi_az:
        cluster_config["cp_multi_az"] = cp_multi_az

    apply_set_fields(cluster_config, set_fields)

    if not dry_run:
        _create_cluster(project_name, cluster_config, output)
    else:
        cluster_template = prepare_cluster_template(cluster_config)
        print_output(cluster_template, output)

# UPDATE CLUSTER
@cluster.command('update', help="Update a cluster by name")
@click.option('--project-name', '-p', required=False, help="Project name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster name", shell_complete=cluster_completer)
@click.option('--description', '-d', help="Description of the cluster")
@click.option('--admin', '-a', help="Admin Whitelist ips. you can use 'my-ip' to automatically use your current IP.")
@click.option('--version', '-v', shell_complete=shell_completions, help="Kubernetes version")
@click.option('--tags', '-t', help="Comma-separated list of tags, example: 'key1=value1,key2=value2'")
@click.option('--enable-admission-plugins', help="List of admission plugins, separated by commas")
@click.option('--disable-admission-plugins', help="List of admission plugins, separated by commas")
@click.option('--quirk', '-q', multiple=True, help="Quirk")
@click.option('--disable-api-termination', type=click.BOOL, help="Disable delete action by API")
@click.option('--control-plane', shell_complete=shell_completions, help="Controlplane plan")
@click.option('--dry-run', is_flag=True, help="Client dry-run, only print the object that would be sent, without sending it")
@click.option('--output', '-o',  type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--filename', '-f', type=click.File("r"), help="Path to file to use to update the cluster ")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.option('--set', 'set_fields', multiple=True, help="Set arbitrary nested fields, e.g. auth.oidc.issuer-url=value")
@click.pass_context
def cluster_update_command(ctx, project_name, cluster_name, description, admin, version, tags, enable_admission_plugins, disable_admission_plugins, quirk, disable_api_termination, control_plane, dry_run, output, filename, profile, set_fields):
    """CLI command to update an existing Kubernetes cluster with new configuration options."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)

    cluster_config = {}

    if filename:
        input_data = filename.read()
        cluster_config = detect_and_parse_input(input_data)

    if description:
        cluster_config['description'] = description

    if admin is not None:
        if len(admin) == 0:
            cluster_config['admin_whitelist'] = []
        else:
            admin_list = admin.split(',')
            resolved_ips = []
            for ip in admin_list:
                ip = ip.strip()
                if ip == "my-ip":
                    try:
                        data = do_request("GET", "myip")
                        if isinstance(data, dict) and "x_real_ip" in data:
                            resolved_ip = data["x_real_ip"]
                            resolved_ips.append(f"{resolved_ip}/32")
                        else:
                            raise click.ClickException(f"Unexpected response format from 'myip': {data}")
                    except Exception as e:
                        raise click.ClickException(f"Unable to resolve 'my-ip': {e}")
                else:
                    resolved_ips.append(ip)
            cluster_config['admin_whitelist'] = list(dict.fromkeys(resolved_ips))

    if version is not None:
        cluster_config['version'] = version

    if tags is not None:
        parsed_tags = {}

        if not len(tags) == 0:
            pairs = tags.split(',')
            for pair in pairs:
                if '=' not in pair:
                    raise click.ClickException(f"Malformed tags: '{pair}' (expected key=value)")
                key, value = pair.split('=', 1)
                parsed_tags[key.strip()] = value.strip()

        cluster_config['tags'] = parsed_tags

    if enable_admission_plugins is not None or disable_admission_plugins is not None:
         cluster_config['admission_flags'] = {}

    if enable_admission_plugins is not None:
        if len(enable_admission_plugins) == 0:
            cluster_config['admission_flags']['enable_admission_plugins'] = []
        else:
            cluster_config['admission_flags']['enable_admission_plugins'] = enable_admission_plugins.split(',')

    if disable_admission_plugins is not None:
        if len(disable_admission_plugins) == 0:
            cluster_config['admission_flags']['disable_admission_plugins'] = []
        else:
            cluster_config['admission_flags']['disable_admission_plugins'] = disable_admission_plugins.split(',')

    if quirk:
        cluster_config['quirks'] = transform_tuple(quirk)

    if disable_api_termination is not None:
        cluster_config["disable_api_termination"] = disable_api_termination

    if control_plane:
        cluster_config['control_planes'] = control_plane
    
    apply_set_fields(cluster_config, set_fields)

    if dry_run:
        print_output(cluster_config, output)
    else:
        data = do_request("PATCH", f'clusters/{cluster_id}', json=cluster_config)
        print_output(data, output)

# UPGRADE CLUSTER
@cluster.command('upgrade', help="Upgrade a cluster by name")
@click.option('--project-name', '-p', required=False, help="Project name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster name", shell_complete=cluster_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--force', is_flag=True, help="Force upgrade")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_update_command(ctx, project_name, cluster_name, output, force, profile):
    """CLI command to upgrade an existing Kubernetes cluster to the latest supported version."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)
    cluster_name = get_cluster_name(cluster_name)

    if force or click.confirm(f"Are you sure you want to upgrade the cluster with name {cluster_name}?", abort=True):
        data = do_request("PATCH", f'clusters/{cluster_id}/upgrade')
        print_output(data, output)

# DELETE CLUSTER BY NAME
@cluster.command('delete', help="Delete a cluster by name")
@click.option('--project-name', '-p', required=False, help="Project name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster name", shell_complete=cluster_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--dry-run', is_flag=True, help="Run without any action")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_delete_command(ctx, project_name, cluster_name, output, dry_run, force, profile):
    """CLI command to delete an existing Kubernetes cluster by name."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)
    cluster_name = get_cluster_name(cluster_name)

    cluster_login = get_cluster_id()

    if dry_run:
        message = {"message": "Dry run: The cluster would be deleted."}
        print_output(message, output)
        return

    if force or click.confirm(f"Are you sure you want to delete the cluster with name {cluster_name}?", abort=True):
        data = do_request("DELETE", f'clusters/{cluster_id}')
        if cluster_id == cluster_login:
            set_cluster_id("")
        print_output(data, output)

# GET KUBECONFIG
@cluster.command('kubeconfig', help="Fetch the kubeconfig for a cluster")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--print-path', is_flag=True, help="Print path to saved kubeconfig")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "table"]), default="yaml", help="Specify output format, default is yaml")
@click.option('--wide', is_flag=True, help="Prints additional info, only supported for table output")
@click.option('--refresh', '--force', is_flag=True, help="Force refresh saved kubeconfig")
@click.option('--nacl', is_flag=True, help="Use public key encryption on wire (require api support)")
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.option('--ttl', type=click.STRING, help="TTL in human readable format (5h, 1d, 1w)")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def cluster_kubeconfig_command(ctx, project_name, cluster_name, print_path, output, wide, refresh, nacl, user, group, ttl, profile):
    """CLI command to fetch and optionally print the kubeconfig for a specified cluster."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)

    # @TODO: check expiration in get_cache() code, etc
    kubeconfig_path = get_cache(project_id, cluster_id, 'kubeconfig', user, group)

    kubeconfig = None
    is_cert_valid = False

    if kubeconfig_path:
        with open(kubeconfig_path) as f:
            kubeconfig = f.read()

    if kubeconfig:
        is_cert_valid = verify_certificate(kubeconfig)

    if not kubeconfig_path or refresh or not is_cert_valid:
        logging.info("extracting kubeconfig by api")

        params = {}
        if user:
            params["user"] = user
        if group:
            params["group"] = group
        if ttl:
            params["ttl"] = ttl

        if nacl:
            ephemeral = PrivateKey.generate()
            unsealbox = SealedBox(ephemeral)

            headers = {
              'x-encrypt-nacl': ephemeral.public_key.encode(Base64Encoder).decode('ascii')
            }
            kubeconfig_raw = do_request("POST", f'clusters/{cluster_id}/kubeconfig', params = params, headers = headers)['data']['kubeconfig']
        else:
            kubeconfig_raw = do_request("GET", f'clusters/{cluster_id}/kubeconfig', params = params)['data']['kubeconfig']

        if not kubeconfig_raw:
            logging.error("empty response")
            raise SystemExit()
        elif nacl:
            logging.info("decrypting received kubeconfig")
            kubeconfig = unsealbox.decrypt(kubeconfig_raw.encode('ascii'), encoder = Base64Encoder).decode('ascii')
        else:
            kubeconfig = kubeconfig_raw

        kubeconfig_path = save_cache(project_id, cluster_id, 'kubeconfig', kubeconfig, user, group)

    if print_path:
        click.echo(kubeconfig_path)
    else:
        if output == 'table':
            kubeconfig_path = pathlib.Path(kubeconfig_path).absolute()
            if not user:
                user = kubeconfig_path.parts[-3]
            if not group:
                group = kubeconfig_path.parts[-2]
            if kubeconfig_path.is_file():
                with kubeconfig_path.open() as f:
                    kubeconfig_str = f.read()
                kubedata = kubeconfig_parse_fields(kubeconfig_str, cluster_name, user, group)
                if not len(kubedata):
                    raise SystemExit("Something went wrong, could not parse kubeconfig")
                fields = [["user", "user"], ["group", "group"], ["expiration date", "expires_at"]]
                if wide:
                    fields.extend([["Cert subject", "cn"], ["context:name", "context_name"], ["context:user", "ctx_user"],
                                   ["context:cluster", "cluster_name"], ["cluster endpoint", "server_name"]])
                print_table(kubedata, fields)
            else:
                raise SystemExit(f"Could not find {kubeconfig_path}")
        elif output == 'json':
            click.echo(json.dumps(yaml.safe_load(kubeconfig)))
        else:
            click.echo(kubeconfig)


def _run_kubectl(project_id, cluster_id, user, group, args, input=None, capture=False):
    """Run a kubectl command using the cached kubeconfig for the specified cluster, refreshing it if needed."""
    # @TODO: check expiration in get_cache() code, etc
    kubeconfig_path = get_cache(project_id, cluster_id, 'kubeconfig', user, group)

    kubeconfig = None
    is_cert_valid = False

    if kubeconfig_path :
        with open(kubeconfig_path) as f:
            kubeconfig = f.read()

    if kubeconfig:
        is_cert_valid = verify_certificate(kubeconfig)

    if not kubeconfig_path or not is_cert_valid:
        logging.info("extracting kubeconfig by api")

        kubeconfig_raw = do_request(
            "GET", f'clusters/{cluster_id}/kubeconfig')['data']['kubeconfig']

        if not kubeconfig_raw:
            click.echo("Cannot get kubeconfig")
            raise SystemExit()

        kubeconfig_path = save_cache(project_id, cluster_id, 'kubeconfig', kubeconfig_raw, user, group)

    env = dict(os.environ)
    env['KUBECONFIG'] = str(kubeconfig_path)
    cmd = ['kubectl']
    cmd += list(args)
    logging.info("running %s", cmd)
    if not input:
        return subprocess.run(cmd, env=env, capture_output=capture)
    else:
        return subprocess.run(cmd, input=input, text=True, env=env, capture_output=capture)


@cluster.command('kubectl', help='Fetch the kubeconfig for a cluster and run kubectl against it', context_settings={"ignore_unknown_options": True})
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def cluster_kubectl_command(ctx, project_name, cluster_name, user, group, args, profile):
    """CLI command to run kubectl against a specified cluster using its kubeconfig."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    cluster_id = find_cluster_id_by_name(project_id, cluster_name)

    _run_kubectl(project_id, cluster_id, user, group, args)


@click.group(help="Nodepool related commands.")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--cluster-name', '--name', '-c', required=False, help="Cluster Name", shell_complete=cluster_completer)
@click.option('--user', type=click.STRING, help="User")
@click.option('--group', type=click.STRING, help="Group")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def nodepool(ctx, project_name, cluster_name, user, group, profile):
    """CLI group for nodepool-related commands, managing project, cluster, user, and profile context."""
    project_name, cluster_name, profile = ctx_update(ctx, project_name, cluster_name, profile)
    login_profile(profile)

    ctx.obj['project_id'] = find_project_id_by_name(project_name)
    ctx.obj['cluster_id'] = find_cluster_id_by_name(
        ctx.obj['project_id'], cluster_name)
    ctx.obj['user'] = user
    ctx.obj['group'] = group


cluster.add_command(nodepool)


@nodepool.command('list')
@click.pass_context
def nodepool_list(ctx):
    """List nodepools in the specified cluster using kubectl."""
    _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'], [
                 'get', 'nodepool', '-o', 'wide'])


@nodepool.command('create', help="Create a new nodepool")
@click.option('--nodepool-name', '-n', default="nodepool01", help="Nodepool Name")
@click.option('--count', '-c', default=2, help="Count of nodes")
@click.option('--type', 'vmtype', '-t', default="tinav6.c2r4p3", help="Type of VMs")
@click.option('--zone', '-z', multiple=True, help="Provide zone(s)")
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--dry-run', is_flag=True, help="Run without any action")
@click.option('--filename', '-f', type=click.File("r"), help="Path to file to use to create the Nodepool")
@click.pass_context
def setup_worker_pool(ctx, nodepool_name, count, vmtype, zone, output, dry_run, filename):
    """Create a new nodepool in the cluster, optionally from a file or parameters."""
    nodepool = get_template("nodepool")

    if filename:
        input_data = filename.read()
        nodepool = detect_and_parse_input(input_data)
    else:
        nodepool['metadata']["name"] = nodepool_name
        nodepool['spec']["desiredNodes"] = count
        nodepool['spec']["nodeType"] = vmtype
        if zone:
            nodepool['spec']["zones"] = list(zone)

    if not nodepool['spec']["zones"]:
        raise click.BadArgumentUsage("Missing option '--zone' / '-z'.")

    if dry_run:
        print_output(nodepool, output)
    else:
        _run_kubectl(ctx.obj['project_id'], ctx.obj['cluster_id'], ctx.obj['user'], ctx.obj['group'], [
                 'create', '-f', '-'], input=json.dumps(nodepool))


@nodepool.command('delete')
@click.option('--nodepool-name', '-n', required=True, help="Nodepool Name")
@click.option('--force', is_flag=True, help="Delete without confirmation")
@click.pass_context
def delete_worker_pool(ctx, nodepool_name, force):
    """Delete a nodepool by name from the cluster."""

    if not force:
        click.confirm(
            f"Are you sure you want to delete the nodepool '{nodepool_name}'?",
            abort=True
        )

    _run_kubectl(
        ctx.obj['project_id'],
        ctx.obj['cluster_id'],
        ctx.obj['user'],
        ctx.obj['group'],
        ['delete', 'nodepool', nodepool_name]
    )

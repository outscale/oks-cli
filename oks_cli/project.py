import click
import time
from datetime import datetime
import dateutil.parser
import human_readable
import prettytable
import os
from prettytable import TableStyle

from .utils import do_request, print_output, print_table, find_project_id_by_name, get_project_id, set_project_id, \
                   detect_and_parse_input, transform_tuple, ctx_update, set_cluster_id, get_template, get_project_name, \
                   format_changed_row, is_interesting_status, login_profile, profile_completer, project_completer, \
                   format_row, format_status

# DEIFNE THE PROJECT COMMAND GROUP
@click.group(help="Project related commands.")
@click.option('--project', 'project_name', required = False, help="Project Name")
@click.option('--project-name', '-p', required=False, help="Project Name", shell_complete=project_completer)
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project(ctx, project_name, profile):
    """Group of commands related to project management."""
    ctx_update(ctx, project_name, None, profile)

# LOGIN ON PROJECT
@project.command('login', help="Set a default project by name")
@click.option('--project-name', '-p', required=False, help="Name of project", type=click.STRING, shell_complete=project_completer)
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_login(ctx, project_name, profile):
    """Set a default project by its name and log in."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    data = do_request("GET", 'projects', params={"name": project_name})
    if len(data) != 1:
        raise click.BadParameter(
            f"{len(data)} projects found by name: {project_name}")
    project = data.pop()

    project_id = project['id']
    project_name = project['name']

    set_project_id(project_id)
    set_cluster_id("")

    project_name = click.style(project_name, bold=True)

    click.echo(f"Logged into project: {project_name}")

# LOGOUT ON PROJECT
@project.command('logout', help="Unset default project")
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_logout(ctx, profile):
    """Unset the current default project and log out."""
    _, _, profile = ctx_update(ctx, None, None, profile)
    login_profile(profile)
    set_project_id("")
    set_cluster_id("")
    click.echo("Logged out from the current project")

# LIST PROJECTS
@project.command('list', help="List all projects")
@click.option('--project-name', '-p', help="Name of project", type=click.STRING, shell_complete=project_completer)
@click.option('--deleted', '-x', is_flag=True, help="List deleted projects")
@click.option('--plain', is_flag=True, help="Plain table format")
@click.option('--msword', is_flag=True, help="Microsoft Word table format")
@click.option('--uuid', is_flag=True, help="Show UUID")
@click.option('--watch', '-w', is_flag=True, help="Watch the changes")
@click.option('--output', '-o',  type=click.Choice(["json", "yaml", "table"]), help="Specify output format, by default is table")
@click.option('--profile', help="Configuration profile to use")
@click.pass_context
def project_list(ctx, project_name, deleted, plain, msword, uuid, watch, output, profile):
    """List projects with filtering, formatting, and live watch capabilities."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    profile_name = os.getenv('OKS_PROFILE')
    region_name = os.getenv('OKS_REGION')
    project_id = get_project_id()

    params = {}
    if project_name:
        params['name'] = project_name

    if deleted:
        params['deleted'] = True

    data = do_request("GET", 'projects', params=params)

    if output in ["json", "yaml"]:
        print_output(data, output)
        return

    field_names = ["PROJECT", "PROFILE", "REGION", "CREATED", "UPDATED", "STATUS", "DEFAULT"]
    if uuid:
        field_names.append('UUID')

    table = prettytable.PrettyTable()
    table.field_names = field_names

    table._min_width = {"CREATED": 13, "UPDATED": 13, "STATUS": 10}

    if plain or watch:
        table.set_style(TableStyle.PLAIN_COLUMNS)

    if msword:
        table.set_style(prettytable.MSWORD_FRIENDLY)

    initial_projects = {}

    for project in data:
        row, _, name = format_row(project, project.get('name'), project_id == project.get('id'))
        row.insert(1, profile_name)
        row.insert(2, region_name)
        if uuid:
            row.append(project.get('id'))
        table.add_row(row)
        initial_projects[name] = project

    click.echo(table)

    if watch:
        total_sleep = 0
        try:
            while True:
                time.sleep(2)
                total_sleep += 2
                try:
                    data = do_request("GET", 'projects', params=params)
                except click.ClickException as err:
                    click.echo(f"Error during watch: {err}")
                    continue

                current_project_names = {project['name'] for project in data}

                for name, project in list(initial_projects.items()):
                    if name not in current_project_names:
                        deleted_project = project.copy()
                        deleted_project['status'] = 'deleted'

                        row, current_status, _ = format_row(deleted_project, deleted_project.get('name'), project_id == deleted_project.get('id'))
                        row.insert(1, profile_name)
                        row.insert(2, region_name)
                        new_table = format_changed_row(table, row)

                        click.echo(new_table)

                        del initial_projects[name]

                for project in data:
                    row, current_status, name = format_row(project, project.get('name'), project_id == project.get('id'))
                    row.insert(1, profile_name)
                    row.insert(2, region_name)

                    if name not in initial_projects:
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_projects[name] = project
                        continue

                    stored_project = initial_projects[name]
                    project_status = stored_project.get('status')
                    if project_status != current_status:
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_projects[name] = project
                        continue

                    if total_sleep % 10 == 0 and is_interesting_status(current_status):
                        new_table = format_changed_row(table, row)
                        click.echo(new_table)
                        initial_projects[name] = project

        except KeyboardInterrupt:
            click.echo("\nWatch stopped.")

# CREATE PROJECT BY NAME
@project.command('create', help="Create a new project")
@click.option('--project-name', '-p', help="Name of the project", type=click.STRING, shell_complete=project_completer)
@click.option('--description', '-d', help="Description of the project")
@click.option('--cidr', help='CIDR for the project')
@click.option('--quirk', '-q', multiple=True, help="Quirk")
@click.option('--tags', '-t', help="Comma-separated list of tags, example: 'key1=value1,key2=value2'")
@click.option('--disable-api-termination', type=click.BOOL, help="Disable delete action by API")
@click.option('--dry-run', is_flag=True, help="Client dry-run, only print the object that would be sent, without sending it")
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "silent"]), help="Specify output format, by default is json")
@click.option('--filename', '-f', type=click.File("r"), help="Path to file to use to create the project")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_create(ctx, project_name, description, cidr, quirk, tags, disable_api_termination, dry_run, output, filename, profile):
    """Create a new project from options or file, with support for dry-run and output formatting."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_config = None

    if filename:
        input_data = filename.read()
        project_config = detect_and_parse_input(input_data)
    else:
        project_config = get_template("project")
        if os.getenv("OKS_REGION"):
            project_config["region"] = os.getenv("OKS_REGION")

    if project_name:
        project_config['name'] = project_name

    if description:
        project_config['description'] = description

    if cidr:
        project_config['cidr'] = cidr

    if quirk:
        project_config['quirks'] = transform_tuple(quirk)
    
    if tags:
        parsed_tags = {}

        pairs = tags.split(',')
        for pair in pairs:
            if '=' not in pair:
                raise click.ClickException(f"Malformed tags: '{pair}' (expected key=value)")
            key, value = pair.split('=', 1)
            parsed_tags[key.strip()] = value.strip()

        project_config['tags'] = parsed_tags

    if disable_api_termination is not None:
        project_config["disable_api_termination"] = disable_api_termination

    if not dry_run:
        data = do_request("POST", 'projects', json=project_config)
        print_output(data, output)
    else:
        print_output(project_config, output)

# GET PROJECT BY NAME
@project.command('get', help="Get default project or the project by name")
@click.option('--project-name', '-p', help="Name of the project", shell_complete=project_completer)
@click.option('--output', '-o', default="json", type=click.Choice(["json", "yaml", "table"]), help="Specify output format, by default is json")
@click.option('--tags', is_flag=True, help="Show tags in table format output")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_get(ctx, project_name, output, profile, tags):
    """Retrieve and display project details by name or default project."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    data = do_request("GET", f'projects/{project_id}')

    if output in ["json", "yaml"]:
        print_output(data, output)
    else:
        fields = [["PROJECT", "name"], ["PROFILE", "profile"], ["CIDR", "cidr"], ["REGION", "region"], ["CREATED", "created_at"],
                  ["UPDATED", "updated_at"], ["STATUS", "status"]]
        created_at = dateutil.parser.parse(data.get('created_at'))
        updated_at = dateutil.parser.parse(data.get('updated_at'))
        now = datetime.now(tz=created_at.tzinfo)

        data.update({"created_at": human_readable.date_time(now - created_at)})
        data.update({"updated_at": human_readable.date_time(now - updated_at)})
        data.update({"status": format_status(status=data.get('status'))})
        data.update({"profile": profile or os.getenv('OKS_PROFILE')})
        print_table([data], table_fields=fields)
        if tags:
            fields = [["TAG KEY", "tag_key"], ["TAG VALUE", "tag_value"]]
            tag_dict = data.get('tags')
            tags = list()
            for k in tag_dict.keys():
                tags.append({"tag_key": k, "tag_value": tag_dict.get(k)})
            print_table(tags, table_fields=fields)


# DELETE PROJECT BY NAME
@project.command('delete', help="Delete a project by name")
@click.option('--project-name', '-p', required=False, help="Project Name", type=click.STRING, shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "table"]), help="Specify output format, by default is table")
@click.option('--dry-run', is_flag=True, help="Run without any action")
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_delete_command(ctx, project_name, output, dry_run, force, profile):
    """Delete a project by name, with optional dry-run and confirmation."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)
    project_name = get_project_name(project_name)

    current_project_id = get_project_id()

    if dry_run:
        message = {"message": "Dry run: The project would be deleted."}
        if output in ["json", "yaml"]:
            print_output(message, output)
        else:
            print_table([{"name": project_name, "message": message.get('message')}],
                        [["PROJECT", "name"], ["MESSAGE", "message"]], align="c")
        return

    if force or click.confirm(f"Are you sure you want to delete the project with name {project_name}?", abort=True):
        data = do_request("DELETE", f'projects/{project_id}')
        if current_project_id == project_id:
            set_project_id("")
            set_cluster_id("")
        if output in ["json", "yaml"]:
            print_output(data, output)
        else:
            data.update({"name": project_name})
            print_table([data], [["PROJECT", "name"], ["MESSAGE", "Details"]], align="c")


# UPDATE PROJECT BY NAME
@project.command('update', help="Update a project by name")
@click.option('--project-name', '-p', required=False, help="Project Name", type=click.STRING, shell_complete=project_completer)
@click.option('--description', '-d', help="Description of the project")
@click.option('--quirk', '-q', multiple=True, help="Quirk")
@click.option('--tags', '-t', help="Comma-separated list of tags, example: 'key1=value1,key2=value2'")
@click.option('--disable-api-termination', type=click.BOOL, help="Disable delete action by API")
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--dry-run', is_flag=True, help="Run without any action")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_update_command(ctx, project_name, description, quirk, tags, disable_api_termination, output, dry_run, profile):
    """Update project details by name, supporting dry-run and output formatting."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    project_config = {}

    if disable_api_termination is not None:
        project_config["disable_api_termination"] = disable_api_termination

    if description:
        project_config['description'] = description

    if quirk:
        project_config['quirks'] = transform_tuple(quirk)

    if tags is not None:
        parsed_tags = {}

        if not len(tags) == 0:
            pairs = tags.split(',')
            for pair in pairs:
                if '=' not in pair:
                    raise click.ClickException(f"Malformed tags: '{pair}' (expected key=value)")
                key, value = pair.split('=', 1)
                parsed_tags[key.strip()] = value.strip()

        project_config['tags'] = parsed_tags

    if dry_run:
        if output in ["json", "yaml"]:
            print_output(project_config, output)
        else:
            print_table([{"name": project_name, "updated": project_config}],
                        table_fields=[["PROJECT", "name"], ["FIELD TO UPDATE (dry run)", "updated"]])
    else:
        data = do_request("PATCH", f'projects/{project_id}', json = project_config)
        if output in ["json", "yaml"]:
            print_output(data, output)
        else:
            fields = [["PROJECT", "name"], ["PROFILE", "profile"], ["CIDR", "cidr"], ["REGION", "region"], ["CREATED", "created_at"],
                      ["UPDATED", "updated_at"], ["STATUS", "status"]]
            created_at = dateutil.parser.parse(data.get('created_at'))
            updated_at = dateutil.parser.parse(data.get('updated_at'))
            now = datetime.now(tz=created_at.tzinfo)

            data.update({"created_at": human_readable.date_time(now - created_at)})
            data.update({"updated_at": human_readable.date_time(now - updated_at)})
            data.update({"status": format_status(status=data.get('status'))})
            data.update({"profile": profile or os.getenv('OKS_PROFILE')})
            print_table([data], table_fields=fields)

            # Print table for tags
            fields = [["TAG KEY", "tag_key"], ["TAG VALUE", "tag_value"]]
            tag_dict = data.get('tags')
            tags = list()
            for k in tag_dict.keys():
                tags.append({"tag_key": k, "tag_value": tag_dict.get(k)})
            print_table(tags, table_fields=fields)


# GET PROJECT QUOTAS BY PROJECT NAME
@project.command('quotas', help="Get project quotas")
@click.option('--project-name', '-p', help="Name of the project", shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml", "table"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_get_quotas(ctx, project_name, output, profile):
    """Retrieve resource quotas for the specified project."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    data = do_request("GET", f'projects/{project_id}/quotas')["data"]
    if output == "table":
        print_table(data["quotas"], [["Name", "Name"],
                                     ["Collection", "QuotaCollection"],
                                     ["Description", "ShortDescription"],
                                     ["Max Value", "MaxValue"],
                                     ["Used Value", "UsedValue"]])
        print_table(data["subregions"], [["Region", "RegionName"],
                                         ["Availability Zone", "SubregionName"],
                                         ["State", "State"]])

    else:
        print_output(data, output)


# GET PROJECT SNAPSHOTS BY PROJECT NAME
@project.command('snapshots', help="Get project snapshots")
@click.option('--project-name', '-p', help="Name of the project", shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile', help="Configuration profile to use", shell_complete=profile_completer)
@click.pass_context
def project_get(ctx, project_name, output, profile):
    """Retrieve snapshots associated with the specified project."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    response = do_request("GET", f'projects/{project_id}/snapshots')
    print_output(response, output)

# GET PUBLIC IPS BY PROJECT NAME
@project.command('publicips', help="Get project public ips")
@click.option('--project-name', '-p', help="Name of the project", shell_complete=project_completer)
@click.option('--output', '-o', type=click.Choice(["json", "yaml"]), help="Specify output format, by default is json")
@click.option('--profile',help="Configuration profile to use")
@click.pass_context
def project_get_public_ips(ctx, project_name, output, profile):
    """Retrieve the list of public IPs associated with the specified project."""
    project_name, _, profile = ctx_update(ctx, project_name, None, profile)
    login_profile(profile)

    project_id = find_project_id_by_name(project_name)

    data = do_request("GET", f'projects/{project_id}/public_ips')
    print_output(data, output)
import click
import prettytable
from .utils import set_profile, remove_profile, profile_list, DEFAULT_API_URL, get_profiles, print_output


# DEFINE THE PROFILE COMMAND GROUP
@click.group(help="Profile related commands.")
def profile():
    """Profile management command group."""
    pass


@profile.command('add', help="Add AK/SK or username/password new profile")
@click.option('--profile-name', required=False, help="Name of profile, optional", type=click.STRING)
@click.option('--access-key', required=False, help="AK of profile", type=click.STRING)
@click.option('--secret-key', required=False, help="SK of profile", type=click.STRING)
@click.option('--username', required=False, help="Username", type=click.STRING)
@click.option('--password', required=False, help="Password", type=click.STRING)
@click.option('--region', required=True, help="Region name", type=click.Choice(['eu-west-2', 'cloudgouv-eu-west-1']))
@click.option('--endpoint', required=False, help="API endpoint", type=click.STRING)
@click.option('--jwt', required=False, help="Enable jwt, by default is false", type=click.BOOL)
def add_profile(profile_name, access_key, secret_key, username, password, region, endpoint, jwt):
    """Add a new profile with AK/SK or username/password authentication."""
    if not profile_name:
        profile_name = "default"

    existing_profiles = get_profiles()
    if profile_name in existing_profiles:
        confirm = click.confirm(
            f"The profile '{profile_name}' already exists. Do you want to replace it?",
            default=False
        )
        if not confirm:
            click.echo("Aborted.")
            return

    obj = {
        "region_name": region
    }

    if endpoint:
        obj["endpoint"] = endpoint

    if access_key and secret_key:
        obj["type"] = "ak/sk"
        obj["access_key"] = access_key
        obj["secret_key"] = secret_key

    elif username and password:
        obj["type"] = "username/password"
        obj["username"] = username
        obj["password"] = password
    else:
        raise click.UsageError("--access-key and --secret-key or --username and --password must be specified")

    if jwt is not None:
        obj["jwt"] = jwt

    set_profile(profile_name, obj)

    profile_name_styled = click.style(profile_name, bold=True)
    click.echo(f"Profile {profile_name_styled} has been successfully added")

@profile.command('update', help="Update an existing profile")
@click.option('--profile-name', required=True, help="Name of profile", type=click.STRING)
@click.option('--region', required=False, help="Region name", type=click.Choice(['eu-west-2', 'cloudgouv-eu-west-1']))
@click.option('--endpoint', required=False, help="API endpoint", type=click.STRING)
@click.option('--jwt', required=False, help="Enable jwt, by default is false", type=click.BOOL)
def update_profile(profile_name, region, endpoint, jwt):
    """Update configuration settings for an existing profile."""
    profiles = profile_list()
    if profile_name not in profiles:
        raise click.ClickException(f"There no profile with name: {profile_name}")

    profile = profiles[profile_name]
    if region:
        profile["region_name"] = region

    if endpoint:
        profile["endpoint"] = endpoint

    if jwt is not None:
        profile["jwt"] = jwt

    set_profile(profile_name, profile)

    profile_name = click.style(profile_name, bold=True)

    click.echo(f"Profile {profile_name} has been successfully updated")

@profile.command('delete', help="Delete a profile by name")
@click.option('--profile-name', required=True, help="Name of profile", type=click.STRING)
@click.option('--force', is_flag=True, help="Force deletion without confirmation")
def delete_profile(profile_name, force):
    """Delete a profile with confirmation."""
    profiles = profile_list()
    profile_name_bold = click.style(profile_name, bold=True)

    if profile_name not in profiles:
        raise click.ClickException(f"There no profile with name: {profile_name_bold}")

    if force or click.confirm(f"Are you sure you want to delete the profile with name {profile_name_bold}?", abort=True):
        remove_profile(profile_name)
        click.echo(f"Profile {profile_name_bold} has been successfully deleted")

@profile.command('list', help="List existing profiles")
@click.option('-o', '--output', type=click.Choice(["json", "yaml", "wide"]), help="Specify output format")
def list_profiles(output):
    """Display all configured profiles with their settings."""
    profiles = profile_list()

    if not profiles:
        return click.echo("There are no profiles")

    profiles_keys = list(profiles.keys())
    lines = list()
    for key in profiles_keys:
        if 'endpoint' not in profiles[key]:
            if 'region_name' in profiles[key]:
                endpoint = DEFAULT_API_URL.format(region=profiles[key]['region_name'])
            else:
                endpoint = None
        else:
            endpoint = profiles[key]["endpoint"]

        name = key
        account_type = profiles[key]["type"]
        region = profiles[key]["region_name"]
        jwt = profiles[key].get("jwt", False)
        # Remove credentials keys from profiles
        profiles[key].pop('access_key', None)
        profiles[key].pop('secret_key', None)
        profiles[key].pop('username', None)
        profiles[key].pop('password', None)
        # Add endpoint and JWT to dict
        profiles[key].update({'endpoint': endpoint})
        profiles[key].update({'jwt_auth': profiles[key].get("jwt", False)})

        if output == 'wide':
            lines.append("Profile: {} Account type: {} Region: {} Endpoint: {} Enabled JWT auth: {}".format(
                         click.style(name, bold=True),
                         click.style(account_type, bold=True),
                         click.style(region, bold=True),
                         click.style(endpoint, bold=True),
                         click.style(jwt, bold=True)))
        else:
            lines.append([name, account_type, region, endpoint, jwt])
    
    if output in ["json", "yaml"]:
        print_output(profiles, output)
        return
    elif output == 'wide':
        for line in lines:
            click.echo(line)
    else:
        table = prettytable.PrettyTable()
        table.field_names = ["PROFILE", "ACCOUNT TYPE", "REGION", "ENDPOINT", "JWT ENABLED"]
        table.add_rows(lines)
        click.echo(table)


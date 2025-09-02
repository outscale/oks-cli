import click
import os
import subprocess
import logging
import requests
from urllib.parse import urljoin, urlencode
import re
import yaml
import json
import pathlib
import traceback
import time
from datetime import datetime
import OpenSSL
import shutil
import prettytable

import base64
import sys

from click.shell_completion import CompletionItem


def get_config_path():
    CONFIG_FOLDER = os.path.expanduser('~/.oks_cli')
    if not os.path.exists(CONFIG_FOLDER):
        os.makedirs(CONFIG_FOLDER)

    PROFILE_FILE = f"{CONFIG_FOLDER}/config.json"
    return CONFIG_FOLDER, PROFILE_FILE

DEFAULT_API_URL = "https://api.{region}.oks.outscale.com/api/v2/"

class JSONClickException(click.ClickException):
    def show(self, file=None):
        click.echo(self.message, file=file)


def find_response_object(data):
    """Extract the main object from the API response payload."""
    response = data.json()

    if isinstance(response, dict):
        keys = list(response.keys())
        keys.remove("ResponseContext")
        
        key = keys.pop()
        if key == "Cluster":
            return response["Cluster"]
        elif key == "Clusters":
            return response["Clusters"]
        elif key == "Project":
            return response["Project"]
        elif key == "Projects":
            return response["Projects"]
        elif key == "detail":
            return {"Details": response["detail"]}
        elif key == "Details":
            return {"Details": response["Details"]}
        elif key == "ControlPlanes":
            return response["ControlPlanes"]
        elif key == "Versions":
            return response["Versions"]
        elif key == "CPSubregions":
            return response["CPSubregions"]
        elif key == "Template":
            return response["Template"]
        elif key == "Quotas":
            return response["Quotas"]
        elif key == "Snapshots":
            return response["Snapshots"]
        elif key == "PublicIps":
            return response["PublicIps"]

    raise click.ClickException("The API response format is incorrect.")

def do_request(method, path, *args, **kwargs):
    """Perform an HTTP request to the API with authentication and error handling."""
    api_url = os.environ.get("OKS_ENDPOINT")

    logging.debug("method: %s path: %s args: %s kwargs: %s", method, path, args, kwargs)

    url = urljoin(api_url, path)

    headers = build_headers()

    kwargs.setdefault('headers', {}).update(headers)

    logging.info("%s request %s?%s", method, url,
                 urlencode(kwargs.get('params', {})))

    retries = int(os.getenv('OKS_RETRIES', 3)) if method.upper() == "GET" else 1
    backoff = 1

    for attempt in range(1, retries + 1):
        try:
            data = requests.request(method, url, *args, **kwargs)
            logging.info("response %s %s %s...", data.status_code,
                        data.reason, data.text[:50])
            data.raise_for_status()
            save_tokens(data.headers)
            obj = find_response_object(data)
            return obj
        except requests.exceptions.HTTPError as err:
            otp_response = handle_otp_error(err, lambda: do_request(method, path, *args, **kwargs))
            if otp_response is not None:
                return otp_response

            jwt_response = handle_jwt_error(err, method, path, args, kwargs)
            if jwt_response is not None:
                return jwt_response

            if attempt < retries and method.upper() == "GET":
                logging.info("GET failed (attempt %s/%s), retrying in %s sec...", attempt, retries, backoff)
                time.sleep(backoff)
                backoff *= 2  # exponential backoff
                continue

            logging.debug(traceback.format_stack(limit = 4))
            raise JSONClickException(err.response.text)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
            errors = {"Error": f"Failed to reach the endpoint {url} ({err.__class__.__name__})"}
            raise JSONClickException(json.dumps(errors))

def build_headers():
    """Build HTTP headers for API requests based on environment authentication settings."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if os.getenv("OKS_OTP_CODE"):
        headers["X-OTP-Code"] =  os.getenv("OKS_OTP_CODE")

    if os.getenv("OKS_DEV_HEADER"):
        for header in os.getenv("OKS_DEV_HEADER").split(','):
            _h, _, _n = header.partition('=')
            if _h and _n:
                headers[_h.strip()] = _n.strip() 

    if is_jwt_enabled() and is_tokens_valid():
        headers["AccessToken"] = get_token('access_token')
        headers["RefreshToken"] = get_token('refresh_token')
    elif os.getenv("OKS_ACCESS_KEY") and os.getenv("OKS_ACCESS_KEY"):
        headers["AccessKey"] =  os.getenv("OKS_ACCESS_KEY")
        headers["SecretKey"] =  os.getenv("OKS_SECRET_KEY")
    elif os.getenv("OKS_USERNAME") and os.getenv("OKS_PASSWORD"):
        username = os.getenv("OKS_USERNAME")
        password = os.getenv("OKS_PASSWORD")
        user_pass = f"{username}:{password}"
        user_pass_bytes = user_pass.encode('utf-8')
        encoded_user_pass = base64.b64encode(user_pass_bytes).decode('utf-8')

        headers["Authorization"] = f"Basic {encoded_user_pass}"
    else:
        raise click.ClickException("No authentication profiles were found. Please set a user profile to proceed")

    return headers

def print_output(data, output_fromat):
    """Print data in the specified format: JSON, YAML, or silent."""
    output_data = json.dumps(data, indent=4)

    if output_fromat == "yaml":
        output_data = yaml.dump(data, sort_keys=False)

    elif output_fromat == "silent":
        return

    click.echo(output_data)

def print_table(data, table_fields, align="l", style=None):
    """Print API returned data as table
    data: list of dict containing data
    table_fields: List of 2 elements list. First element is the table field name, second element is the corresponding dict key in data
    align: Columns alignment (l,r,c)
    style: Table format other style
    """
    table = prettytable.PrettyTable()
    table.align = align
    if style and isinstance(style, prettytable.TableStyle):
        table.set_style(style)
    fields = list()
    values = list()

    for d in table_fields:
        fields.append(d[0])
        values.append(d[1])

    table.field_names = fields

    for d in data:
        table.add_row([d[v] if v in d else "" for v in values])
    click.echo(table)

def handle_otp_error(err, callback):
    """Handle OTP authentication error by prompting the user and retrying the request."""
    try:
        response_body = json.loads(err.response.text)
        if response_body.get("otp_required"):
            otp_code = click.prompt('Enter your OTP code', type=int)
            os.environ["OKS_OTP_CODE"] = str(otp_code)

            return callback()
    except Exception:
        return None

def handle_jwt_error(err, method, path, args, kwargs):
    """Handle invalid JWT errors by removing tokens and retrying the request."""
    try:
        response_body = json.loads(err.response.text)
        if response_body.get("message") == "Unauthorized: Invalid JWT.":
            remove_jwt_token('access_token')
            remove_jwt_token('refresh_token')

            headers = kwargs.get("headers", {})
            headers.pop("AccessToken", None)
            headers.pop("RefreshToken", None)

            return do_request(method, path, *args, **kwargs)
    except Exception:
        return None

def find_project_id_by_name(project_name):
    """Retrieve the project ID by name or use the default project if no name is provided."""
    if not project_name:
        project_id = get_project_id()
        if not project_id:
            raise click.BadParameter("--project-name must be specified, or a default project must be set")
    else:
        data = do_request("GET", 'projects', params={"name": project_name})
        if len(data) != 1:
            errors = {"Error": f"{len(data)} projects found by name: {project_name}"}
            raise JSONClickException(json.dumps(errors))
        project_id = data.pop()['id']

    return project_id

def find_cluster_id_by_name(project_id, cluster_name):
    """Retrieve the cluster ID by name within a given project, or use the default cluster if none is provided."""
    if not cluster_name:
        cluster_id = get_cluster_id()
        if not cluster_id:
            raise click.BadParameter("--cluster-name must be specified, or a default cluster must be set")
    else:
        data = do_request("GET", 'clusters', params={"project_id": project_id, "name": cluster_name})
        if len(data) != 1:
            errors = {"Error": f"{len(data)} clusters found by name: {cluster_name}"}
            raise JSONClickException(json.dumps(errors))
        cluster_id = data.pop()['id']

    return cluster_id

def get_project_id():
    """Return the default project ID from the profile configuration file, if available."""
    project_id = None

    if not os.getenv("OKS_PROFILE"):
        return
    
    CONFIG_FOLDER, _ = get_config_path()

    PROJECT_ID_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.project_id"

    if os.path.exists(PROJECT_ID_FILE):
        with open(PROJECT_ID_FILE, 'r') as file:
            project_id = file.read()

    return project_id

def get_cluster_id():
    """Return the default cluster ID from the profile configuration file, if available."""
    cluster_id = None

    if not os.getenv("OKS_PROFILE"):
        return
    
    CONFIG_FOLDER, _ = get_config_path()

    CLUSTER_ID_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.cluster_id"

    if os.path.exists(CLUSTER_ID_FILE):
        with open(CLUSTER_ID_FILE, 'r') as file:
            cluster_id = file.read()

    return cluster_id

def set_cluster_id(cluster_id):
    """Save the given cluster ID to the profile configuration file with secure permissions."""
    CONFIG_FOLDER, _ = get_config_path()

    if not os.path.exists(CONFIG_FOLDER):
        os.makedirs(CONFIG_FOLDER)

    if not os.getenv("OKS_PROFILE"):
        return

    CLUSTER_ID_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.cluster_id"

    with open(CLUSTER_ID_FILE, 'w') as file:
        file.write(cluster_id)

    os.chmod(CLUSTER_ID_FILE, 0o600)

def set_project_id(project_id):
    """Save the given project ID to the profile configuration file with secure permissions."""
    CONFIG_FOLDER, _ = get_config_path()

    if not os.path.exists(CONFIG_FOLDER):
        os.makedirs(CONFIG_FOLDER)

    if not os.getenv("OKS_PROFILE"):
        return

    PROJECT_ID_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.project_id"

    with open(PROJECT_ID_FILE, 'w') as file:
        file.write(project_id)

    os.chmod(PROJECT_ID_FILE, 0o600)

def login_profile(name):
    """
    Load and set environment variables for the given profile name.
    Raises an exception if the profile does not exist or lacks required info.
    """
    _, PROFILE_FILE = get_config_path()

    # check is profile name is defined by user as environment variable
    if name is None:
        if os.getenv('OKS_PROFILE') is None:
            name = "default"
        else:
            name = os.getenv('OKS_PROFILE')

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as file:
            profiles = json.load(file)

        if name not in profiles:
            raise click.ClickException("Profile %s does not exist" % click.style(name, bold=True))

        os.environ["OKS_PROFILE"] = name

        if profiles[name]['type'] == 'username/password':
            os.environ["OKS_USERNAME"] = profiles[name]['username']
            os.environ["OKS_PASSWORD"] = profiles[name]['password']
        else: # profiles[name]['type'] == 'ak/sk'
            os.environ["OKS_ACCESS_KEY"] = profiles[name]['access_key']
            os.environ["OKS_SECRET_KEY"] = profiles[name]['secret_key']

        if not os.environ.get("OKS_ENDPOINT"):
            if 'endpoint' in profiles[name]:
                os.environ["OKS_ENDPOINT"] = profiles[name]['endpoint']
            elif 'region_name' in profiles[name]:
                os.environ["OKS_ENDPOINT"] = DEFAULT_API_URL.format(region=profiles[name]['region_name'])
            else:
                raise click.ClickException(f"Unable to find API endpoint for {click.style(name, bold=True)} profile")

        if 'region_name' in profiles[name]:
            os.environ["OKS_REGION"] = profiles[name]['region_name']

        return profiles[name]

    return {}

def profile_list():
    """Return all profiles as a dict, or empty if none."""
    _, PROFILE_FILE = get_config_path()

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as file:
            profiles = json.load(file)
            return profiles
    
    return {}

def get_profiles():
    """Return list of profile names, or empty list."""
    _, PROFILE_FILE = get_config_path()

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return list(data.keys())
    return []

def profile_completer(ctx, param, incomplete):
    """Autocomplete profile names starting with input."""
    profiles = get_profiles()
    return [CompletionItem(p) for p in profiles if p.startswith(incomplete)]

def cluster_completer(ctx, param, incomplete):
    profile = (
        ctx.params.get("profile")
        or getattr(ctx.parent, "params", {}).get("profile")
        or getattr(getattr(ctx.parent, "parent", None), "params", {}).get("profile")
        or "default"
    )

    try:
        if profile:
            login_profile(profile)
    except Exception:
        return []
    
    project_name = ctx.params.get("project_name") or getattr(ctx.parent, "params", {}).get("project_name")

    project_id = None
    try:
        projects = do_request("GET", "projects")
        if project_name:
            for p in projects:
                if p["name"] == project_name:
                    project_id = p["id"]
                    break
        else:
            project_id = get_project_id()
    except Exception:
        return []

    params = {}
    if project_id:
        params["project_id"] = project_id

    try:
        data = do_request("GET", "clusters", params=params)
    except Exception:
        return []

    cluster_names = [c["name"] for c in data]
    matches = [n for n in cluster_names if n.startswith(incomplete)] if incomplete else cluster_names
    return [CompletionItem(n) for n in matches]

def project_completer(ctx, param, incomplete):
    profile = (
        ctx.params.get("profile")
        or getattr(ctx.parent, "params", {}).get("profile")
        or getattr(getattr(ctx.parent, "parent", None), "params", {}).get("profile")
        or "default"
    )

    try:
        if profile:
            login_profile(profile)
    except Exception:
        return []

    try:
        data = do_request("GET", "projects")
    except Exception:
        return []

    project_names = [p["name"] for p in data]
    matches = [n for n in project_names if n.startswith(incomplete)] if incomplete else project_names
    return [CompletionItem(n) for n in matches]

def set_profile(name, obj: dict):
    """Add or update a profile in the profiles file."""
    _, PROFILE_FILE = get_config_path()

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r+') as file:
            profiles = json.load(file)
            profiles[name] = obj

            profiles = json.dumps(profiles)

            file.seek(0)
            file.write(profiles)
            file.truncate()
    else:
        with open(PROFILE_FILE, 'w') as file:
            profiles = {
                name: obj
            }
            profiles = json.dumps(profiles)
            file.write(profiles)

    os.chmod(PROFILE_FILE, 0o600)

def remove_profile(name):
    """Remove a profile by name from the profiles file."""
    _, PROFILE_FILE = get_config_path()

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r+') as file:
            profiles = json.load(file)
            del profiles[name]

            profiles = json.dumps(profiles)

            file.seek(0)
            file.write(profiles)
            file.truncate()

def get_cache(project, cluster, name, user, group):
    """Return path to cached item if it exists, else None."""
    CONFIG_FOLDER, _ = get_config_path()

    user = user or "default"
    group = group or "default"

    cluster_cache = pathlib.Path(CONFIG_FOLDER).joinpath("cache", f"{project}-{cluster}", user, group)
    item_path = cluster_cache.joinpath(name).absolute()

    try:
        with item_path.open():
            logging.info("cache found at %s", item_path)
            return item_path
    except Exception:
        logging.info("cache item %s %s %s not found", project, cluster, name)

def save_cache(project, cluster, name, data, user, group):
    """Save data to cache file and return its path."""
    CONFIG_FOLDER, _ = get_config_path()

    user = user or "default"
    group = group or "default"

    cluster_cache = pathlib.Path(CONFIG_FOLDER).joinpath("cache", f"{project}-{cluster}", user, group)
    item_path = cluster_cache.joinpath(name).absolute()

    if not cluster_cache.exists():
        cluster_cache.mkdir(parents = True)

    with item_path.open("w") as f:
        logging.info("saving cache at %s", item_path)
        f.write(data)

    os.chmod(item_path, 0o600)

    return item_path

def clear_cache():
    """Delete the entire cache directory."""
    CONFIG_FOLDER, _ = get_config_path()
    cache = pathlib.Path(CONFIG_FOLDER).joinpath("cache")
    shutil.rmtree(cache)

def get_all_cache(project, cluster, name):
    """Retrieve all cache entries for a project and cluster."""
    CONFIG_FOLDER, _ = get_config_path()
    cluster_cache_path = pathlib.Path(CONFIG_FOLDER).joinpath("cache", f"{project}-{cluster}")
    table = []

    if not os.path.exists(cluster_cache_path):
        logging.info(f"Cache directory '{cluster_cache_path}' does not exist.")
        return table

    for user in os.listdir(cluster_cache_path):
        user_path = os.path.join(cluster_cache_path, user)
        if os.path.isdir(user_path):
            for group in os.listdir(user_path):
                group_path = os.path.join(user_path, group)
                if os.path.isdir(group_path):
                    cache = get_cache(project, cluster, name, user, group)
                    table.append({"user": user,"group": group, "cache_path": cache})

    return table

def parse_jwt(token):
    """Decode and parse a JWT token payload as JSON."""
    try:
        payload_b64 = token.split('.')[1]
        padding = '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        return json.loads(payload_json)
    except (IndexError, ValueError):
        return None

def save_tokens(headers):
    """Save access and refresh tokens from response headers."""
    CONFIG_FOLDER, _ = get_config_path()
    if not headers.get('Access-Token') or not headers['Refresh-Token']:
        return

    if not os.getenv("OKS_PROFILE"):
        return

    ACCESS_TOKEN_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.access_token"
    REFRESH_TOKEN_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.refresh_token"

    with open(ACCESS_TOKEN_FILE, 'w') as file:
        file.write(headers['Access-Token'])

    with open(REFRESH_TOKEN_FILE, 'w') as file:
        file.write(headers['Refresh-Token'])

    os.chmod(ACCESS_TOKEN_FILE, 0o600)
    os.chmod(REFRESH_TOKEN_FILE, 0o600)

def is_tokens_valid():
    """Check if stored refresh token is still valid."""
    CONFIG_FOLDER, _ = get_config_path()
    if not os.getenv("OKS_PROFILE"):
        return

    REFRESH_TOKEN_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.refresh_token"

    if not os.path.exists(REFRESH_TOKEN_FILE):
        return False

    with open(REFRESH_TOKEN_FILE, 'r') as file:
        refresh_token = file.read()

        decoded_refresh_token = parse_jwt(refresh_token)

        if decoded_refresh_token and decoded_refresh_token.get('exp'):

            current_time = int(time.time())

            if decoded_refresh_token['exp'] >= current_time + 5: # 5sec margin
                return True

    return False

def is_jwt_enabled():
    """Return True if JWT is enabled in the current profile."""
    _, PROFILE_FILE = get_config_path()

    if not os.getenv("OKS_PROFILE"):
        return

    name = os.getenv("OKS_PROFILE")

    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as file:
            profiles = json.load(file)

        if name not in profiles:
            raise click.ClickException("Profile %s does not exist" % click.style(name, bold=True))

        return profiles[name].get('jwt', False)

    return False

def get_token(token_type):
    """Retrieve stored token (access or refresh) for current profile."""
    CONFIG_FOLDER, _ = get_config_path()

    if not os.getenv("OKS_PROFILE"):
        return

    TOKEN_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.{token_type}"

    if not os.path.exists(TOKEN_FILE):
        return ""

    with open(TOKEN_FILE, 'r') as file:
        token = file.read()
        return token

def remove_jwt_token(token_type):
    """Delete the specified JWT token file for current profile."""
    CONFIG_FOLDER, _ = get_config_path()

    if not os.getenv("OKS_PROFILE"):
        return

    TOKEN_FILE = f"{CONFIG_FOLDER}/{os.getenv('OKS_PROFILE')}.{token_type}"

    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def detect_and_parse_input(input_data):
    """Parse input as JSON or YAML; raise error if invalid."""
    try:
        return json.loads(input_data)
    except json.JSONDecodeError:
        pass

    try:
        return yaml.safe_load(input_data)
    except yaml.YAMLError:
        pass

    raise click.BadParameter("Input file is neither valid JSON nor YAML.")

def verify_certificate(kubeconfig_str):
    """Check if the kubeconfig client certificate is still valid."""
    not_after_date = get_expiration_date(kubeconfig_str)

    if not_after_date < datetime.now():
        return False
    else:
        return True

def get_expiration_date(kubeconfig_str):
    """Extract and return the client certificate expiration date."""
    kubeconfig = yaml.safe_load(kubeconfig_str)

    for user_entry in kubeconfig.get('users', []):
        user_details = user_entry['user']
        client_cert_data = user_details.get('client-certificate-data')

        if not client_cert_data:
            logging.info("No client certificate data found for user.")
            continue

        cert = decode_parse_certificate(client_cert_data)
        not_after = cert.get_notAfter().decode('ascii')
        not_after_date = datetime.strptime(not_after, '%Y%m%d%H%M%SZ')

        return not_after_date

def decode_parse_certificate(cert_str):
    """Parse base64 encoded certificate data and returns cert (X509) object"""
    try:
        ca_cert = base64.b64decode(cert_str)
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, ca_cert)
        return cert
    except OpenSSL.crypto.Error as e:
        logging.info(f"ERROR: Can't parse base64 encoded certificate: {e}")

def kubeconfig_parse_fields(kubeconfig, cluster_name, user, group):
    """
    Load YAML kubeconfig and extract fields
    kubeconfig: Kubeconfig load file as string (YAML)
    cluster_name: Name of the cluster kubeconfig is related to
    user: user name of this kubeconfig (if set)
    group: user group name of this kubeconfig (if set)
    """
    kubeconfig_str = yaml.safe_load(kubeconfig)
    kubedata = list()

    # Ensure loaded YAML returnes a valid dict object
    if not isinstance(kubeconfig_str, dict):
        return kubedata

    for context in kubeconfig_str.get('contexts', []):
        data = dict()
        ctx_cluster = context.get('context').get('cluster', None)
        ctx_user = context.get('context').get('user', None)
        ctx_name = context.get('name')
        data.update({"context_name": ctx_name})

        for cluster in kubeconfig_str.get('clusters', []):
            if ctx_cluster == cluster.get('name', None):
                cls_server = cluster.get('cluster').get('server')
                if not cluster_name:
                    cluster_name = ctx_cluster
                data.update({"cluster_name": cluster_name, "server_name": cls_server})
                break

        for user_name in kubeconfig_str.get('users', []):
            if ctx_user == user_name.get('name'):
                cert_str = user_name.get('user').get('client-certificate-data')
                cert_obj = decode_parse_certificate(cert_str)
                expires_at = datetime.strptime(cert_obj.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
                cn = cert_obj.get_subject().get_components()
                cn_user = f"CN={cn[0][1].decode('utf-8')}"
                cn_group = f"/O={cn[1][1].decode('utf-8')}" if len(cn) > 1 else ""
                data.update({"user": click.style(user, bold=True), "group": click.style(group, bold=True),
                             "expires_at": expires_at, "ctx_user": ctx_user, "cn": f"{cn_user}{cn_group}"})
                break
        kubedata.append(data)

    return kubedata

def retrieve_cp_sized(filepath, endpoint):
    """Fetch control plane sizes from API and save to file."""
    cp_list = do_request("GET", endpoint)

    with open(filepath, "w") as file:
        json.dump(cp_list, file)

def shell_completions(ctx, param: click.core.Option, incomplete):
    """Provide shell autocompletions with cached API data."""
    CONFIG_FOLDER, _ = get_config_path()

    profiles = profile_list()
    profile = ctx.params["profile"] or ctx.parent.params["profile"] or ctx.parent.parent.params["profile"] or None

    # Check if OKS_PROFILE is set somehow
    if profile is None:
        if os.getenv('OKS_PROFILE') is None:
            profile = 'default'
        else:
            profile = os.getenv('OKS_PROFILE')

    if profile not in profiles:
        return []

    login_profile(profile)

    if param.name == "version":
        endpoint = "clusters/limits/kubernetes_versions"
    elif param.name == "control_plane":
        endpoint = "clusters/limits/control_plane_plans"
    elif param.name == "zone":
        endpoint = "clusters/limits/cp_subregions"
    else:
        return []
    
    CP_SIZES_PATH = f"{CONFIG_FOLDER}/cache/{profile}.{param.name}"
    os.makedirs(f"{CONFIG_FOLDER}/cache", exist_ok=True)

    if os.path.exists(CP_SIZES_PATH):
        file_ctime = os.path.getctime(CP_SIZES_PATH)
        if datetime.timestamp(datetime.now()) - file_ctime > 300:
            retrieve_cp_sized(CP_SIZES_PATH, endpoint)
    else:
        retrieve_cp_sized(CP_SIZES_PATH, endpoint)

    if os.path.exists(CP_SIZES_PATH):
        with open(CP_SIZES_PATH, "r") as file:
            cp_list = json.load(file)
    else:
        cp_list = []

    return [k for k in cp_list if k.startswith(incomplete)]

def update_shell_profile(shell_profile, filepath):
    """Append source command to shell profile if not present."""
    if os.path.exists(shell_profile):
        with open(shell_profile, 'r') as f:
            lines = f.readlines()

        line_to_add = f". {filepath}\n"
        if line_to_add not in lines:
            with open(shell_profile, 'a') as f:
                f.write("\n" + line_to_add)

def find_shell_profile(home, shell_type):
    """Return user shell profile path or None if ambiguous."""
    shell_profile = None

    if shell_type == "bash":

        bash_profile = os.path.join(home, '.bash_profile')
        bashrc = os.path.join(home, '.bashrc')

        if os.path.exists(bash_profile) and os.path.exists(bashrc):
            return None

        shell_profile = bash_profile or bashrc

    elif shell_type == "zsh":

        zshrc = os.path.join(home, '.zshrc')
        profile = os.path.join(home, '.profile')

        if os.path.exists(zshrc) and os.path.exists(profile):
            return None

        shell_profile = zshrc or profile

    return shell_profile

def install_completions(shell_type):
    """Install shell completion scripts for bash or zsh."""
    home = os.path.expanduser('~')

    if shell_type is None:
        try:
            shell_pid = os.getppid()
            result = subprocess.run(['ps', '-p', str(shell_pid), '-o', 'comm='], capture_output=True, text=True)
            shell_name = result.stdout.strip()

            shell_type = os.path.basename(shell_name).lstrip('-')
        except subprocess.SubProcessError:
            click.echo("Failed to determine shell type, please specify it by --type")

    completion_dir = os.path.join(home, ".oks_cli", "completions")
    os.makedirs(completion_dir, exist_ok=True)

    if shell_type == 'bash':
        subprocess.run(f'_OKS_CLI_COMPLETE=bash_source oks-cli > {completion_dir}/oks-cli.sh', shell=True)
        shell_profile = find_shell_profile(home, shell_type)
        if shell_profile:
            update_shell_profile(shell_profile, f"{completion_dir}/oks-cli.sh")
            click.echo(f"Autocompletion installed for {shell_type} in {completion_dir}.\nRestart your shell or source you {click.style(shell_profile, bold=True)} to enable it.")
        else:
            click.echo(
                "\nTo activate autocompletion on login please add following lines into your .bash_profile or .bashrc file:\n\n" +
                click.style('[ -s "$HOME/.oks_cli/completions/oks-cli.sh" ] && source "$HOME/.oks_cli/completions/oks-cli.sh"\n\n', bold=True) +
                "And to activate it now - please run:\n\n" +
                click.style('source "$HOME/.oks_cli/completions/oks-cli.sh"\n', bold=True)
            )

    elif shell_type == 'zsh':
        subprocess.run(f'_OKS_CLI_COMPLETE=zsh_source oks-cli > {completion_dir}/oks-cli.sh', shell=True)
        shell_profile = find_shell_profile(home, shell_type)
        if shell_profile:
            update_shell_profile(shell_profile, f"{completion_dir}/oks-cli.sh")
            click.echo(f"Autocompletion installed for {shell_type} in {completion_dir}.\nRestart your shell or source you {click.style(shell_profile, bold=True)} to enable it.")
        else:
            click.echo(
                "\nTo activate autocompletion on login please add following lines into your .profile or .zshrc file:\n\n" +
                click.style('[ -s "$HOME/.oks_cli/completions/oks-cli.sh" ] && source "$HOME/.oks_cli/completions/oks-cli.sh"\n\n', bold=True) +
                "And to activate it now - please run:\n\n" +
                click.style('source "$HOME/.oks_cli/completions/oks-cli.sh"\n', bold=True)
            )
    else:
        raise click.UsageError(f"Shell completions for {shell_type} are not implemented.")

def transform_tuple(data):
    """Convert tuple to list unless it contains only an empty string."""
    return [] if data == ('',) else list(data)

def cluster_create_in_background(cluster_config, text):
    """Forks and retries cluster creation in background until project ready or failed."""
    pid = os.fork()

    if pid == 0:  # Child process
        time.sleep(120) # Initial 2 mins pause
        for i in range(30): # retry every 30 seconds during 15 mins
            project = do_request("GET", f"projects/{cluster_config.get('project_id')}")

            if project.get("status") == "ready":
                do_request("POST", 'clusters', json=cluster_config)
                return
            elif project.get("status") == "failed":
                return

            time.sleep(30)
    else:  # Parent process
        click.echo(f"Task for create cluster started in background. PID: {pid}" + text)

def get_template(type):
    """Fetch and cache template, refresh if older than 15 minutes."""
    CONFIG_FOLDER, _ = get_config_path()

    TEMPLATE_PATH = f"{CONFIG_FOLDER}/cache/{type}.template"
    os.makedirs(f"{CONFIG_FOLDER}/cache", exist_ok=True)

    if os.path.exists(TEMPLATE_PATH):
        file_ctime = os.path.getctime(TEMPLATE_PATH)
        if datetime.timestamp(datetime.now()) - file_ctime > 900:
            template = do_request("GET", f"templates/{type}")
            with open(TEMPLATE_PATH, "w") as file:
                json.dump(template, file)
            os.chmod(TEMPLATE_PATH, 0o600)
        else:
            with open(TEMPLATE_PATH, "r") as file:
                template = json.load(file)
    else:
        template = do_request("GET", f"templates/{type}")
        with open(TEMPLATE_PATH, "w") as file:
            json.dump(template, file)
        os.chmod(TEMPLATE_PATH, 0o600)

    return template

def ctx_update(ctx, project_name=None, cluster_name=None, profile=None, overwrite=True):
    """Update context with project, cluster, and profile; optionally prevent overwrites."""
    if not hasattr(ctx, 'obj') or not ctx.obj:
        ctx.obj = dict()

    if project_name is not None:
        if ctx.obj.get('project_name') and not overwrite:
            raise click.BadParameter("project-name already set before")
        ctx.obj['project_name'] = project_name

    if cluster_name is not None:
        if ctx.obj.get('cluster_name') and not overwrite:
            raise click.BadParameter("cluster-name already set before")
        ctx.obj['cluster_name'] = cluster_name
        
    if profile is not None:
        if ctx.obj.get('profile') and not overwrite:
            raise click.BadParameter("profile already set before")
        ctx.obj['profile'] = profile

    return (ctx.obj.get('project_name'), ctx.obj.get('cluster_name'), ctx.obj.get('profile'))

def get_project_name(project_name):
    """Return project name from ID or given name, else raise error."""
    if not project_name:
        project_id = get_project_id()
        if not project_id:
            raise click.BadParameter("--project-name must be specified, or a default project must be set")

        project = do_request("GET", f'projects/{project_id}')
        return project['name']
    else:
        return project_name

def get_cluster_name(cluster_name):
    """Return cluster name from ID or given name, else raise error."""
    if not cluster_name:
        cluster_id = get_cluster_id()
        if not cluster_id:
            raise click.BadParameter("--cluster_name must be specified, or a default cluster must be set")

        cluster = do_request("GET", f'clusters/{cluster_id}')
        return cluster['name']
    else:
        return cluster_name

def format_changed_row(table, row):
    """Format a single changed row maintaining table style."""
    new_table = prettytable.PrettyTable()
    new_table.field_names = table.field_names
    if table._style:
        new_table.set_style(table._style)
    new_table.header = False

    # Set the min width for each column
    for i, width in enumerate(table._widths):
        if i < len(new_table.field_names):
            new_table.min_width[new_table.field_names[i]] = width

    new_table.add_row(row)

    return new_table

def is_interesting_status(status):
    """Check if status is in the list of interesting statuses."""
    interesting_statuses = ["pending", "deploying", "updating", "upgrading", "deleting"]
    return status in interesting_statuses
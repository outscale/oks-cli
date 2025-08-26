import click
import prettytable
from .utils import do_request, print_output, print_table, ctx_update, login_profile, profile_completer

@click.command(help="Get Quotas")
@click.option("--profile", help="Configuration profile to use", shell_complete=profile_completer)
@click.option('--output','-o', type=click.Choice(["json", "yaml", "table"]), help="Specify output format, by default is json")
@click.pass_context
def quotas(ctx, profile, output):
    """Retrieve global quotas across all projects for the given profile."""
    _, _, profile = ctx_update(ctx, None, None, profile)
    login_profile(profile)

    data = do_request("GET", 'quotas')
    if output == "table":
        print_table([data], [["Projects", "Projects"],
                           ["Clusters per project", "ClustersPerProject"],
                           ["Kubernetes versions", "KubeVersions"],
                           ["Control plane subregions", "CPSubregions"]])
    else:
        print_output(data, output)

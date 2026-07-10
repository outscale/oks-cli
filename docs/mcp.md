# MCP Server

`oks-cli` ships a [Model Context Protocol](https://modelcontextprotocol.io) server that exposes its commands as tools an LLM client — such as Claude Code or Claude Desktop — can call directly, without you typing shell commands.

## How it works

The server lives in [`oks_cli/mcp_server.py`](../oks_cli/mcp_server.py) and is built with [`FastMCP`](https://github.com/modelcontextprotocol/python-sdk).

* Every tool (e.g. `cluster_list`, `nodepool_create`) is a thin Python wrapper that builds an `oks-cli ...` argument list and runs it as a subprocess (`subprocess.run`).
* Most read commands pass `--output json`, so the tool result is a JSON string the model can parse. A few exceptions:
  * `cluster_kubeconfig` returns YAML.
  * `nodepool_list` / `nodepool_create` / `nodepool_delete` shell out to `kubectl` and return the CLI's default table text (no `--output json` flag is passed for these).
* On a non-zero exit code, the wrapper returns `{"error": "<stderr or stdout>"}` instead of raising, so the model sees the failure as a normal tool result and can react to it.
* The server talks to its client over **stdio** — the client spawns it as a subprocess and exchanges JSON-RPC messages on stdin/stdout. There is no network port to open.
* Tools don't hold any session state (no "current project/cluster"). Every call takes explicit `project_name` / `cluster_name` arguments; if omitted, `oks-cli` falls back to whatever default project/cluster was set via `oks-cli project login` / `cluster login` on the machine running the server.
* Every tool also accepts an optional `profile`, forwarded as `--profile` to select a specific `oks-cli` profile (see [Prerequisites](#prerequisites)) instead of the default one.

### Tool coverage

| Category | Tools |
|---|---|
| Project | `project_list`, `project_get`, `project_create`, `project_update`, `project_delete`, `project_quotas`, `project_snapshots`, `project_publicips`, `project_nets` |
| Cluster | `cluster_list`, `cluster_get`, `cluster_create`, `cluster_update`, `cluster_upgrade`, `cluster_delete`, `cluster_kubeconfig` |
| Nodepool | `nodepool_list`, `nodepool_create`, `nodepool_delete` |
| NetPeering | `netpeering_list`, `netpeering_get`, `netpeering_create`, `netpeering_delete` |
| User (EIM) | `user_list`, `user_create`, `user_delete` |
| Quotas | `quotas_get` |

### ⚠️ Safety note

Destructive tools (`project_delete`, `cluster_delete`, `cluster_upgrade`, `nodepool_delete`, `netpeering_delete`, `user_delete`) run `oks-cli` with `--force`, which skips the CLI's normal interactive "are you sure?" prompt — the model has no terminal to answer it. That means the model itself (or the human approving its tool calls) is the only confirmation gate before the action runs. Treat requests that trigger these tools with the same caution you'd give any irreversible cloud operation.

## Prerequisites

* `oks-cli` installed with the `mcp` extra:
  ```bash
  pip install "oks-cli[mcp]"
  # or, from a local checkout:
  pip install -e ".[mcp]"
  ```
* At least one profile configured, since the subprocess calls rely on stored credentials:
  ```bash
  oks-cli profile add --access-key <AK> --secret-key <SK> --region eu-west-2
  ```

## Setting it up in Claude

The server can be launched two equivalent ways:

```bash
oks-cli-mcp                    # console script installed by setup.py
python -m oks_cli.mcp_server   # module form, no PATH dependency
```

Point your Claude client at one of these. Pick the scope that matches how you want to share the config:

### Project scope (this repo)

This repository already has a working project-scoped config at `.mcp.json` (repo root) — the standard Claude Code convention for a project MCP config meant to be shared with every contributor via git:

```json
{
  "mcpServers": {
    "oks-cli": {
      "command": "python",
      "args": ["-m", "oks_cli.mcp_server"]
    }
  }
}
```

Because it runs an arbitrary command on your machine, Claude Code asks you to approve this project's MCP servers the first time you open the repo (or after the file changes), even though it's checked into git.

### User scope (all projects)

To register the server globally instead of per-repo, use the Claude Code CLI:

```bash
claude mcp add oks-cli --scope user -- python -m oks_cli.mcp_server
```

### Claude Desktop

Add the same block to Claude Desktop's `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "oks-cli": {
      "command": "python",
      "args": ["-m", "oks_cli.mcp_server"]
    }
  }
}
```

Restart the client after editing any of these files so it picks up the new server. Once connected, tools appear prefixed as `mcp__oks-cli__<tool_name>` (e.g. `mcp__oks-cli__cluster_list`).


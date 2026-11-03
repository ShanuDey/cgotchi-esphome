"""The `cgotchi` command: `dev` builds the firmware, `api` calls the HA API, `mcp` tools, `deploy` installs into HA."""
import sys

USAGE = """usage: cgotchi dev <esphome command> ...   build and flash with the local components
       cgotchi api <command> ...             drive the device through Home Assistant (state, display, speaker, ...)
       cgotchi mcp ui                        open the MCP Inspector for the device's MCP endpoint (needs Node)
       cgotchi deploy api [--restart]        copy the HA integration into the HA config folder"""


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("dev", "api", "mcp", "deploy"):
        print(USAGE, file=sys.stderr)
        return 2
    group, *rest = sys.argv[1:]
    sys.argv = [f"cgotchi {group}", *rest]
    if group == "dev":
        from scripts.dev import main as dev_main
        return dev_main()
    if group == "api":
        from cgotchi_api.cli import main as cli_main
        return cli_main(rest)
    if group == "mcp":
        if rest[:1] != ["ui"]:
            print(USAGE, file=sys.stderr)
            return 2
        from cgotchi_api.mcp_ui import main as mcp_ui_main
        return mcp_ui_main(rest[1:])
    if rest[:1] != ["api"]:
        print(USAGE, file=sys.stderr)
        return 2
    from cgotchi_api.deploy import main as deploy_main
    return deploy_main(rest[1:])


if __name__ == "__main__":
    sys.exit(main())

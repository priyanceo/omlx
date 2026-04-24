#!/usr/bin/env python3
"""
omlx - A command-line tool for managing and querying language model configurations.

Fork of jundot/omlx with additional features and improvements.
"""

import argparse
import json
import os
import sys
from pathlib import Path

__version__ = "0.1.0"
__author__ = "omlx contributors"

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "omlx" / "config.json"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load configuration from the given path.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        A dictionary containing the configuration.
    """
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not load config from {config_path}: {e}", file=sys.stderr)
        return {}


def save_config(config: dict, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Save configuration to the given path.

    Args:
        config: Dictionary to save as JSON.
        config_path: Path to write the configuration file.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"Config saved to {config_path}")


def cmd_list(args: argparse.Namespace, config: dict) -> int:
    """List all configured models."""
    models = config.get("models", {})
    if not models:
        print("No models configured. Use 'omlx add' to add a model.")
        return 0
    print(f"{'Name':<20} {'Endpoint':<40} {'Default':<8}")
    print("-" * 70)
    default_model = config.get("default", "")
    for name, info in models.items():
        is_default = "*" if name == default_model else ""
        endpoint = info.get("endpoint", "(not set)")
        print(f"{name:<20} {endpoint:<40} {is_default:<8}")
    return 0


def cmd_add(args: argparse.Namespace, config: dict) -> int:
    """Add or update a model entry."""
    models = config.setdefault("models", {})
    models[args.name] = {
        "endpoint": args.endpoint,
        "api_key_env": args.api_key_env or "",
    }
    if args.set_default or not config.get("default"):
        config["default"] = args.name
    save_config(config)
    print(f"Model '{args.name}' added.")
    return 0


def cmd_remove(args: argparse.Namespace, config: dict) -> int:
    """Remove a model entry."""
    models = config.get("models", {})
    if args.name not in models:
        print(f"Error: Model '{args.name}' not found.", file=sys.stderr)
        return 1
    del models[args.name]
    if config.get("default") == args.name:
        config.pop("default", None)
    save_config(config)
    print(f"Model '{args.name}' removed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="omlx",
        description="Manage language model configurations from the command line.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                        help="Path to config file (default: ~/.config/omlx/config.json)")

    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List configured models")

    # add
    add_parser = subparsers.add_parser("add", help="Add or update a model")
    add_parser.add_argument("name", help="Model name/alias")
    add_parser.add_argument("endpoint", help="API endpoint URL")
    add_parser.add_argument("--api-key-env", dest="api_key_env",
                            help="Environment variable name holding the API key")
    add_parser.add_argument("--default", dest="set_default", action="store_true",
                            help="Set this model as the default")

    # remove
    rm_parser = subparsers.add_parser("remove", aliases=["rm"], help="Remove a model")
    rm_parser.add_argument("name", help="Model name/alias to remove")

    return parser


def main() -> int:
    """Entry point for the omlx CLI."""
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)

    commands = {
        "list": cmd_list,
        "add": cmd_add,
        "remove": cmd_remove,
        "rm": cmd_remove,
    }

    if args.command is None:
        parser.print_help()
        return 0

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args, config)


if __name__ == "__main__":
    sys.exit(main())

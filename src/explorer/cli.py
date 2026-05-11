"""Simple CLI for exploring Arkiv entities."""
from __future__ import annotations

import argparse
import logging
import json
import os
import sys
from typing import Any, Dict, Optional, cast

ARKIV_RPC_URL_DEFAULT = "https://braga.hoodi.arkiv.network/rpc"

def _connect_client() -> Any:
    """Return an Arkiv client. Prefer ARKIV_RPC_URL if set."""
    try:
        from arkiv import Arkiv
        from arkiv.provider import ProviderBuilder
        from web3.providers.base import BaseProvider
    except Exception as exc:  # pragma: no cover - environment may not have SDK in tests
        raise RuntimeError("Arkiv SDK is required to run explorer CLI") from exc

    rpc = os.getenv("ARKIV_RPC_URL", ARKIV_RPC_URL_DEFAULT)
    if rpc:
        provider = cast(BaseProvider, ProviderBuilder().custom(url=rpc).build())
        return Arkiv(provider=provider)
    # fallback: start a local Arkiv node
    return Arkiv()


def _format_entity(entity: Any) -> str:
    # Build a dict of useful fields
    d: Dict[str, Any] = {
        "$key": entity.key,
        "$owner": entity.owner,
        "$contentType": entity.content_type,
        "$createdAtBlock": getattr(entity, "created_at_block", None),
        "$lastModifiedAtBlock": getattr(entity, "lastModifiedAtBlock", None),
        "$expiresAtBlock": entity.expires_at_block,
        "attributes": entity.attributes,
    }

    if entity.payload is None:
        d["payload"] = None
    else:
        # Try to represent payload sensibly
        try:
            # If bytes -> try decode as utf-8, else base64
            payload = entity.payload
            if isinstance(payload, bytes):
                text = payload.decode("utf-8")

                # Try to parse as JSON
                try:
                    d["payload"] = json.loads(text)
                except Exception:
                    d["payload"] = text
            else:
                d["payload"] = payload
        except Exception:
            d["payload"] = f"<binary {len(entity.payload)} bytes>"

    return json.dumps(d, indent=2, default=str)


def _show_entity(client: Any, entity_key: str) -> int:
    try:
        entity = client.arkiv.get_entity(entity_key)
    except Exception:
        # Treat lookup errors (parsing, rpc errors, not found) as "not found"
        print(f"Entity not found: {entity_key}", file=sys.stderr)
        return 2

    print(_format_entity(entity))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="explorer")
    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        help="Set the log level for Arkiv and related libraries",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_entity = sub.add_parser("entity", help="Show an entity by key")
    p_entity.add_argument("key", help="Entity key (hex string)")

    args = parser.parse_args(argv)

    # Configure logging if requested
    if getattr(args, "log_level", None):
        level = getattr(logging, args.log_level, None)
        if level is not None:
            logging.basicConfig(level=level)
            # Set Arkiv and common libraries to the requested level so users can see SDK logs
            logging.getLogger("arkiv").setLevel(level)
            logging.getLogger("web3").setLevel(level)
            logging.getLogger("websockets").setLevel(level)
            logging.getLogger("urllib3").setLevel(level)

    if args.cmd == "entity":
        # Try to connect and then show
        try:
            client = _connect_client()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 3

        return _show_entity(client, args.key)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

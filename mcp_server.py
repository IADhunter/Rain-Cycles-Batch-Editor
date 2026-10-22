"""RCBE MCP server (stdio, JSON-RPC 2.0, no dependencies).

Exposes the Rain Cycles Batch Editor as MCP tools so an AI agent can inspect
the input settings and preview batch edits. This server is READ-ONLY: it never
writes to input/ or output/.

Protocol: newline-delimited JSON-RPC 2.0 over stdin/stdout. Logs go to stderr.

Launch (example client config):
    { "command": "python", "args": ["...\\mcp_server.py"] }
"""

import json
import sys

import mcp_tools

PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
DEFAULT_PROTOCOL = "2024-11-05"
SERVER_INFO = {"name": "rcbe", "version": "0.1.0"}

RULES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "description": "Batch rules. Omitted keys keep their defaults.",
    "properties": {
        "palette": {"type": "object", "additionalProperties": {"type": "string"},
                    "description": "Map old Palette id -> new id"},
        "fade_palette": {"type": "object", "additionalProperties": {"type": "string"},
                         "description": "Map old FadePalette id -> new id"},
        "fade_opacity": {"type": "number", "default": 1.0},
        "terrain_palette": {"type": "object", "additionalProperties": {"type": "string"}},
        "terrain_fade_palette": {"type": "object", "additionalProperties": {"type": "string"}},
        "terrain_fade_opacity": {"type": "number", "default": 1.0},
        "decal": {"type": "number", "default": 1.0},
        "light": {"type": "number", "default": 1.0},
        "grime": {"type": "number", "default": 1.0},
        "clouds": {"type": "number", "default": 1.0},
        "terrain_effects": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "light": {"type": "number"}, "stain_amount": {"type": "number"},
                "stain_brightness": {"type": "number"}, "stain_height": {"type": "number"},
                "waves": {"type": "number"}, "grain": {"type": "number"},
                "sky_fade": {"type": "number"},
            },
        },
        "rain_cycles": {
            "type": "object", "additionalProperties": False,
            "description": "Partial update: omitted type/view/tint keep the existing tag; "
                           "view=\"None\" or tint=\"\" clears it; type=\"Vanilla\" removes the line.",
            "properties": {
                "enabled": {"type": "boolean"},
                "type": {"type": "string", "enum": ["Blend", "Static", "Vanilla"]},
                "view": {"type": "string", "enum": ["ACV", "RTV", "PSV", "ORV", "AUV", "None"]},
                "tint": {"type": ["string", "null"]},
            },
        },
        "template": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "replace": {"type": "object", "additionalProperties": {"type": "string"}},
                "create": {"type": ["string", "null"]},
            },
        },
        "effect_color_a": {
            "type": "object", "additionalProperties": False,
            "properties": {"enabled": {"type": "boolean"}, "h": {"type": "number"},
                           "s": {"type": "number"}, "v": {"type": "number"},
                           "only": {"type": "boolean"}},
        },
        "effect_color_b": {
            "type": "object", "additionalProperties": False,
            "properties": {"enabled": {"type": "boolean"}, "h": {"type": "number"},
                           "s": {"type": "number"}, "v": {"type": "number"},
                           "only": {"type": "boolean"}},
        },
        "bkg": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "enabled": {"type": "boolean"},
                "mod": {"type": "string"},
                "sky": {"type": "string"},
                "fog": {"type": "string"},
                "sun": {"type": "string"},
                "only_view": {"type": "boolean"},
                "view": {"type": "string"},
            },
            "description": "Writes <Mod:mod,sky[,sun[,fog]]> into the RainCycles line. "
                           "Needs mod+sky; the line must have a view. "
                           "only_view (GUI: Only Effect View) restricts to settings with a vanilla view effect; "
                           "view (name or ACV/RTV/PSV/ORV/AUV, case-insensitive) narrows it to that effect "
                           "(only when only_view is true).",
        },
    },
}

TOOLS = [
    {
        "name": "list_settings",
        "description": "List every .txt in input/ with a compact summary "
                       "(template, palettes, RainCycles tags, whether it has a vanilla view effect).",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "properties": {"input_dir": {"type": "string", "description": "Optional override; defaults to <editor>/input"}},
        },
    },
    {
        "name": "get_setting",
        "description": "Show the full summary plus the relevant raw lines "
                       "(RainCycles, Effects, Template, EffectColorA/B) of one setting file.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["file"],
            "properties": {"file": {"type": "string"}, "input_dir": {"type": "string"}},
        },
    },
    {
        "name": "preview_rules",
        "description": "Apply rules in-memory and return unified diffs per file WITHOUT writing anything. "
                       "Use it to validate edits before the user runs the GUI Generate.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["rules"],
            "properties": {
                "rules": RULES_SCHEMA,
                "files": {"type": "array", "items": {"type": "string"},
                          "description": "Optional exact filenames; default: all .txt in input/"},
                "name_contains": {"type": "string",
                                  "description": "Optional case-insensitive substring filter on filenames"},
                "input_dir": {"type": "string"},
                "max_diff_chars": {"type": "integer", "default": 20000},
            },
        },
    },
    {
        "name": "generate",
        "description": "Apply rules and WRITE the results to output/ (mirrors the GUI Generate). "
                       "Never modifies input/; files are written as-is with the same names.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["rules"],
            "properties": {
                "rules": RULES_SCHEMA,
                "files": {"type": "array", "items": {"type": "string"},
                          "description": "Optional exact filenames; default: all .txt in input/"},
                "name_contains": {"type": "string",
                                  "description": "Optional case-insensitive substring filter on filenames"},
                "input_dir": {"type": "string"},
                "output_dir": {"type": "string",
                               "description": "Optional override; defaults to <editor>/output"},
            },
        },
    },
    {
        "name": "list_vanilla_views",
        "description": "List the vanilla room effects that create a background 'view' "
                       "(used by bkg.only_view).",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
    {
        "name": "rules_reference",
        "description": "Return the rules object structure, defaults and notes.",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
]

HANDLERS = {
    "list_settings": lambda a: mcp_tools.list_settings(a.get("input_dir")),
    "get_setting": lambda a: mcp_tools.get_setting(a["file"], a.get("input_dir")),
    "preview_rules": lambda a: mcp_tools.preview_rules(
        a["rules"], a.get("files"), a.get("name_contains"),
        a.get("input_dir"), int(a.get("max_diff_chars", 20000))),
    "generate": lambda a: mcp_tools.generate(
        a["rules"], a.get("files"), a.get("name_contains"),
        a.get("input_dir"), a.get("output_dir")),
    "list_vanilla_views": lambda a: mcp_tools.list_vanilla_views(),
    "rules_reference": lambda a: mcp_tools.rules_reference(),
}


# ============================================================
# TRANSPORTE
# ============================================================
def _send(obj):
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(data + b"\n")
    sys.stdout.buffer.flush()


def _ok(id_, result):
    _send({"jsonrpc": "2.0", "id": id_, "result": result})


def _error(id_, code, message):
    _send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})


def _log(msg):
    print(f"[rcbe-mcp] {msg}", file=sys.stderr, flush=True)


def _handle(msg):
    method = msg.get("method")
    id_ = msg.get("id")
    params = msg.get("params") or {}
    is_request = "id" in msg

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in PROTOCOL_VERSIONS else DEFAULT_PROTOCOL
        _ok(id_, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })
        return

    if method == "ping":
        if is_request:
            _ok(id_, {})
        return

    if method == "tools/list":
        _ok(id_, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            _ok(id_, {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True})
            return
        try:
            result = handler(args)
            text = json.dumps(result, ensure_ascii=False, indent=2)
            _ok(id_, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as exc:  # tool errors are results, not protocol errors
            _log(f"tool {name} failed: {exc}")
            _ok(id_, {"content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}], "isError": True})
        return

    # Capacidades que no ofrecemos: responder vacío si el cliente las sondea.
    if method == "resources/list":
        _ok(id_, {"resources": []})
        return
    if method == "prompts/list":
        _ok(id_, {"prompts": []})
        return
    if method in ("resources/templates/list",):
        _ok(id_, {"resourceTemplates": []})
        return
    if method == "logging/setLevel":
        _ok(id_, {})
        return

    # Notificaciones desconocidas: ignorar. Peticiones desconocidas: error.
    if is_request:
        _error(id_, -32601, f"Method not found: {method}")


def main():
    _log(f"ready (cwd={sys.argv[0]})")
    while True:
        raw = sys.stdin.buffer.readline()
        if not raw:
            break
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line.decode("utf-8"))
        except Exception as exc:
            _log(f"parse error: {exc}")
            _error(None, -32700, "Parse error")
            continue

        try:
            _handle(msg)
        except Exception as exc:
            _log(f"dispatch error: {exc}")
            if "id" in msg:
                _error(msg.get("id"), -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    main()

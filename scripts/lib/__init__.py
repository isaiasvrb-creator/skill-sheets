#!/usr/bin/env python3
"""
Sheets Ratos - Biblioteca compartilhada
Auth (google-api-python-client), .env loader, output helpers, error handling
Suporta OAuth2 proprio ou compartilhado com google-ads-ratos/ga4-ratos.
"""

import json
import os
import sys
import time

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

def ensure_sdk():
    try:
        import googleapiclient.discovery  # noqa: F401
        import google.oauth2.credentials  # noqa: F401
        return True
    except ImportError:
        print("ERRO: SDK do Google nao instalado.", file=sys.stderr)
        print("  Instale com: pip3 install google-api-python-client google-auth google-auth-oauthlib", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

_ENV_SEARCH_PATHS = [
    os.path.expanduser("~/.claude/skills/sheets/.env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
]

_FALLBACK_ENV_PATHS = [
    os.path.expanduser("~/.claude/skills/ga4/.env"),
    os.path.expanduser("~/.claude/skills/google-ads/.env"),
]


def _parse_env(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and not os.environ.get(key):
                os.environ[key] = value


def _load_env_file():
    for env_path in _ENV_SEARCH_PATHS:
        if os.path.isfile(env_path):
            _parse_env(env_path)
            return env_path
    return None


def _load_fallback_env():
    for env_path in _FALLBACK_ENV_PATHS:
        if os.path.isfile(env_path):
            _parse_env(env_path)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_sheets_service = None
_drive_service = None


def _build_credentials():
    ensure_sdk()
    from google.oauth2.credentials import Credentials

    _load_env_file()

    client_id = os.environ.get("SHEETS_CLIENT_ID")
    client_secret = os.environ.get("SHEETS_CLIENT_SECRET")
    refresh_token = os.environ.get("SHEETS_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        _load_fallback_env()
        client_id = client_id or os.environ.get("GA4_CLIENT_ID") or os.environ.get("GOOGLE_ADS_CLIENT_ID")
        client_secret = client_secret or os.environ.get("GA4_CLIENT_SECRET") or os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
        refresh_token = refresh_token or os.environ.get("SHEETS_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        print("ERRO: Credenciais OAuth2 nao encontradas.", file=sys.stderr)
        print("  Configure SHEETS_CLIENT_ID, SHEETS_CLIENT_SECRET, SHEETS_REFRESH_TOKEN", file=sys.stderr)
        print("  em ~/.claude/skills/sheets/.env", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Para gerar o refresh token:", file=sys.stderr)
        print("    python3 ~/.claude/skills/sheets/scripts/generate_token.py \\", file=sys.stderr)
        print("      --client-id SEU_ID --client-secret SEU_SECRET", file=sys.stderr)
        sys.exit(1)

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SHEETS_SCOPES,
    )


def sheets_service():
    global _sheets_service
    if _sheets_service is None:
        from googleapiclient.discovery import build
        _sheets_service = build("sheets", "v4", credentials=_build_credentials(), cache_discovery=False)
    return _sheets_service


def drive_service():
    global _drive_service
    if _drive_service is None:
        from googleapiclient.discovery import build
        _drive_service = build("drive", "v3", credentials=_build_credentials(), cache_discovery=False)
    return _drive_service


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def print_error(msg):
    print(f"ERRO: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Sheet helpers
# ---------------------------------------------------------------------------

def resolve_sheet_id(spreadsheet_id, sheet_name_or_id):
    """Resolve o sheetId numerico a partir de um nome de aba ou ID.

    Se sheet_name_or_id for numerico, retorna como int.
    Caso contrario, busca pelo titulo na spreadsheet.
    """
    if sheet_name_or_id is None:
        # Primeira aba
        meta = sheets_service().spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return meta["sheets"][0]["properties"]["sheetId"]

    try:
        return int(sheet_name_or_id)
    except (TypeError, ValueError):
        pass

    meta = sheets_service().spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta["sheets"]:
        if sheet["properties"]["title"] == sheet_name_or_id:
            return sheet["properties"]["sheetId"]

    print_error(f"Aba '{sheet_name_or_id}' nao encontrada em {spreadsheet_id}")
    sys.exit(1)


def parse_range_to_grid(spreadsheet_id, range_a1):
    """Converte range A1 (ex: 'Sheet1!A1:C10') em GridRange dict."""
    if "!" in range_a1:
        sheet_name, cell_range = range_a1.split("!", 1)
        # Remove aspas simples (notacao A1 usa 'Sheet Name'!A1 quando tem espaco/acento)
        if sheet_name.startswith("'") and sheet_name.endswith("'"):
            sheet_name = sheet_name[1:-1].replace("''", "'")
    else:
        sheet_name = None
        cell_range = range_a1

    sheet_id = resolve_sheet_id(spreadsheet_id, sheet_name)

    start_cell, _, end_cell = cell_range.partition(":")
    start_col, start_row = _parse_cell(start_cell)
    if end_cell:
        end_col, end_row = _parse_cell(end_cell)
    else:
        end_col, end_row = start_col, start_row

    grid = {"sheetId": sheet_id}
    if start_row is not None:
        grid["startRowIndex"] = start_row - 1
    if end_row is not None:
        grid["endRowIndex"] = end_row
    if start_col is not None:
        grid["startColumnIndex"] = start_col - 1
    if end_col is not None:
        grid["endColumnIndex"] = end_col
    return grid


def _parse_cell(cell):
    """Separa letras (coluna) de numeros (linha). Retorna (col_idx_1based, row_1based).

    Suporta 'A', '1', 'A1', 'AB12'. Retorna None se faltar componente.
    """
    if not cell:
        return None, None
    col_chars = ""
    row_digits = ""
    for ch in cell:
        if ch.isalpha():
            col_chars += ch.upper()
        elif ch.isdigit():
            row_digits += ch

    col_idx = None
    if col_chars:
        col_idx = 0
        for ch in col_chars:
            col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)

    row_idx = int(row_digits) if row_digits else None
    return col_idx, row_idx


def hex_to_rgb(hex_or_name):
    """Converte '#rrggbb' ou nome em dict {red, green, blue} (0-1 floats)."""
    if not hex_or_name:
        return None
    named = {
        "black": "#000000", "white": "#ffffff", "red": "#ff0000",
        "green": "#00aa00", "blue": "#2563eb", "gray": "#808080",
        "grey": "#808080", "yellow": "#ffcc00", "orange": "#ff6600",
    }
    value = named.get(hex_or_name.lower(), hex_or_name)
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def handle_api_error(func):
    def wrapper(*args, **kwargs):
        ensure_sdk()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e)
            error_data = {"error": True, "message": error_str}

            if "403" in error_str or "PERMISSION_DENIED" in error_str:
                error_data["hint"] = (
                    "Sem permissao. Verifique se o usuario OAuth tem acesso a planilha "
                    "ou se o escopo inclui spreadsheets/drive.file."
                )
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                error_data["hint"] = "Rate limit atingido (60 write/min). Aguarde 60s."
            if "401" in error_str or "UNAUTHENTICATED" in error_str or "invalid_grant" in error_str:
                error_data["hint"] = "Refresh token invalido ou expirado. Rode generate_token.py novamente."
            if "404" in error_str or "NOT_FOUND" in error_str:
                error_data["hint"] = "Planilha ou range nao encontrado. Verifique o --id e o --range."

            print(json.dumps(error_data, indent=2, ensure_ascii=False, default=str))
            sys.exit(1)
    return wrapper


def safe_delay(seconds=0.3):
    time.sleep(seconds)

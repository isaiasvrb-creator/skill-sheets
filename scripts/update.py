#!/usr/bin/env python3
"""
Edita Google Sheets: valores, validacao, formatacao, abas, compartilhamento.

Subcomandos:
  values         — escreve valores num range (sobrescreve)
  append         — adiciona linhas ao fim
  validation     — dropdown (lista suspensa)
  format         — formata celulas (negrito, cor, alinhamento)
  number-format  — formato de numero (percent, currency, date)
  freeze         — congela linhas/colunas
  add-sheet      — adiciona nova aba
  share          — compartilha via email
"""
import argparse
import json
import sys

from lib import (
    drive_service,
    handle_api_error,
    hex_to_rgb,
    parse_range_to_grid,
    print_json,
    resolve_sheet_id,
    sheets_service,
)


def _parse_data(raw):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERRO: --data invalido: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print("ERRO: --data deve ser um JSON array de arrays.", file=sys.stderr)
        sys.exit(1)
    return [row if isinstance(row, list) else [row] for row in data]


@handle_api_error
def cmd_values(args):
    values = _parse_data(args.data)
    resp = sheets_service().spreadsheets().values().update(
        spreadsheetId=args.id,
        range=args.range,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()
    print_json({"updated_range": resp.get("updatedRange"), "updated_cells": resp.get("updatedCells")})


@handle_api_error
def cmd_append(args):
    values = _parse_data(args.data)
    resp = sheets_service().spreadsheets().values().append(
        spreadsheetId=args.id,
        range=args.range,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()
    print_json({
        "updated_range": resp.get("updates", {}).get("updatedRange"),
        "updated_rows": resp.get("updates", {}).get("updatedRows"),
    })


@handle_api_error
def cmd_validation(args):
    grid = parse_range_to_grid(args.id, args.range)
    values_list = [v.strip() for v in args.values.split(",") if v.strip()]

    request = {
        "setDataValidation": {
            "range": grid,
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in values_list],
                },
                "strict": args.strict,
                "showCustomUi": True,
            },
        }
    }
    resp = sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=args.id,
        body={"requests": [request]},
    ).execute()
    print_json({"ok": True, "range": args.range, "values": values_list, "replies": len(resp.get("replies", []))})


@handle_api_error
def cmd_format(args):
    grid = parse_range_to_grid(args.id, args.range)
    text_format = {}
    if args.bold:
        text_format["bold"] = True
    if args.italic:
        text_format["italic"] = True
    if args.fg:
        text_format["foregroundColor"] = hex_to_rgb(args.fg)
    if args.font_size:
        text_format["fontSize"] = args.font_size

    cell_format = {}
    if text_format:
        cell_format["textFormat"] = text_format
    if args.bg:
        cell_format["backgroundColor"] = hex_to_rgb(args.bg)
    if args.halign:
        cell_format["horizontalAlignment"] = args.halign.upper()
    if args.valign:
        cell_format["verticalAlignment"] = args.valign.upper()
    if args.wrap:
        cell_format["wrapStrategy"] = "WRAP"

    if not cell_format:
        print("ERRO: informe ao menos uma opcao de formatacao.", file=sys.stderr)
        sys.exit(1)

    fields = []
    if "textFormat" in cell_format:
        fields.append("userEnteredFormat.textFormat")
    if "backgroundColor" in cell_format:
        fields.append("userEnteredFormat.backgroundColor")
    if "horizontalAlignment" in cell_format:
        fields.append("userEnteredFormat.horizontalAlignment")
    if "verticalAlignment" in cell_format:
        fields.append("userEnteredFormat.verticalAlignment")
    if "wrapStrategy" in cell_format:
        fields.append("userEnteredFormat.wrapStrategy")

    request = {
        "repeatCell": {
            "range": grid,
            "cell": {"userEnteredFormat": cell_format},
            "fields": ",".join(fields),
        }
    }
    sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=args.id,
        body={"requests": [request]},
    ).execute()
    print_json({"ok": True, "range": args.range})


NUMBER_FORMAT_PATTERNS = {
    "percent": "0%",
    "percent-1": "0.0%",
    "percent-2": "0.00%",
    "currency": '"R$" #,##0.00',
    "number": "#,##0.00",
    "integer": "#,##0",
    "date": "dd/mm/yyyy",
    "datetime": "dd/mm/yyyy hh:mm",
    "time": "hh:mm",
}

NUMBER_FORMAT_TYPES = {
    "percent": "PERCENT",
    "percent-1": "PERCENT",
    "percent-2": "PERCENT",
    "currency": "CURRENCY",
    "number": "NUMBER",
    "integer": "NUMBER",
    "date": "DATE",
    "datetime": "DATE_TIME",
    "time": "TIME",
}


@handle_api_error
def cmd_number_format(args):
    grid = parse_range_to_grid(args.id, args.range)
    fmt_type = args.type
    pattern = args.pattern or NUMBER_FORMAT_PATTERNS.get(fmt_type)
    gs_type = NUMBER_FORMAT_TYPES.get(fmt_type, "NUMBER")

    if not pattern:
        print(f"ERRO: --type '{fmt_type}' desconhecido. Use --pattern para custom.", file=sys.stderr)
        sys.exit(1)

    request = {
        "repeatCell": {
            "range": grid,
            "cell": {"userEnteredFormat": {"numberFormat": {"type": gs_type, "pattern": pattern}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    }
    sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=args.id,
        body={"requests": [request]},
    ).execute()
    print_json({"ok": True, "range": args.range, "type": fmt_type, "pattern": pattern})


@handle_api_error
def cmd_freeze(args):
    sheet_id = resolve_sheet_id(args.id, args.sheet)
    grid_props = {}
    if args.rows is not None:
        grid_props["frozenRowCount"] = args.rows
    if args.cols is not None:
        grid_props["frozenColumnCount"] = args.cols
    if not grid_props:
        print("ERRO: informe --rows ou --cols.", file=sys.stderr)
        sys.exit(1)

    request = {
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": grid_props},
            "fields": ",".join(f"gridProperties.{k}" for k in grid_props),
        }
    }
    sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=args.id,
        body={"requests": [request]},
    ).execute()
    print_json({"ok": True, "sheet_id": sheet_id, **grid_props})


@handle_api_error
def cmd_add_sheet(args):
    request = {"addSheet": {"properties": {"title": args.title}}}
    if args.rows:
        request["addSheet"]["properties"].setdefault("gridProperties", {})["rowCount"] = args.rows
    if args.cols:
        request["addSheet"]["properties"].setdefault("gridProperties", {})["columnCount"] = args.cols

    resp = sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=args.id,
        body={"requests": [request]},
    ).execute()
    props = resp["replies"][0]["addSheet"]["properties"]
    print_json({"ok": True, "sheet_id": props["sheetId"], "title": props["title"]})


@handle_api_error
def cmd_share(args):
    if args.role == "owner" and not args.confirm:
        print("ERRO: role 'owner' transfere a posse. Use --confirm para continuar.", file=sys.stderr)
        sys.exit(1)

    body = {
        "type": "user",
        "role": args.role,
        "emailAddress": args.email,
    }
    resp = drive_service().permissions().create(
        fileId=args.id,
        body=body,
        sendNotificationEmail=not args.no_notify,
        transferOwnership=(args.role == "owner"),
        fields="id,emailAddress,role",
    ).execute()
    print_json({"ok": True, "permission_id": resp["id"], "email": resp["emailAddress"], "role": resp["role"]})


def main():
    parser = argparse.ArgumentParser(description="Edita Google Sheets")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("values", help="Escreve valores num range")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True, help="Notacao A1, ex: Sheet1!A1:C10")
    p.add_argument("--data", required=True, help="JSON array de arrays")
    p.set_defaults(func=cmd_values)

    p = sub.add_parser("append", help="Adiciona linhas ao fim")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--data", required=True)
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("validation", help="Dropdown de lista")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--values", required=True, help="Lista separada por virgula, ex: Sim,Nao")
    p.add_argument("--strict", action="store_true", help="Rejeita valores fora da lista")
    p.set_defaults(func=cmd_validation)

    p = sub.add_parser("format", help="Formatacao (negrito, cor, alinhamento)")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--bold", action="store_true")
    p.add_argument("--italic", action="store_true")
    p.add_argument("--fg", help="Cor do texto (#hex ou nome)")
    p.add_argument("--bg", help="Cor de fundo (#hex ou nome)")
    p.add_argument("--font-size", type=int)
    p.add_argument("--halign", choices=["left", "center", "right"])
    p.add_argument("--valign", choices=["top", "middle", "bottom"])
    p.add_argument("--wrap", action="store_true")
    p.set_defaults(func=cmd_format)

    p = sub.add_parser("number-format", help="Formato de numero")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--type", required=True, help=f"Tipo: {', '.join(NUMBER_FORMAT_PATTERNS)}")
    p.add_argument("--pattern", help="Pattern custom (sobrescreve --type)")
    p.set_defaults(func=cmd_number_format)

    p = sub.add_parser("freeze", help="Congela linhas/colunas")
    p.add_argument("--id", required=True)
    p.add_argument("--sheet", help="Nome ou ID da aba (default: primeira)")
    p.add_argument("--rows", type=int)
    p.add_argument("--cols", type=int)
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("add-sheet", help="Adiciona nova aba")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--rows", type=int)
    p.add_argument("--cols", type=int)
    p.set_defaults(func=cmd_add_sheet)

    p = sub.add_parser("share", help="Compartilha via email")
    p.add_argument("--id", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--role", default="writer", choices=["reader", "commenter", "writer", "owner"])
    p.add_argument("--no-notify", action="store_true", help="Nao manda email de aviso")
    p.add_argument("--confirm", action="store_true", help="Confirma transferencia de posse (role=owner)")
    p.set_defaults(func=cmd_share)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

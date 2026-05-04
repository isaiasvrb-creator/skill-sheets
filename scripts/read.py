#!/usr/bin/env python3
"""
Le Google Sheets.

Subcomandos:
  values  — le valores de um range
  meta    — metadata da planilha (abas, tamanho)
"""
import argparse

from lib import handle_api_error, print_json, sheets_service


@handle_api_error
def cmd_values(args):
    resp = sheets_service().spreadsheets().values().get(
        spreadsheetId=args.id,
        range=args.range,
        valueRenderOption=args.render,
    ).execute()
    print_json({
        "range": resp.get("range"),
        "values": resp.get("values", []),
        "row_count": len(resp.get("values", [])),
    })


@handle_api_error
def cmd_meta(args):
    resp = sheets_service().spreadsheets().get(
        spreadsheetId=args.id,
        fields="spreadsheetId,spreadsheetUrl,properties.title,sheets.properties",
    ).execute()
    sheets_meta = []
    for sh in resp.get("sheets", []):
        p = sh["properties"]
        sheets_meta.append({
            "sheet_id": p["sheetId"],
            "title": p["title"],
            "index": p.get("index"),
            "rows": p.get("gridProperties", {}).get("rowCount"),
            "cols": p.get("gridProperties", {}).get("columnCount"),
            "frozen_rows": p.get("gridProperties", {}).get("frozenRowCount", 0),
            "frozen_cols": p.get("gridProperties", {}).get("frozenColumnCount", 0),
        })
    print_json({
        "id": resp["spreadsheetId"],
        "url": resp["spreadsheetUrl"],
        "title": resp["properties"]["title"],
        "sheets": sheets_meta,
    })


def main():
    parser = argparse.ArgumentParser(description="Le Google Sheets")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("values", help="Le valores de um range")
    p.add_argument("--id", required=True)
    p.add_argument("--range", required=True, help="Notacao A1, ex: Sheet1!A1:C10")
    p.add_argument(
        "--render",
        default="FORMATTED_VALUE",
        choices=["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
        help="Como renderizar os valores (default: FORMATTED_VALUE)",
    )
    p.set_defaults(func=cmd_values)

    p = sub.add_parser("meta", help="Metadata da planilha")
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_meta)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

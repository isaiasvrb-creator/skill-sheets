#!/usr/bin/env python3
"""
Cria Google Sheets via Sheets API.

Subcomandos:
  blank      — planilha em branco
  from-csv   — planilha a partir de CSV local
  from-json  — planilha a partir de JSON (lista de listas)
"""
import argparse
import csv
import json
import sys

from lib import handle_api_error, print_json, sheets_service


@handle_api_error
def cmd_blank(args):
    body = {"properties": {"title": args.title}}
    if args.sheet_title:
        body["sheets"] = [{"properties": {"title": args.sheet_title}}]
    resp = sheets_service().spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
    print_json({"id": resp["spreadsheetId"], "url": resp["spreadsheetUrl"]})


def _rows_from_csv(path, delimiter=","):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        return [row for row in reader]


def _rows_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("ERRO: JSON deve ser uma lista de listas.", file=sys.stderr)
        sys.exit(1)
    return [row if isinstance(row, list) else [row] for row in data]


def _create_with_rows(title, sheet_title, rows):
    svc = sheets_service()
    body = {"properties": {"title": title}}
    if sheet_title:
        body["sheets"] = [{"properties": {"title": sheet_title}}]
    resp = svc.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl,sheets.properties").execute()
    sheet_id_num = resp["sheets"][0]["properties"]["title"]

    if rows:
        svc.spreadsheets().values().update(
            spreadsheetId=resp["spreadsheetId"],
            range=f"{sheet_id_num}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()

    return {"id": resp["spreadsheetId"], "url": resp["spreadsheetUrl"], "rows_written": len(rows)}


@handle_api_error
def cmd_from_csv(args):
    rows = _rows_from_csv(args.file, delimiter=args.delimiter)
    print_json(_create_with_rows(args.title, args.sheet_title, rows))


@handle_api_error
def cmd_from_json(args):
    rows = _rows_from_json(args.file)
    print_json(_create_with_rows(args.title, args.sheet_title, rows))


def main():
    parser = argparse.ArgumentParser(description="Cria Google Sheets")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("blank", help="Planilha em branco")
    p1.add_argument("--title", required=True, help="Titulo da planilha")
    p1.add_argument("--sheet-title", help="Titulo da primeira aba (default: Sheet1)")
    p1.set_defaults(func=cmd_blank)

    p2 = sub.add_parser("from-csv", help="A partir de CSV")
    p2.add_argument("--file", required=True, help="Arquivo CSV")
    p2.add_argument("--title", required=True, help="Titulo da planilha")
    p2.add_argument("--sheet-title", help="Titulo da primeira aba")
    p2.add_argument("--delimiter", default=",", help="Delimitador do CSV (default: ,)")
    p2.set_defaults(func=cmd_from_csv)

    p3 = sub.add_parser("from-json", help="A partir de JSON (lista de listas)")
    p3.add_argument("--file", required=True, help="Arquivo JSON")
    p3.add_argument("--title", required=True, help="Titulo da planilha")
    p3.add_argument("--sheet-title", help="Titulo da primeira aba")
    p3.set_defaults(func=cmd_from_json)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

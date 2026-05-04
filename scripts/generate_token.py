#!/usr/bin/env python3
"""
Gera refresh token OAuth2 com escopos spreadsheets + drive.file.
Uso: python3 generate_token.py --client-id XXX --client-secret XXX

Reaproveite o Client ID/Secret do Google Cloud que ja usa em
outras skills (so precisa habilitar Sheets API e Drive API
no mesmo projeto do Google Cloud).
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

REDIRECT_URI = "http://localhost:8844"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    args = parser.parse_args()

    params = {
        "client_id": args.client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("\n=== Gerar Token OAuth2 (Sheets + Drive) ===\n")
    print("1. Abra essa URL no navegador:\n")
    print(auth_url)
    print("\n2. Faca login e autorize.")
    print("3. Vai dar erro de 'site nao pode ser acessado' — e normal.")
    print("4. Copie o valor do parametro 'code=' da URL de redirect e cole abaixo:\n")

    code = input("Code: ").strip()

    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        print("\n=== TOKEN GERADO COM SUCESSO ===\n")
        print(f"SHEETS_REFRESH_TOKEN={result['refresh_token']}")
        print(f"\nEscopos: {', '.join(SCOPES)}")
        print("\nAtualize ~/.claude/skills/sheets/.env com esse refresh token.")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nERRO {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

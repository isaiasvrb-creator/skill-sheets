---
name: sheets
description: Cria, edita e le Google Sheets via Sheets API + Drive API. Cria planilhas com dados iniciais, aplica formulas, adiciona validacao de dados (dropdown Sim/Nao, lista), formata celulas (negrito, percentual, moeda, cor), adiciona abas, congela linhas, compartilha por email. Use quando o usuario mencionar google sheets, planilha, spreadsheet, dropdown, validacao de dados, formula, compartilhar planilha. Tambem dispara com /sheets setup.
---

# Sheets

Skill completa para criar e editar Google Sheets via Sheets API + Drive API. Substitui o MCP basico do Google Drive (que so cria a partir de CSV e nao aplica validacao/formatacao).

**IMPORTANTE: Esta skill usa SOMENTE os scripts Python locais. NAO usar MCPs de Google Drive para estas operacoes.**

## Setup (primeira vez)

### 1. Dependencias

```bash
pip3 install google-api-python-client google-auth google-auth-oauthlib
```

### 2. Criar .env

Criar `~/.claude/skills/sheets/.env`:

```
# Sheets, Configuracao OAuth2
# Reaproveite o Client ID/Secret do Google Cloud que voce ja usa em outras skills.
SHEETS_CLIENT_ID=""
SHEETS_CLIENT_SECRET=""
SHEETS_REFRESH_TOKEN=""
```

### 3. Gerar refresh token

```bash
python3 ~/.claude/skills/sheets/scripts/generate_token.py \
  --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET
```

Escopos usados: `spreadsheets` (criar/editar) + `drive.file` (compartilhar/mover arquivos criados).

Colar a URL no navegador, autorizar, copiar o `code=` da URL de redirect, colar no terminal. O script retorna o refresh token, cole no `.env`.

### 4. Testar

```bash
python3 ~/.claude/skills/sheets/scripts/create.py blank --title "Teste Sheets"
```

Deve retornar o ID e URL da planilha.

## Como usar

Todos os scripts estao em `~/.claude/skills/sheets/scripts/`. O padrao:

```
python3 <script>.py <subcomando> [argumentos]
```

---

## Referencia rapida

### create.py: Criar planilha

| Subcomando | O que faz | Exemplo |
|---|---|---|
| `blank` | Planilha em branco | `create.py blank --title "Minha Planilha"` |
| `from-csv` | Planilha a partir de arquivo CSV local | `create.py from-csv --file dados.csv --title "Ação X"` |
| `from-json` | Planilha a partir de JSON (lista de listas) | `create.py from-json --file grid.json --title "X"` |

### update.py: Editar planilha

| Subcomando | O que faz | Exemplo |
|---|---|---|
| `values` | Escrever valores num range (sobrescreve) | `update.py values --id SHEET_ID --range "Sheet1!A1:C3" --data '[["a","b","c"],[1,2,3],[4,5,6]]'` |
| `append` | Adicionar linhas ao fim de um range | `update.py append --id SHEET_ID --range "Sheet1!A:C" --data '[[1,2,3]]'` |
| `validation` | Dropdown (lista suspensa) num range | `update.py validation --id SHEET_ID --range "Sheet1!H10:H91" --values "Sim,Não"` |
| `format` | Formatar celulas: negrito, cor, numero, alinhamento | `update.py format --id SHEET_ID --range "Sheet1!A1:L1" --bold --bg "#0b0b0b" --fg "#ffffff"` |
| `number-format` | Formato de numero (percent, currency, date) | `update.py number-format --id SHEET_ID --range "Sheet1!B3:B4" --type percent` |
| `freeze` | Congelar linhas/colunas | `update.py freeze --id SHEET_ID --rows 7` |
| `add-sheet` | Adicionar nova aba | `update.py add-sheet --id SHEET_ID --title "Resumo"` |
| `share` | Compartilhar planilha com email | `update.py share --id SHEET_ID --email usuario@gmail.com --role writer` |

### read.py: Ler planilha

| Subcomando | O que faz | Exemplo |
|---|---|---|
| `values` | Ler valores de um range | `read.py values --id SHEET_ID --range "Sheet1!A1:L91"` |
| `meta` | Metadata da planilha (abas, tamanho) | `read.py meta --id SHEET_ID` |

---

## Parametros comuns

| Parametro | O que faz |
|---|---|
| `--id` | Spreadsheet ID (extrair da URL, entre `/d/` e `/edit`) |
| `--range` | Range em notacao A1: `Sheet1!A1:C10` |
| `--data` | JSON array de arrays (linhas), ex: `[["a","b"],["c","d"]]` |
| `--values` | Lista separada por virgula (para validation): `Sim,Não` |
| `--title` | Titulo da planilha ou aba |

---

## Formatos de numero disponiveis

| Tipo | Resultado |
|---|---|
| `percent` | `45%` (aceita decimais: `percent-1` = `45.3%`) |
| `currency` | `R$ 1.234,56` |
| `number` | `1.234,56` |
| `integer` | `1.234` |
| `date` | `21/04/2026` |
| `datetime` | `21/04/2026 14:30` |

## Cores

Aceitam hex (`#0b0b0b`) ou nome (`red`, `green`, `blue`, `black`, `white`, `gray`).

## Roles de compartilhamento

- `reader`: so leitura
- `commenter`: pode comentar
- `writer`: pode editar
- `owner`: transfere posse (requer confirmacao)

---

## Fluxos comuns

### Criar planilha + aplicar dropdown + formatar

```bash
# 1. Criar planilha a partir de CSV
python3 create.py from-csv --file dados.csv --title "Minha Acao" 
# retorna: {"id": "1abc...", "url": "..."}

# 2. Aplicar dropdown Sim/Não
python3 update.py validation --id 1abc --range "Sheet1!H10:I91" --values "Sim,Não"

# 3. Formatar cabecalho
python3 update.py format --id 1abc --range "Sheet1!A7:L7" --bold --bg "#0b0b0b" --fg "#ffffff"

# 4. Congelar primeiras 7 linhas
python3 update.py freeze --id 1abc --rows 7

# 5. Formato percentual nas taxas
python3 update.py number-format --id 1abc --range "Sheet1!B3:B4" --type percent

# 6. Compartilhar com cliente
python3 update.py share --id 1abc --email cliente@email.com --role writer
```

### Atualizar planilha existente com fórmulas

```bash
python3 update.py values --id 1abc --range "Sheet1!B3" \
  --data '[["=IFERROR(COUNTIF(H10:H91,\"Sim\")/COUNTA(E10:E91),0)"]]'
```

## Regras de seguranca

1. **Nunca hardcodar credenciais**: sempre usar `.env`
2. **Confirmar antes de deletar ou sobrescrever** grandes ranges
3. **Compartilhamento via email**: confirmar email e role antes de executar
4. **Rate limits**: Sheets API tem limite de 60 write req/min por projeto. Se estourar, aguardar 60s

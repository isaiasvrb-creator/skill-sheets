# sheets

Skill do Claude Code para criar, editar e ler Google Sheets via Sheets API + Drive API.

Substitui o MCP padrão do Google Drive (que só cria a partir de CSV e não aplica validação ou formatação rica).

## O que ela faz

- Cria planilhas em branco, a partir de CSV ou JSON
- Escreve valores e fórmulas em qualquer range
- Aplica validação de dados (dropdowns Sim/Não, listas customizadas)
- Formata células (negrito, cor de fundo, cor de texto, alinhamento)
- Formato de número (percent, currency BRL, date, datetime, integer)
- Congela linhas/colunas
- Adiciona abas
- Compartilha planilha por email com role (reader, commenter, writer, owner)
- Lê valores e metadata

## Instalação

### Para galera que usa Claude Code (recomendado)

Cole o seguinte prompt no seu Claude Code:

```
Quero instalar a skill "sheets" deste repositório:
https://github.com/isaiasvrb-creator/skill-sheets

Faz pra mim, passo a passo, parando pra confirmar quando precisar de input:

1. Clonar o repositório em ~/.claude/skills/sheets/
2. Verificar se as libs Python estão instaladas, se não estiverem, instalar:
   pip3 install google-api-python-client google-auth google-auth-oauthlib
3. Me explicar como criar Client ID e Client Secret OAuth 2.0 no Google Cloud Console:
   - Criar projeto (ou usar existente)
   - Ativar Google Sheets API e Google Drive API
   - Criar credencial OAuth 2.0 tipo "Desktop app"
   - Adicionar meu email como "test user" na tela de consentimento OAuth
4. Quando eu te passar o Client ID e Client Secret, rodar:
   python3 ~/.claude/skills/sheets/scripts/generate_token.py --client-id MEU_ID --client-secret MEU_SECRET
5. Me guiar pra colar a URL no navegador, autorizar, copiar o "code=" da URL de redirect e colar no terminal
6. Criar o arquivo ~/.claude/skills/sheets/.env com as 3 variáveis (SHEETS_CLIENT_ID, SHEETS_CLIENT_SECRET, SHEETS_REFRESH_TOKEN)
7. Testar criando uma planilha de teste:
   python3 ~/.claude/skills/sheets/scripts/create.py blank --title "Teste Sheets"
8. Me retornar o link da planilha pra eu confirmar que funcionou

Importante: a credencial Google é minha. Não compartilho com ninguém.
```

### Manual

```bash
# 1. Clonar
git clone https://github.com/isaiasvrb-creator/skill-sheets.git ~/.claude/skills/sheets

# 2. Instalar libs
pip3 install google-api-python-client google-auth google-auth-oauthlib

# 3. Criar projeto no Google Cloud, ativar Sheets API + Drive API,
#    criar credencial OAuth 2.0 "Desktop app". Adicionar seu email como test user.

# 4. Gerar refresh token
python3 ~/.claude/skills/sheets/scripts/generate_token.py \
  --client-id SEU_CLIENT_ID \
  --client-secret SEU_CLIENT_SECRET

# 5. Criar ~/.claude/skills/sheets/.env com:
SHEETS_CLIENT_ID=...
SHEETS_CLIENT_SECRET=...
SHEETS_REFRESH_TOKEN=...

# 6. Testar
python3 ~/.claude/skills/sheets/scripts/create.py blank --title "Teste"
```

## Como o Claude Code aciona

A skill dispara automaticamente quando você menciona termos como: google sheets, planilha, spreadsheet, dropdown, validação de dados, fórmula, compartilhar planilha. Também pode chamar com `/sheets`.

## Documentação completa

Veja [SKILL.md](SKILL.md) para a referência completa de comandos, fluxos e parâmetros.

## Licença

MIT. Veja [LICENSE](LICENSE).

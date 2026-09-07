# 05 — Ambiente de desenvolvimento

Passo a passo para sair do zero até a API rodando. Escrito a partir do
ambiente real de desenvolvimento (**Windows 11**), com os problemas que
apareceram de verdade documentados ao final.

## Pré-requisitos

| Ferramenta | Versão | Observação |
|---|---|---|
| Python | **3.14** | Ver [nota sobre a versão](#por-que-python-314) |
| PostgreSQL | 14+ | Local, para desenvolvimento |
| Git | qualquer | |
| DBeaver | opcional | Cliente gráfico usado no projeto |

## Setup

### 1. Clonar

```bash
git clone https://github.com/<usuario>/CRM-andrade.git
cd CRM-andrade/crm-andrade-backend
```

### 2. Ambiente virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1        # PowerShell
# source venv/Scripts/activate     # Git Bash
```

Se o PowerShell recusar o script por política de execução:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

`-Scope Process` limita o efeito a esta janela — não é uma mudança
permanente na máquina.

### 3. Dependências

```bash
pip install -r requirements-dev.txt   # inclui requirements.txt
```

Para produção, apenas `pip install -r requirements.txt`.

### 4. Banco de dados

Criar o banco (ele **não** é criado automaticamente):

```sql
CREATE DATABASE crm_andrade;
```

### 5. Arquivo `.env`

Na raiz de `crm-andrade-backend/`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/crm_andrade
```

O `.env` **não é versionado** — contém credenciais. Está no `.gitignore`.

### 6. Migrations

```bash
alembic upgrade head
```

Cria a tabela `clients` com todas as constraints.

### 7. Rodar

```bash
uvicorn app.main:app --reload
```

API em <http://127.0.0.1:8000>, Swagger em <http://127.0.0.1:8000/docs>.

O `--reload` reinicia o servidor a cada alteração de arquivo. É para
desenvolvimento apenas — em produção, nunca.

## Verificando que está tudo certo

```bash
# 1. Conexão com o banco
python -c "from app.database import engine; engine.connect(); print('ok')"

# 2. Migrations aplicadas (deve mostrar a revisão mais recente)
alembic current

# 3. Model e banco em sincronia (deve dizer "No new upgrade operations")
alembic check
```

---

## Notas específicas de Windows

Registradas porque custaram tempo real de troubleshooting.

### Por que Python 3.14

A tentativa inicial com **Python 3.9** falhou ao instalar o `greenlet`
(dependência do SQLAlchemy). O `greenlet` tem extensões em C e, quando não
existe *wheel* pré-compilado para a combinação de versão do Python +
plataforma, o pip tenta compilar do zero — o que exige o **Visual C++ Build
Tools**, que não estava instalado.

Atualizar o Python resolveu porque existe wheel pronta para a versão nova.
A lição: em Windows, erro de build em pacote com extensão C geralmente é
falta de wheel para a sua versão de Python, não um bug do pacote.

### `UnicodeDecodeError` no psycopg2

Sintoma: ao conectar, um `UnicodeDecodeError` incompreensível, sem nenhuma
menção a banco de dados.

**Causa raiz: o banco `crm_andrade` não existia.** O Postgres respondia com
uma mensagem de erro em português (`banco de dados "crm_andrade" não
existe`), e o psycopg2 falhava ao decodificar os acentos dessa mensagem.
O erro de encoding era *sintoma do sintoma* — a mensagem de erro real
nunca chegava a aparecer.

**Se aparecer um `UnicodeDecodeError` na conexão, verifique primeiro se o
banco existe.** O erro quase nunca é sobre encoding.

### `psql` fora do PATH

O instalador do Postgres no Windows não adiciona o `psql` ao PATH. Ou se
usa o caminho completo:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

(o `&` é necessário porque o caminho tem espaços), ou se usa o DBeaver —
que foi o caminho adotado no projeto.

### PowerShell não é Bash

O ambiente tem os dois disponíveis, e a sintaxe difere:

| | PowerShell | Git Bash |
|---|---|---|
| Ativar venv | `.\venv\Scripts\Activate.ps1` | `source venv/Scripts/activate` |
| Encadear comandos | `cmd1; if ($?) { cmd2 }` | `cmd1 && cmd2` |
| Variável de ambiente | `$env:VAR = "x"` | `export VAR=x` |
| Descartar saída | `2>$null` | `2>/dev/null` |

Notavelmente, **`&&` não funciona no PowerShell 5.1** — é erro de sintaxe,
não apenas um comportamento diferente.

### O `venv` acumulou pacotes alheios

O `venv` atual tem `graphifyy` e `numpy` instalados, que não pertencem a
este projeto (provavelmente de algum experimento). Eles **não** estão no
`requirements.txt`. Recriar o ambiente do zero a partir do
`requirements-dev.txt` limparia isso.

---

## Comandos do dia a dia

```bash
uvicorn app.main:app --reload            # sobe a API
alembic upgrade head                     # aplica migrations pendentes
alembic current                          # em que revisão o banco está
alembic history --verbose                # histórico completo
alembic revision --autogenerate -m "..." # nova migration (LEIA o resultado!)
alembic downgrade -1                     # desfaz a última migration
alembic check                            # model e banco estão sincronizados?
```

Sobre `--autogenerate`, há uma armadilha importante com renomeações:
ver [06 — Migrations](06-migrations.md).

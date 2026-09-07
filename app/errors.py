"""Tradução de erros do banco para respostas HTTP.

Motivação
---------
Sem isto, qualquer violação de constraint no Postgres sobe como
`sqlalchemy.exc.IntegrityError` até o topo da stack e o FastAPI devolve
`500 Internal Server Error` — mentindo para o cliente da API, porque o
servidor não falhou: o *pedido* é que era inválido.

Por que traduzir aqui e não checar antes de inserir
---------------------------------------------------
A alternativa seria consultar o banco antes ("já existe alguém com este
CPF?") e devolver o erro sem tentar o insert. Isso tem duas falhas:

1. **Race condition (TOCTOU).** Entre a consulta e o insert, outra
   requisição pode inserir o mesmo CPF. A checagem prévia dá a *ilusão*
   de segurança; só a constraint no banco realmente garante.
2. **Duplicação de regra.** A regra passaria a existir em dois lugares
   (aplicação e banco), que podem divergir com o tempo.

Portanto: o banco continua sendo a única fonte de verdade sobre
integridade, e esta camada apenas traduz o "não" dele para HTTP.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

# SQLSTATE — códigos padronizados do Postgres para violação de integridade.
# https://www.postgresql.org/docs/current/errcodes-appendix.html
UNIQUE_VIOLATION = "23505"
CHECK_VIOLATION = "23514"
NOT_NULL_VIOLATION = "23502"
FOREIGN_KEY_VIOLATION = "23503"
# O Postgres usa um código próprio para violação de ON DELETE RESTRICT,
# distinto do de chave estrangeira comum. Apagar um cliente que tem
# cobranças cai aqui.
RESTRICT_VIOLATION = "23001"

# Mensagens por nome de constraint. Manter o nome da constraint como chave
# (e não o texto do erro do Postgres) é deliberado: o texto muda conforme o
# idioma configurado no servidor, o nome da constraint não.
#
# Para cobrir uma tabela nova, basta acrescentar entradas aqui — nenhuma
# rota precisa mudar. É o Open-Closed Principle aplicado a erros.
CONSTRAINT_MESSAGES: dict[str, str] = {
    "uq_clients_cpf": "Já existe um cliente cadastrado com este CPF.",
    "uq_clients_cnpj": "Já existe um cliente cadastrado com este CNPJ.",
    "check_person_type_valid": (
        "Tipo de pessoa inválido. Use 'INDIVIDUAL' ou 'COMPANY'."
    ),
    "check_document_by_person_type": (
        "Documento incompatível com o tipo de pessoa: informe CPF para "
        "'INDIVIDUAL' e CNPJ para 'COMPANY', nunca os dois."
    ),
    "fk_charges_client_id": (
        "Cliente inexistente, ou o cliente possui cobranças e não pode ser "
        "removido."
    ),
    "uq_charges_external_id": (
        "Já existe uma cobrança registrada com este identificador do banco."
    ),
    "check_charge_status_valid": "Status de cobrança inválido.",
    "check_charge_amount_positive": "O valor da cobrança deve ser maior que zero.",
    "check_charge_paid_at_matches_status": (
        "Incoerência: cobrança paga precisa ter data de pagamento, e apenas "
        "cobranças pagas podem tê-la."
    ),
    "check_charge_issued_consistency": (
        "Incoerência: identificador do banco e data de emissão devem existir "
        "juntos."
    ),
}

# Cada classe de violação vira um status HTTP diferente, porque significam
# coisas diferentes para quem consome a API:
#   409 Conflict           -> o pedido é válido, mas colide com o estado atual
#   422 Unprocessable      -> o pedido é sintaticamente ok, mas viola uma regra
STATUS_BY_SQLSTATE: dict[str, int] = {
    UNIQUE_VIOLATION: 409,
    CHECK_VIOLATION: 422,
    NOT_NULL_VIOLATION: 422,
    FOREIGN_KEY_VIOLATION: 409,
    RESTRICT_VIOLATION: 409,
}

DEFAULT_STATUS = 409
DEFAULT_MESSAGE = "A operação viola uma regra de integridade dos dados."


def _extract_diagnostics(error: IntegrityError) -> tuple[str | None, str | None]:
    """Extrai (sqlstate, nome da constraint) do erro original do driver.

    `error.orig` é a exceção crua do psycopg2. Nem todo driver expõe
    `diag`, por isso o acesso é defensivo — um erro ao *tratar* o erro
    seria pior do que o erro original.
    """
    original = getattr(error, "orig", None)
    if original is None:
        return None, None

    sqlstate = getattr(original, "pgcode", None)
    diagnostics = getattr(original, "diag", None)
    constraint = getattr(diagnostics, "constraint_name", None) if diagnostics else None
    return sqlstate, constraint


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    sqlstate, constraint = _extract_diagnostics(exc)

    status_code = STATUS_BY_SQLSTATE.get(sqlstate, DEFAULT_STATUS)
    detail = CONSTRAINT_MESSAGES.get(constraint, DEFAULT_MESSAGE)

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "constraint": constraint},
    )

"""Constantes do domínio.

Reunidas em um módulo próprio para que os valores válidos existam em um
lugar só. Sem isto, a mesma lista apareceria no model (CHECK constraint),
no schema Pydantic e em cada comparação espalhada pelo código — livres
para divergir.
"""

# --- Cliente ---------------------------------------------------------------

PERSON_TYPE_INDIVIDUAL = "INDIVIDUAL"
PERSON_TYPE_COMPANY = "COMPANY"

PERSON_TYPES = (PERSON_TYPE_INDIVIDUAL, PERSON_TYPE_COMPANY)

# --- Cobrança --------------------------------------------------------------

# Ciclo de vida do PAGAMENTO. Deliberadamente não inclui estados de emissão
# ("boleto criado no banco") nem de notificação ("enviado no WhatsApp") —
# esses são registrados em colunas próprias.
#
# O motivo: uma cobrança pode estar emitida, notificada E paga ao mesmo
# tempo. Se tudo morasse em uma coluna só, esses fatos seriam mutuamente
# exclusivos, e o sistema perderia informação a cada transição.
CHARGE_STATUS_PENDING = "PENDING"      # aguardando pagamento
CHARGE_STATUS_PAID = "PAID"            # pagamento confirmado
CHARGE_STATUS_OVERDUE = "OVERDUE"      # venceu sem pagamento
CHARGE_STATUS_CANCELLED = "CANCELLED"  # cancelada antes de ser paga

CHARGE_STATUSES = (
    CHARGE_STATUS_PENDING,
    CHARGE_STATUS_PAID,
    CHARGE_STATUS_OVERDUE,
    CHARGE_STATUS_CANCELLED,
)

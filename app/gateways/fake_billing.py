"""Implementação falsa do gateway de cobrança, para desenvolvimento e teste.

Guarda tudo em memória. Não toca a rede, não emite boleto de verdade e não
movimenta dinheiro.

Serve a dois propósitos:

1. **Desbloquear o desenvolvimento.** As credenciais do Inter dependem de
   uma conta PJ que ainda não existe. Com este adaptador, o módulo de
   cobrança inteiro pode ser construído e exercitado antes disso.
2. **Tornar os testes rápidos e determinísticos.** Cenários como "esta
   cobrança foi paga" ou "o banco está fora do ar" são forçados
   diretamente, sem esperar nada acontecer no mundo real.

⚠️ **Um fake que mente é pior que nenhum fake.** Ele cria confiança falsa.
Este aqui reproduz de propósito alguns comportamentos desagradáveis do
mundo real — cobrança paga não pode ser cancelada, id inexistente levanta
erro — mas nenhuma simulação substitui um teste de integração real contra
o Inter antes de ir para produção.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.domain import (
    CHARGE_STATUS_CANCELLED,
    CHARGE_STATUS_PAID,
    CHARGE_STATUS_PENDING,
)
from app.gateways.billing import (
    BillingGateway,
    BillingGatewayError,
    ChargeNotFoundError,
    ChargeRequest,
    IssuedCharge,
)


class FakeBillingGateway(BillingGateway):
    def __init__(self) -> None:
        # external_id -> {"request": ChargeRequest, "status": str}
        self._charges: dict[str, dict] = {}

        # Quando True, toda chamada falha. Permite testar o caminho de erro
        # sem depender de a rede realmente cair.
        self.fail_next_calls = False

    # --- Contrato -----------------------------------------------------------

    def issue(self, request: ChargeRequest) -> IssuedCharge:
        self._maybe_fail()

        external_id = f"FAKE-{uuid.uuid4().hex[:12].upper()}"
        self._charges[external_id] = {
            "request": request,
            "status": CHARGE_STATUS_PENDING,
        }

        return IssuedCharge(
            external_id=external_id,
            issued_at=datetime.now(timezone.utc),
            payment_url=f"https://fake.local/boleto/{external_id}",
            digitable_line="00000.00000 00000.000000 00000.000000 0 00000000000000",
            pix_copy_paste=f"00020126FAKE{external_id}",
        )

    def get_status(self, external_id: str) -> str:
        self._maybe_fail()
        return self._get(external_id)["status"]

    def cancel(self, external_id: str) -> None:
        self._maybe_fail()
        charge = self._get(external_id)

        # Um banco de verdade também recusa isto. Reproduzir a recusa aqui
        # evita que a regra de negócio seja escrita assumindo o contrário.
        if charge["status"] == CHARGE_STATUS_PAID:
            raise BillingGatewayError(
                "Não é possível cancelar uma cobrança já paga."
            )

        charge["status"] = CHARGE_STATUS_CANCELLED

    # --- Auxiliares de teste ------------------------------------------------
    # Não fazem parte do contrato BillingGateway: existem só para que um
    # teste force um cenário. A regra de negócio nunca deve chamá-los.

    def mark_as_paid(self, external_id: str) -> None:
        """Simula o pagamento de uma cobrança pelo cliente."""
        self._get(external_id)["status"] = CHARGE_STATUS_PAID

    def set_status(self, external_id: str, status: str) -> None:
        self._get(external_id)["status"] = status

    def issued_count(self) -> int:
        return len(self._charges)

    def find_request(self, external_id: str) -> Optional[ChargeRequest]:
        charge = self._charges.get(external_id)
        return charge["request"] if charge else None

    def reset(self) -> None:
        self._charges.clear()
        self.fail_next_calls = False

    # --- Internos -----------------------------------------------------------

    def _get(self, external_id: str) -> dict:
        try:
            return self._charges[external_id]
        except KeyError:
            raise ChargeNotFoundError(
                f"Cobrança {external_id} não encontrada."
            ) from None

    def _maybe_fail(self) -> None:
        if self.fail_next_calls:
            raise BillingGatewayError("Falha simulada de comunicação.")

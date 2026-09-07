"""Contrato de emissão de cobrança — a *porta* do módulo de cobrança.

Esta interface é a fronteira entre o domínio do CRM e qualquer instituição
financeira. A regra de negócio depende **dela**, nunca do Banco Inter.

Por que isso importa (Dependency Inversion Principle, o "D" do SOLID):
sem a interface, o domínio dependeria do Inter e o formato da API do banco
vazaria para dentro do sistema. Com ela, a direção se inverte — o Inter é
que precisa se encaixar em um contrato definido por nós, a partir do que o
*domínio* precisa.

Consequências práticas:

- O módulo inteiro pode ser construído e testado com `FakeBillingGateway`,
  sem depender da conta PJ e das credenciais do Inter, que ainda não existem.
- Trocar de banco significa escrever um adaptador novo. Nenhuma regra de
  negócio muda.
- Testes não tocam a rede nem emitem boleto de verdade.

Nota sobre o vocabulário: isto **não é o pattern Strategy**. Strategy é
quando existem várias formas igualmente válidas de fazer a mesma coisa e
se escolhe entre elas por regra de negócio, em runtime. Aqui há uma única
intenção — emitir uma cobrança — e as implementações diferem apenas em com
quem falam. O nome correto é porta/adaptador (arquitetura hexagonal).

Ver docs/decisoes/0012-gateway-de-cobranca-abstrato.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class BillingGatewayError(Exception):
    """Falha ao falar com a instituição financeira.

    Existe para que quem chama o gateway não precise conhecer `requests`,
    `httpx` ou qualquer detalhe do adaptador. Cada implementação traduz
    seus próprios erros para esta exceção — mantendo o acoplamento na
    fronteira, que é justamente o ponto da interface.
    """


class ChargeNotFoundError(BillingGatewayError):
    """A cobrança não existe na instituição financeira."""


@dataclass(frozen=True)
class Payer:
    """Quem paga a cobrança.

    Deliberadamente **não** é o model `Client` do SQLAlchemy. Se o gateway
    recebesse a entidade do ORM, ficaria acoplado à persistência — e o
    adaptador do Inter passaria a depender de como guardamos os dados, o
    que não é da conta dele.
    """

    name: str
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass(frozen=True)
class ChargeRequest:
    """O que o domínio pede ao banco.

    `reference_id` é o nosso UUID da cobrança, enviado ao banco como
    identificador próprio. Serve para correlacionar os dois lados quando
    chegar um webhook de pagamento — sem ele, o casamento dependeria de
    valor + vencimento, que não é único.
    """

    reference_id: str
    amount: Decimal
    due_date: date
    payer: Payer
    description: Optional[str] = None


@dataclass(frozen=True)
class IssuedCharge:
    """O que o banco devolve depois de emitir.

    Os três meios de pagamento são opcionais porque nem toda instituição
    devolve todos. O domínio não pode assumir que existe linha digitável,
    nem que existe Pix.
    """

    external_id: str
    issued_at: datetime
    payment_url: Optional[str] = None
    digitable_line: Optional[str] = None
    pix_copy_paste: Optional[str] = None


class BillingGateway(ABC):
    """Porta de emissão de cobrança.

    Toda implementação concreta (Inter, fake, outro banco) cumpre este
    contrato. Métodos levantam `BillingGatewayError` em caso de falha de
    comunicação — nunca exceções específicas de biblioteca HTTP.
    """

    @abstractmethod
    def issue(self, request: ChargeRequest) -> IssuedCharge:
        """Emite a cobrança na instituição financeira."""

    @abstractmethod
    def get_status(self, external_id: str) -> str:
        """Consulta o status atual. Retorna um dos valores de CHARGE_STATUSES.

        Traduzir o vocabulário do banco para o nosso é responsabilidade do
        adaptador. O domínio nunca vê o jargão do Inter.
        """

    @abstractmethod
    def cancel(self, external_id: str) -> None:
        """Cancela uma cobrança ainda não paga."""

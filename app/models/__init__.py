"""Registro central dos models.

Todos os models precisam ser importados aqui — e não só onde são usados.

Motivo: o SQLAlchemy resolve `relationship("Charge")` por **nome**, no
momento em que configura os mappers. Se a classe `Charge` nunca tiver sido
importada, esse nome não existe no registro e o mapper do `Client` falha
com "failed to locate a name 'Charge'" — mesmo que nada na requisição
mexesse com cobranças.

Como importar `app.models.client` executa este __init__ primeiro, basta
listar os models aqui para que todos estejam sempre registrados.
"""

from app.models.charge import Charge  # noqa: F401
from app.models.client import Client  # noqa: F401

__all__ = ["Charge", "Client"]

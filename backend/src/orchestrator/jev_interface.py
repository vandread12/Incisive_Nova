"""
Interfaz aislada con el motor de decisión Jev (SPEC-01).

Principio de desacoplamiento estricto: Jev recibe únicamente un
`JevDecisionInput` y devuelve un `JevDecisionOutput`. NO conoce APIs bancarias,
cotizaciones de Abroad, direcciones Stellar ni detalles de ejecución. El
orquestador es el único que traduce la decisión de Jev en acciones concretas.
"""

from typing import Protocol, runtime_checkable

from ..schemas.jev_schemas import JevDecisionInput, JevDecisionOutput


@runtime_checkable
class JevInterface(Protocol):
    """Contrato que debe cumplir cualquier motor de decisión Jev.

    Al ser un Protocol, permite inyectar tanto una implementación real
    (cliente HTTP al motor Jev) como un doble de prueba, sin acoplamiento.
    """

    async def evaluate(self, decision_input: JevDecisionInput) -> JevDecisionOutput:
        """Evalúa una orden y devuelve la decisión de Jev."""
        ...

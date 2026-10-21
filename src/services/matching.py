"""Matching de habilidades y generación de tickets."""

import json
import logging
import os
from typing import Any

from .catalog import MOCK_OFFERS, consultar_vacantes_bd
from .config import configuration_value

logger = logging.getLogger(__name__)


def _ticket_local(habilidad: str, vacantes: list[dict[str, Any]]) -> str:
    seleccionadas = (vacantes or MOCK_OFFERS)[:3]
    lineas = [
        "========================================",
        "          CHAMBAYA - TICKET DE EMPLEO",
        "========================================",
        f"Habilidad registrada: {habilidad}",
        "",
    ]
    for numero, oferta in enumerate(seleccionadas, start=1):
        lineas.extend([
            f"{numero}. {oferta['titulo']}",
            f"   Fuente: {oferta['fuente']}",
            f"   Dirección: {oferta['direccion']}",
            f"   Teléfono: {oferta['telefono']}",
            f"   Recomendación: {oferta['req']}",
            "",
        ])
    lineas.extend(["Presenta este ticket o llama al contacto.", "========================================"])
    return "\n".join(lineas)


def agente_match_habilidades(habilidad_usuario: str) -> str:
    vacantes = consultar_vacantes_bd()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = configuration_value("AZURE_OPENAI_API_KEY", "azure-openai-api-key")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not (endpoint and deployment):
        return _ticket_local(habilidad_usuario, vacantes)

    try:
        from openai import AzureOpenAI, OpenAIError
        from azure.core.exceptions import AzureError
    except ImportError:
        logger.exception("openai no está instalado; se usará el ticket local.")
        return _ticket_local(habilidad_usuario, vacantes)

    try:
        client_kwargs = {
            "azure_endpoint": endpoint,
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            client_kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
        response = AzureOpenAI(**client_kwargs).chat.completions.create(
            model=deployment,
            temperature=0.2,
            messages=[
                {"role": "system", "content": (
                    "Eres el agente de empleabilidad comunitaria de chambaYA. "
                    "Selecciona hasta tres oportunidades apropiadas según la habilidad. "
                    "Responde solo texto corto apto para imprimir, con título, dirección, "
                    "teléfono y recomendación sencilla. No inventes datos."
                )},
                {"role": "user", "content": (
                    f"Habilidad del joven: {habilidad_usuario}\n"
                    f"Vacantes disponibles: {json.dumps(vacantes, ensure_ascii=False)}"
                )},
            ],
        )
        return response.choices[0].message.content or _ticket_local(habilidad_usuario, vacantes)
    except (AzureError, OpenAIError, OSError, ValueError):
        logger.exception("No fue posible consultar Azure OpenAI; se usará el ticket local.")
        return _ticket_local(habilidad_usuario, vacantes)

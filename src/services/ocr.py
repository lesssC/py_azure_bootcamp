"""OCR de anuncios con Azure Document Intelligence."""

import logging
import os

from .config import configuration_value

logger = logging.getLogger(__name__)


def extraer_texto_anuncio(documento: bytes) -> str:
    endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = configuration_value(
        "DOCUMENT_INTELLIGENCE_API_KEY", "document-intelligence-api-key"
    )
    if not endpoint:
        return "OCR no configurado. Registra la vacante manualmente o configura Document Intelligence."

    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.exceptions import AzureError, HttpResponseError
    except ImportError as error:
        logger.exception("azure-ai-documentintelligence no está instalado.")
        return f"No fue posible procesar el anuncio: {error}"

    try:
        if key:
            from azure.core.credentials import AzureKeyCredential
            credential = AzureKeyCredential(key)
        else:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
        result = DocumentIntelligenceClient(endpoint, credential).begin_analyze_document(
            "prebuilt-read", body=documento
        ).result()
        return result.content or "No se detectó texto legible en la imagen."
    except HttpResponseError as error:
        logger.exception(
            "Document Intelligence devolvio HTTP %s.",
            getattr(error, "status_code", "desconocido"),
        )
        if getattr(error, "status_code", None) == 503:
            return (
                "El servicio de lectura está temporalmente ocupado. "
                "Espera unos segundos y vuelve a intentarlo."
            )
        return "No fue posible leer el anuncio en este momento. Inténtalo nuevamente."
    except (AzureError, ImportError, OSError, TimeoutError, ValueError) as error:
        logger.exception("No fue posible procesar el anuncio con Document Intelligence.")
        return "No fue posible procesar el anuncio. Verifica la imagen e inténtalo nuevamente."

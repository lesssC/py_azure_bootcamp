"""Fachada de compatibilidad para los servicios de chambaYA."""

from services.announcement import estructurar_anuncio
from services.catalog import (
    consultar_vacantes_bd,
    consultar_ofertas_admin,
    actualizar_oferta_bd,
    desactivar_oferta_bd,
    estado_catalogo,
    registrar_oferta_bd,
)
from services.matching import agente_match_habilidades
from services.ocr import extraer_texto_anuncio

__all__ = [
    "agente_match_habilidades",
    "consultar_vacantes_bd",
    "consultar_ofertas_admin",
    "actualizar_oferta_bd",
    "desactivar_oferta_bd",
    "estado_catalogo",
    "extraer_texto_anuncio",
    "estructurar_anuncio",
    "registrar_oferta_bd",
]

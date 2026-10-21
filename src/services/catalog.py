"""Acceso al catálogo de ofertas de Azure SQL."""

import logging
import os
from typing import Any

import pyodbc

from .config import sql_connection

logger = logging.getLogger(__name__)
_database_status = "No consultado"

MOCK_OFFERS = [
    {"id": 1, "titulo": "Ayudante de Pintura y Drywall", "fuente": "Bodega / Mercado", "direccion": "Av. Las Flores 450, Mz B Lote 3", "telefono": "987654321", "req": "Experiencia práctica en brocha o empaste. Ganas de trabajar."},
    {"id": 2, "titulo": "Asistente de Cocina y Menú", "fuente": "Pyme local", "direccion": "Mercado Central, Puesto 12", "telefono": "912345678", "req": "Saber picar verduras y limpiar. Horario de mañanas."},
    {"id": 3, "titulo": "Taller Práctico de Electricidad Residencial", "fuente": "CETPRO", "direccion": "Parroquia San José, Salón Comunal", "telefono": "955554433", "req": "Sin experiencia. Taller gratuito de dos semanas."},
]


def consultar_vacantes_bd() -> list[dict[str, Any]]:
    global _database_status
    if not os.getenv("AZURE_SQL_CONNECTIONSTRING") and not os.getenv("AZURE_SQL_SERVER"):
        _database_status = "Catálogo demo: SQL no configurado"
        return MOCK_OFFERS

    try:
        connection_string, attributes = sql_connection()
        with pyodbc.connect(connection_string, attrs_before=attributes, timeout=8) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT OfertaID, TituloVacante, Fuente, DireccionUbicacion,
                       TelefonoContacto, RequisitosMinimos
                FROM OfertasOportunidades
                WHERE Activo = 1
                ORDER BY FechaRegistro DESC
                """
            )
            offers = [
                {"id": row[0], "titulo": row[1], "fuente": row[2],
                 "direccion": row[3], "telefono": row[4],
                 "req": row[5] or "Consultar detalles al contacto."}
                for row in cursor.fetchall()
            ]
            _database_status = f"Azure SQL: {len(offers)} ofertas activas"
            return offers
    except (OSError, ValueError, pyodbc.Error):
        _database_status = "Catálogo demo: error de conexión con Azure SQL"
        logger.exception("No fue posible consultar Azure SQL; se usará el catálogo demo.")
        return MOCK_OFFERS


def estado_catalogo() -> str:
    return _database_status


def registrar_oferta_bd(titulo: str, fuente: str, direccion: str, telefono: str, requisitos: str) -> int:
    values = [titulo.strip(), fuente.strip(), direccion.strip(), telefono.strip()]
    if not all(values):
        raise ValueError("Completa título, fuente, dirección y teléfono.")

    try:
        connection_string, attributes = sql_connection()
        with pyodbc.connect(connection_string, attrs_before=attributes, timeout=8) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO OfertasOportunidades
                    (TituloVacante, Fuente, DireccionUbicacion,
                     TelefonoContacto, RequisitosMinimos)
                OUTPUT INSERTED.OfertaID
                VALUES (?, ?, ?, ?, ?)
                """,
                *values,
                requisitos.strip() or None,
            )
            oferta_id = cursor.fetchone()[0]
            connection.commit()
            return int(oferta_id)
    except (OSError, ValueError, pyodbc.Error) as error:
        logger.exception("No fue posible guardar la oferta en Azure SQL.")
        raise RuntimeError("No fue posible guardar la oferta en Azure SQL.") from error

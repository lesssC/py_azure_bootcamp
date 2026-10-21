"""Configuración y credenciales externas."""

import logging
import os
import struct

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def configuration_value(environment_name: str, secret_name: str) -> str | None:
    value = os.getenv(environment_name)
    if value:
        return value

    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    if not vault_url:
        return None

    try:
        from azure.core.exceptions import AzureError
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        return SecretClient(
            vault_url=vault_url,
            credential=DefaultAzureCredential(),
        ).get_secret(secret_name).value
    except (AzureError, ImportError, OSError):
        logger.exception("No fue posible leer el secreto %s desde Key Vault.", secret_name)
        return None


def sql_connection() -> tuple[str, dict[int, bytes]]:
    """Construye una conexión SQL con secreto o token Entra ID."""
    connection_string = os.getenv("AZURE_SQL_CONNECTIONSTRING")
    if connection_string:
        return connection_string, {}

    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE", "sqldb-redsosten")
    if not server:
        raise ValueError("Configure AZURE_SQL_CONNECTIONSTRING o AZURE_SQL_SERVER.")

    sql_user = os.getenv("AZURE_SQL_USER")
    sql_password = configuration_value("AZURE_SQL_PASSWORD", "azure-sql-password")
    if sql_user and sql_password:
        return (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{server},1433;Database={database};"
            f"UID={sql_user};PWD={sql_password};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
            {},
        )

    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(
        "https://database.windows.net/.default"
    ).token.encode("utf-16-le")
    return (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{server},1433;Database={database};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=8;",
        {1256: struct.pack("<I", len(token)) + token},
    )

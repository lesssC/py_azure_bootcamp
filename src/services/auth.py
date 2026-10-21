"""Registro, inicio de sesión y roles de usuarios."""

import hashlib
import hmac
import secrets
from typing import Any

import pyodbc

from .config import configuration_value, sql_connection


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"{salt.hex()}${digest.hex()}"


def _password_matches(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), 240_000
        ).hex()
        return hmac.compare_digest(expected, digest_hex)
    except (ValueError, TypeError):
        return False


def _ensure_users_table(cursor: Any) -> None:
    cursor.execute(
        """
        IF OBJECT_ID('dbo.Usuarios', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Usuarios (
                UsuarioID INT IDENTITY(1,1) PRIMARY KEY,
                NombreCompleto VARCHAR(100) NOT NULL,
                Correo VARCHAR(150) NOT NULL UNIQUE,
                PasswordHash VARCHAR(300) NOT NULL,
                Rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
                Activo BIT NOT NULL DEFAULT 1,
                FechaRegistro DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            );
        END
        """
    )


def registrar_usuario(
    nombre: str, correo: str, password: str, invite_code: str = ""
) -> str:
    nombre, correo, password = nombre.strip(), correo.strip().lower(), password.strip()
    if not nombre or not correo or len(password) < 8:
        raise ValueError("Completa tus datos y usa una contraseña de mínimo 8 caracteres.")
    expected_invite = configuration_value("ADMIN_INVITE_CODE", "admin-invite-code")
    rol = "admin" if expected_invite and hmac.compare_digest(
        invite_code.strip(), expected_invite
    ) else "usuario"

    try:
        connection_string, attributes = sql_connection()
        with pyodbc.connect(connection_string, attrs_before=attributes, timeout=8) as connection:
            cursor = connection.cursor()
            _ensure_users_table(cursor)
            cursor.execute(
                """
                INSERT INTO Usuarios (NombreCompleto, Correo, PasswordHash, Rol)
                VALUES (?, ?, ?, ?)
                """,
                nombre, correo, _hash_password(password), rol,
            )
            connection.commit()
            return rol
    except pyodbc.IntegrityError as error:
        raise ValueError("Ese correo ya está registrado.") from error
    except (OSError, ValueError, pyodbc.Error) as error:
        raise RuntimeError("No fue posible crear la cuenta.") from error


def iniciar_sesion(correo: str, password: str) -> dict[str, Any] | None:
    try:
        connection_string, attributes = sql_connection()
        with pyodbc.connect(connection_string, attrs_before=attributes, timeout=8) as connection:
            cursor = connection.cursor()
            _ensure_users_table(cursor)
            row = cursor.execute(
                """
                SELECT UsuarioID, NombreCompleto, Correo, PasswordHash, Rol
                FROM Usuarios
                WHERE Correo = ? AND Activo = 1
                """,
                correo.strip().lower(),
            ).fetchone()
            if row and _password_matches(password, row[3]):
                return {"id": row[0], "nombre": row[1], "correo": row[2], "rol": row[4]}
            return None
    except (OSError, ValueError, pyodbc.Error) as error:
        raise RuntimeError("No fue posible iniciar sesión.") from error

"""Transformación de OCR en campos editables para publicación."""

import re


def estructurar_anuncio(texto: str) -> dict[str, str]:
    lineas = [re.sub(r"\s+", " ", linea).strip(" •*-:") for linea in texto.splitlines()]
    lineas = [linea for linea in lineas if linea]
    texto_normalizado = " ".join(lineas)
    texto_mayusculas = texto_normalizado.upper()
    titulo = ""
    for linea in lineas:
        if "EMPRESA DE" in linea.upper() and (
            "SOLICIT" in linea.upper() or "PERSONAL" in linea.upper()
        ):
            titulo = re.sub(r"^(URGENTE[, ]*)", "", linea, flags=re.IGNORECASE).strip()
            break
    if not titulo:
        titulo = "Personal para empresa de alimentos y gaseosas"

    telefono_match = re.search(
        r"(?<!\d)(?:\+?51[\s-]?)?(9\d{8}|[2-9]\d{6,7})(?!\d)",
        texto_normalizado,
    )
    areas = [
        linea for linea in lineas
        if linea.upper() in {
            "VENTAS", "MARKETING DIGITAL", "PROMOTORA DE VENTAS",
            "PUBLICIDAD", "DISTRIBUCIÓN", "DISTRIBUCION",
            "ATENCIÓN AL CLIENTE", "ATENCION AL CLIENTE",
        }
    ]
    requisitos = []
    if "18 AÑOS" in texto_mayusculas or "18 ANOS" in texto_mayusculas:
        requisitos.append("Mayores de 18 años.")
    if "MEDIO TIEMPO" in texto_mayusculas and "TIEMPO COMPLETO" in texto_mayusculas:
        requisitos.append("Disponibilidad de medio tiempo o tiempo completo.")
    elif "TIEMPO COMPLETO" in texto_mayusculas:
        requisitos.append("Disponibilidad de tiempo completo.")
    if areas:
        requisitos.append("Áreas: " + ", ".join(dict.fromkeys(areas)) + ".")
    pago_match = re.search(r"S[/.]?\s*([0-9][0-9.,]*)", texto_normalizado, re.IGNORECASE)
    if pago_match:
        requisitos.append(f"Pago anunciado: S/ {pago_match.group(1)}.")
    if "SIN EXPERIENCIA" in texto_mayusculas:
        requisitos.append("No se requiere experiencia previa.")
    if "PREVIA CITA" in texto_mayusculas:
        requisitos.append("Postulación previa cita.")
    return {
        "titulo": titulo[:100],
        "fuente": "Anuncio de bodega",
        "direccion": "",
        "telefono": telefono_match.group(0).strip() if telefono_match else "",
        "requisitos": " ".join(requisitos)[:2000],
    }

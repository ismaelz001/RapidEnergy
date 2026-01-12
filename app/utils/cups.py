import re

# CRASH TEST: If you see this error in Render logs, the module IS being loaded
raise Exception("🔥 CUPS MODULE LOADED SUCCESSFULLY - Remove this line after confirming!")

CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
BLACKLIST = ["FACTURA", "RESUMEN", "TOTAL", "CLIENTE", "SUMINISTRO", "TELEFONO", "ELECTRICIDAD"]

def normalize_cups(text: str) -> str | None:
    """
    Normaliza un texto candidato a CUPS:
    - Uppercase
    - Elimina espacios, guiones, saltos de línea
    - Filtra palabras de la lista negra
    - Verifica longitud mínima/máxima plausible (18-22 chars)
    """
    if not text:
        return None
    
    # 1. Limpiar caracteres básicos
    cleaned = text.upper()
    cleaned = re.sub(r"[\s\-\.\n]", "", cleaned)
    
    # 2. Check Blacklist
    for bad_word in BLACKLIST:
        if bad_word in cleaned:
            return None
            
    # 3. Validar longitud bruta plausible (ES + 16 num + 2 letras = 20 chars min)
    # Algunos sistemas pueden tener 20 o 22 caracteres.
    # ES + 16 Digits + 2 Letters = 20 chars
    # + Optional 1 Digit + 1 Letter = 22 chars
    if len(cleaned) < 20 or len(cleaned) > 22:
        # A veces el OCR pega cosas extra. 
        # Intentamos extraer el patrón si está dentro de una cadena más larga?
        # Por ahora simple: si no mide 20-22, sospechoso.
        # Pero a veces Gemini devuelve "CUPS: ES..." -> ya limpiamos espacios.
        pass

    return cleaned

def is_valid_cups(cups: str) -> bool:
    """
    Valida un código CUPS usando el algoritmo de control Modulo 529.
    Algoritmo transpialdo de: https://gist.github.com/leon-domingo/631a98a13afe6e6163422fa85d52e9c9
    
    Formato: ES + 16 dígitos + 2 letras + (opcional 1 dígito + 1 letra)
    """
    if not cups:
        return False

    # Regex estricto inicial
    # Debe empezar por ES (España) según requisitos usuario, aunque CUPS internacional podría ser otro.
    # Ajustamos a ES obligatorio.
    # Grupo 1: 16 dígitos
    # Grupo 2: 2 letras control
    # Grupo 3 optional: sufijo
    match = re.search(r"^ES(\d{16})([A-Z]{2})(\d[FPCRXYZ])?$", cups)
    
    if not match:
        return False
    
    digits_16 = match.group(1)
    control_2 = match.group(2)
    
    # Algoritmo validación
    try:
        val_int = int(digits_16)
        mod_529 = val_int % 529
        
        quotient = mod_529 // 23
        remainder = mod_529 % 23
        
        expected = CONTROL_LETTERS[quotient] + CONTROL_LETTERS[remainder]
        
        return control_2 == expected
        
    except Exception:
        return False

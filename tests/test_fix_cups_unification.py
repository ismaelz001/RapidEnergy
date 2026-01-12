
import sys
import os
import pytest

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.cups import normalize_cups, is_valid_cups

def test_cups_unification_logic():
    # Caso 1: Basura "ESUMENDELAFACTURA"
    # Debe ser rechazada por normalize_cups (blacklist)
    raw_garbage = "ESUMENDELAFACTURA"
    normalized_garbage = normalize_cups(raw_garbage)
    print(f"Garbage '{raw_garbage}' -> Normalized: {normalized_garbage}")
    assert normalized_garbage is None, "normalize_cups should reject 'ESUMENDELAFACTURA' due to blacklist"

    # Caso 2: CUPS válido "ES0022000008763779TF1P"
    raw_valid = "ES0022000008763779TF1P"
    normalized_valid = normalize_cups(raw_valid)
    print(f"Valid '{raw_valid}' -> Normalized: {normalized_valid}")
    assert normalized_valid is not None
    assert is_valid_cups(normalized_valid) is True

    # Caso 3: CUPS con formato extraño pero válido tras normalizar
    raw_spaced = "ES 0022 0000 0876 3779 TF 1P"
    normalized_spaced = normalize_cups(raw_spaced)
    print(f"Spaced '{raw_spaced}' -> Normalized: {normalized_spaced}")
    assert normalized_spaced == "ES0022000008763779TF1P"
    assert is_valid_cups(normalized_spaced) is True

    # Caso 4: Mocking webhook logic
    # "cups_norm = normalize_cups(raw) ... if not is_valid ... None"
    
    # 4a. Invalid checksum
    # ES + 20 chars
    invalid_checksum_cups = "ES0022000008763779XX1P" 
    norm = normalize_cups(invalid_checksum_cups)
    # Puede que normalize lo acepte porque length OK y no blacklist
    if norm and not is_valid_cups(norm):
        final_cups = None
    else:
        final_cups = norm
        
    print(f"Invalid checksum -> Final: {final_cups}")
    assert final_cups is None

if __name__ == "__main__":
    test_cups_unification_logic()

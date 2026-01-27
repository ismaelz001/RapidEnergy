import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.cups import normalize_cups, is_valid_cups

class TestCupsValidation(unittest.TestCase):
    
    def test_normalize_basic(self):
        self.assertEqual(normalize_cups("  ES1234567890123456AB  "), "ES1234567890123456AB")
        self.assertIsNone(normalize_cups("ES-1234.5678")) # Too short, should be None
    
    def test_normalize_blacklist(self):
        self.assertIsNone(normalize_cups("ESUMENDELAFACTURA"))
        self.assertIsNone(normalize_cups("TOTAL IMPORT"))
        self.assertIsNone(normalize_cups("CLIENTE: ES123")) # "CLIENTE" is blacklisted
        
    def test_valid_cups_generated(self):
        # Case 1: N=529 -> mod 529 = 0 -> Q=0 (T), R=0 (T) -> TT
        valid_1 = "ES0000000000000529TT"
        self.assertTrue(is_valid_cups(valid_1), f"Should be valid: {valid_1}")
        
        # Case 2: N=23 -> mod 529 = 23 -> Q=1 (R), R=0 (T) -> RT
        valid_2 = "ES0000000000000023RT"
        self.assertTrue(is_valid_cups(valid_2), f"Should be valid: {valid_2}")

    def test_invalid_cups_format(self):
        self.assertFalse(is_valid_cups("ESUMENDELAFACTURA")) # No digits
        self.assertFalse(is_valid_cups("ES1234")) # Too short
        self.assertFalse(is_valid_cups("FR1234567890123456AB")) # Not ES
        
    def test_invalid_cups_checksum(self):
        # Same as Valid Case 1 but wrong letters
        invalid_1 = "ES0000000000000529XX"
        self.assertFalse(is_valid_cups(invalid_1), "Should check checksum")

if __name__ == '__main__':
    unittest.main()

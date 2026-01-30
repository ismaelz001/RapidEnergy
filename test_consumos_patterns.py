#!/usr/bin/env python3
"""
Test para ver por qué no extrae los consumos P1, P2, P3
"""

import re

# El texto de donde debería extraer
raw_text = """Sus consumos desagregados han sido punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh."""

# Los patrones actuales
patterns_p1 = [
    r"(?i)\bpunta\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
    r"(?i)consumo\s+punta[\s\S]{0,50}?([\d.,]+)",
    r"(?i)(?:P1|punta)\s*[:\-]?\s*([\d.,]+)",
]

patterns_p2 = [
    r"(?i)\bllano\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
    r"(?i)consumo\s+llano[\s\S]{0,50}?([\d.,]+)",
    r"(?i)(?:P2|llano)\s*[:\-]?\s*([\d.,]+)",
]

patterns_p3 = [
    r"(?i)\bvalle\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
    r"(?i)consumo\s+valle[\s\S]{0,50}?([\d.,]+)",
    r"(?i)(?:P3|valle)\s*[:\-]?\s*([\d.,]+)",
]

def test_patterns(patterns, name, text):
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    
    for i, pat in enumerate(patterns):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            print(f"✅ Pattern {i}: {pat}")
            print(f"   Found: {m.group(0)}")
            print(f"   Captured: {m.group(1)}")
        else:
            print(f"❌ Pattern {i}: {pat}")

test_patterns(patterns_p1, "P1 (PUNTA)", raw_text)
test_patterns(patterns_p2, "P2 (LLANO)", raw_text)
test_patterns(patterns_p3, "P3 (VALLE)", raw_text)

# Let's try with the raw text JUST the consumos section
consumos_section = "punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh"
print(f"\n\n{'='*60}")
print("Testing with consumos section only")
print(f"{'='*60}")
print(f"Text: {consumos_section}\n")

test_patterns(patterns_p1, "P1 (PUNTA)", consumos_section)
test_patterns(patterns_p2, "P2 (LLANO)", consumos_section)
test_patterns(patterns_p3, "P3 (VALLE)", consumos_section)

# Let's try a simpler pattern
print(f"\n\n{'='*60}")
print("Testing simpler patterns")
print(f"{'='*60}")

simple_patterns = [
    ("P1 simple", r"punta[:\s]+([\d.,]+)", consumos_section),
    ("P2 simple", r"llano[:\s]+([\d.,]+)", consumos_section),
    ("P3 simple", r"valle[:\s]+([\d.,]+)", consumos_section),
]

for name, pat, text in simple_patterns:
    m = re.search(pat, text, re.IGNORECASE)
    if m:
        print(f"✅ {name}: {pat}")
        print(f"   Captured: {m.group(1)}")
    else:
        print(f"❌ {name}: {pat}")

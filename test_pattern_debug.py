#!/usr/bin/env python3
"""
Test específico para el patrón "consumos desagregados"
"""

import re

text = """estas lecturas reales. Sus consumos desagregados han sido punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh."""

# Test the new pattern
pattern = r"(?i)consumos\s+desagregados.*?punta[:\s]+([\d.,]+)"
m = re.search(pattern, text)

if m:
    print(f"✅ Found: {m.group(0)}")
    print(f"   Captured: {m.group(1)}")
else:
    print(f"❌ Pattern didn't match")
    print(f"Pattern: {pattern}")
    print(f"Text: {text}")
    
    # Try debugging
    print("\n\nDebug steps:")
    m1 = re.search(r"(?i)consumos", text)
    print(f"Step 1 - consumos: {'✅' if m1 else '❌'}")
    
    m2 = re.search(r"(?i)consumos\s+desagregados", text)
    print(f"Step 2 - consumos desagregados: {'✅' if m2 else '❌'}")
    
    m3 = re.search(r"(?i)consumos\s+desagregados.*?punta", text)
    print(f"Step 3 - consumos desagregados ... punta: {'✅' if m3 else '❌'}")
    if m3:
        print(f"         Match: {m3.group(0)}")
    
    m4 = re.search(r"(?i)punta[:\s]+([\d.,]+)", text)
    print(f"Step 4 - punta[:space:](number): {'✅' if m4 else '❌'}")
    if m4:
        print(f"         Captured: {m4.group(1)}")
    
    m5 = re.search(r"(?i)consumos\s+desagregados.*?punta[:\s]+([\d.,]+)", text)
    print(f"Step 5 - Full pattern: {'✅' if m5 else '❌'}")
    if m5:
        print(f"         Captured: {m5.group(1)}")

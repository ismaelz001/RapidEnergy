"""
AUDIT E2E TEST - Sistema OCR + Comparador
Objetivo: Testear extremo a extremo subida de facturas, validación, y comparación
"""

import requests
import os
import json
from typing import Dict, List
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

API_URL = os.getenv("API_URL", "https://rapidenergy.onrender.com/webhook")
DIR_PATH = "E:/MecaEnergy/temp_facturas"

# =============================================================================
# UTILIDADES
# =============================================================================

class Color:
    """Colores ANSI para terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_section(title: str):
    """Imprime una sección visual"""
    print(f"\n{Color.BOLD}{'='*80}{Color.END}")
    print(f"{Color.BLUE}{Color.BOLD}{title}{Color.END}")
    print(f"{Color.BOLD}{'='*80}{Color.END}\n")

def log_success(msg: str):
    print(f"{Color.GREEN}✅ {msg}{Color.END}")

def log_error(msg: str):
    print(f"{Color.RED}❌ {msg}{Color.END}")

def log_warning(msg: str):
    print(f"{Color.YELLOW}⚠️  {msg}{Color.END}")

def log_info(msg: str):
    print(f"ℹ️  {msg}")

# =============================================================================
# FASE 1: PIPELINE OCR - SUBIDA DE FACTURAS
# =============================================================================

def test_fase_1_ocr(facturas_path: str) -> List[Dict]:
    """
    FASE 1: Testea la subida masiva de facturas y valida:
    - Extracción de CUPS
    - Campos parsed_fields
    - Estado de factura
    - missing_fields
    """
    log_section("FASE 1 — PIPELINE OCR: SUBIDA MASIVA DE FACTURAS")
    
    if not os.path.exists(facturas_path):
        log_error(f"Carpeta no encontrada: {facturas_path}")
        return []
    
    files = [f for f in os.listdir(facturas_path) if os.path.isfile(os.path.join(facturas_path, f))]
    log_info(f"Encontradas {len(files)} facturas para procesar")
    
    results = []
    
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(facturas_path, filename)
        log_info(f"\n[{i}/{len(files)}] Procesando: {filename}")
        
        try:
            with open(file_path, "rb") as f:
                # Determinate mime type
                mime_type = "application/pdf"
                if filename.lower().endswith((".jpg", ".jpeg")):
                    mime_type = "image/jpeg"
                elif filename.lower().endswith(".png"):
                    mime_type = "image/png"
                
                upload_files = {"file": (filename, f, mime_type)}
                response = requests.post(f"{API_URL}/upload", files=upload_files, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    factura_id = data.get('id')
                    
                    # FETCH REAL DATA FROM DATABASE
                    real_data_response = requests.get(f"{API_URL}/facturas/{factura_id}", timeout=30)
                    if real_data_response.status_code == 200:
                        factura_data = real_data_response.json()
                        
                        # Analizar factura
                        cups = factura_data.get("cups")
                        estado = factura_data.get("estado_factura")
                        
                        # Parse raw_data para obtener missing_fields
                        raw_data_str = factura_data.get("raw_data")
                        missing_fields = []
                        parsed_fields = {}
                        
                        if raw_data_str:
                            try:
                                raw_data = json.loads(raw_data_str)
                                missing_fields = raw_data.get("missing_fields", [])
                                parsed_fields = raw_data.get("parsed_fields", {})
                            except:
                                pass
                        
                        # Determinar nivel de problema
                        nivel_problema = "OK"
                        problemas = []
                        
                        if not cups:
                            nivel_problema = "P0"
                            problemas.append("CUPS no extraído (BLOQUEANTE)")
                        
                        if estado != "lista_para_comparar":
                            if nivel_problema == "OK":
                                nivel_problema = "P1"
                            problemas.append(f"Estado: {estado} (esperado: lista_para_comparar)")
                        
                        if len(missing_fields) > 0:
                            if nivel_problema == "OK":
                                nivel_problema = "P1"
                            problemas.append(f"Campos faltantes: {', '.join(missing_fields)}")
                        
                        result = {
                            "file": filename,
                            "status": "OK",
                            "factura_id": factura_id,
                            "cups": cups,
                            "estado_factura": estado,
                            "missing_fields": missing_fields,
                            "parsed_fields": parsed_fields,
                            "nivel_problema": nivel_problema,
                            "problemas": problemas,
                            "factura_completa": factura_data
                        }
                        
                        if nivel_problema == "OK":
                            log_success(f"ID {factura_id} | CUPS: {cups} | Estado: {estado}")
                        elif nivel_problema == "P0":
                            log_error(f"ID {factura_id} | BLOQUEANTE: {', '.join(problemas)}")
                        else:
                            log_warning(f"ID {factura_id} | GRAVES: {', '.join(problemas)}")
                        
                        results.append(result)
                    else:
                        log_error(f"Error al obtener datos de factura {factura_id}")
                        results.append({
                            "file": filename,
                            "status": "ERROR_FETCH",
                            "factura_id": factura_id
                        })
                
                elif response.status_code == 409:
                    log_warning(f"DUPLICADA (ya existe en base de datos)")
                    results.append({"file": filename, "status": "DUPLICATE"})
                
                else:
                    log_error(f"HTTP {response.status_code}: {response.text[:200]}")
                    results.append({"file": filename, "status": f"ERROR_{response.status_code}"})
        
        except Exception as e:
            log_error(f"EXCEPCIÓN: {e}")
            results.append({"file": filename, "status": "EXCEPTION", "error": str(e)})
    
    return results

# =============================================================================
# FASE 2: TEST DEL COMPARADOR
# =============================================================================

def test_fase_2_comparador(facturas_results: List[Dict]) -> List[Dict]:
    """
    FASE 2: Testea el comparador para facturas con estado 'lista_para_comparar'
    Valida:
    - Creación de comparativa
    - Creación de ofertas_calculadas
    - Coherencia de cálculos
    """
    log_section("FASE 2 — TEST DEL COMPARADOR")
    
    # Filtrar facturas aptas para comparar
    aptas = [r for r in facturas_results if r.get("estado_factura") == "lista_para_comparar"]
    log_info(f"Facturas aptas para comparar: {len(aptas)} de {len(facturas_results)}")
    
    comparador_results = []
    
    for i, factura_result in enumerate(aptas, 1):
        factura_id = factura_result.get("factura_id")
        filename = factura_result.get("file")
        
        log_info(f"\n[{i}/{len(aptas)}] Comparando factura ID {factura_id} ({filename})")
        
        try:
            response = requests.post(f"{API_URL}/comparar/facturas/{factura_id}", timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validar respuesta
                comparativa_id = data.get("comparativa_id")
                periodo_dias = data.get("periodo_dias")
                current_total = data.get("current_total")
                offers = data.get("offers", [])
                
                # Detectar problemas
                nivel_problema = "OK"
                problemas = []
                
                if not comparativa_id:
                    nivel_problema = "P1"
                    problemas.append("No se creó comparativa")
                
                if not periodo_dias:
                    nivel_problema = "P0"
                    problemas.append("periodo_dias no calculado (BLOQUEANTE)")
                
                if len(offers) == 0:
                    nivel_problema = "P0"
                    problemas.append("Sin ofertas generadas (BLOQUEANTE)")
                
                # Validar ofertas
                for idx, offer in enumerate(offers):
                    tarifa_id = offer.get("tarifa_id")
                    coste = offer.get("estimated_total_periodo") or offer.get("estimated_total")
                    ahorro_periodo = offer.get("ahorro_periodo") or offer.get("saving_amount")
                    breakdown = offer.get("breakdown", {})
                    
                    if not tarifa_id:
                        if nivel_problema == "OK":
                            nivel_problema = "P1"
                        problemas.append(f"Oferta {idx+1}: sin tarifa_id")
                    
                    if coste == 0 or coste is None:
                        if nivel_problema == "OK":
                            nivel_problema = "P1"
                        problemas.append(f"Oferta {idx+1}: coste_estimado es 0 o None")
                    
                    # Validar breakdown
                    if breakdown:
                        coste_energia = breakdown.get("coste_energia", 0)
                        coste_potencia = breakdown.get("coste_potencia", 0)
                        
                        if coste_energia == 0:
                            if nivel_problema == "OK":
                                nivel_problema = "P1"
                            problemas.append(f"Oferta {idx+1}: coste_energia es 0")
                
                result = {
                    "factura_id": factura_id,
                    "filename": filename,
                    "status": "OK",
                    "comparativa_id": comparativa_id,
                    "periodo_dias": periodo_dias,
                    "current_total": current_total,
                    "num_ofertas": len(offers),
                    "nivel_problema": nivel_problema,
                    "problemas": problemas,
                    "offers_sample": offers[:2] if len(offers) > 0 else []  # Muestra 2 ofertas
                }
                
                if nivel_problema == "OK":
                    log_success(f"Comparativa {comparativa_id} | {len(offers)} ofertas | Periodo: {periodo_dias} días")
                elif nivel_problema == "P0":
                    log_error(f"BLOQUEANTE: {', '.join(problemas)}")
                else:
                    log_warning(f"GRAVES: {', '.join(problemas)}")
                
                comparador_results.append(result)
            
            elif response.status_code == 422:
                # Error de dominio (esperado para facturas incompletas)
                error_data = response.json()
                log_warning(f"Error de dominio: {error_data.get('detail', {}).get('message', 'Unknown')}")
                comparador_results.append({
                    "factura_id": factura_id,
                    "filename": filename,
                    "status": "DOMAIN_ERROR",
                    "error": error_data
                })
            
            else:
                log_error(f"HTTP {response.status_code}: {response.text[:200]}")
                comparador_results.append({
                    "factura_id": factura_id,
                    "filename": filename,
                    "status": f"ERROR_{response.status_code}"
                })
        
        except Exception as e:
            log_error(f"EXCEPCIÓN: {e}")
            comparador_results.append({
                "factura_id": factura_id,
                "filename": filename,
                "status": "EXCEPTION",
                "error": str(e)
            })
    
    return comparador_results

# =============================================================================
# REPORTE FINAL
# =============================================================================

def generate_report(fase1_results: List[Dict], fase2_results: List[Dict]):
    """
    Genera el reporte final consolidado con:
    - Tabla de estado actual (semáforo)
    - Lista de bugs priorizada
    - Repro steps
    """
    log_section("REPORTE FINAL DE AUDITORÍA")
    
    # A) TABLA DE ESTADO ACTUAL
    print(f"{Color.BOLD}A) TABLA DE ESTADO ACTUAL{Color.END}\n")
    print(f"{'Factura':<30} | {'CUPS OK':<10} | {'Campos OK':<12} | {'Lista Comp.':<12} | {'Comparador OK':<15} | {'Errores clave':<40}")
    print("-" * 140)
    
    for result in fase1_results:
        if result.get("status") != "OK":
            continue
        
        filename = result["file"][:28]
        cups_ok = "✅" if result.get("cups") else "❌"
        campos_ok = "✅" if len(result.get("missing_fields", [])) == 0 else "❌"
        lista_comparar = "✅" if result.get("estado_factura") == "lista_para_comparar" else "❌"
        
        # Buscar resultado comparador
        comparador_ok = "N/A"
        errores = ", ".join(result.get("problemas", []))[:38]
        
        fase2_match = next((r for r in fase2_results if r.get("factura_id") == result.get("factura_id")), None)
        if fase2_match:
            if fase2_match.get("nivel_problema") == "OK":
                comparador_ok = "✅"
            elif fase2_match.get("nivel_problema") == "P0":
                comparador_ok = "❌ P0"
            else:
                comparador_ok = "⚠️  P1"
            
            if fase2_match.get("problemas"):
                errores = ", ".join(fase2_match["problemas"])[:38]
        
        print(f"{filename:<30} | {cups_ok:<10} | {campos_ok:<12} | {lista_comparar:<12} | {comparador_ok:<15} | {errores:<40}")
    
    # B) LISTA DE BUGS PRIORIZADA
    print(f"\n{Color.BOLD}B) LISTA DE BUGS PRIORIZADA{Color.END}\n")
    
    # Consolidar bugs P0, P1, P2
    bugs_p0 = []
    bugs_p1 = []
    bugs_p2 = []
    
    for result in fase1_results + fase2_results:
        nivel = result.get("nivel_problema")
        problemas = result.get("problemas", [])
        
        for problema in problemas:
            bug_entry = {
                "factura": result.get("file") or result.get("filename"),
                "factura_id": result.get("factura_id"),
                "problema": problema
            }
            
            if nivel == "P0":
                bugs_p0.append(bug_entry)
            elif nivel == "P1":
                bugs_p1.append(bug_entry)
            else:
                bugs_p2.append(bug_entry)
    
    if bugs_p0:
        print(f"{Color.RED}{Color.BOLD}🔴 P0 - BLOQUEANTES:{Color.END}")
        for i, bug in enumerate(bugs_p0, 1):
            print(f"  {i}. [{bug['factura']}] {bug['problema']}")
        print()
    
    if bugs_p1:
        print(f"{Color.YELLOW}{Color.BOLD}🟡 P1 - GRAVES:{Color.END}")
        for i, bug in enumerate(bugs_p1, 1):
            print(f"  {i}. [{bug['factura']}] {bug['problema']}")
        print()
    
    if bugs_p2:
        print(f"{Color.BLUE}{Color.BOLD}🔵 P2 - MEJORAS:{Color.END}")
        for i, bug in enumerate(bugs_p2, 1):
            print(f"  {i}. [{bug['factura']}] {bug['problema']}")
        print()
    
    # C) RESUMEN ESTADÍSTICO
    print(f"\n{Color.BOLD}C) RESUMEN ESTADÍSTICO{Color.END}\n")
    
    total_facturas = len(fase1_results)
    facturas_ok = len([r for r in fase1_results if r.get("nivel_problema") == "OK"])
    facturas_p0 = len([r for r in fase1_results if r.get("nivel_problema") == "P0"])
    facturas_p1 = len([r for r in fase1_results if r.get("nivel_problema") == "P1"])
    
    comparador_ok = len([r for r in fase2_results if r.get("nivel_problema") == "OK"])
    comparador_p0 = len([r for r in fase2_results if r.get("nivel_problema") == "P0"])
    comparador_p1 = len([r for r in fase2_results if r.get("nivel_problema") == "P1"])
    
    print(f"Total facturas procesadas: {total_facturas}")
    print(f"  ✅ OK: {facturas_ok}")
    print(f"  🔴 P0 (bloqueantes): {facturas_p0}")
    print(f"  🟡 P1 (graves): {facturas_p1}")
    print()
    print(f"Total comparaciones ejecutadas: {len(fase2_results)}")
    print(f"  ✅ OK: {comparador_ok}")
    print(f"  🔴 P0 (bloqueantes): {comparador_p0}")
    print(f"  🟡 P1 (graves): {comparador_p1}")
    
    # Exportar JSON completo
    output_file = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "fase1_ocr": fase1_results,
            "fase2_comparador": fase2_results,
            "bugs_p0": bugs_p0,
            "bugs_p1": bugs_p1,
            "bugs_p2": bugs_p2
        }, f, indent=2, ensure_ascii=False)
    
    log_success(f"Reporte JSON exportado: {output_file}")

# =============================================================================
# MAIN
# =============================================================================

def main():
    print(f"""
{Color.BOLD}╔═══════════════════════════════════════════════════════════════════════════╗
║                   AUDIT E2E TEST - OCR + COMPARADOR                       ║
║                      Sistema RapidEnergy / EnergyLuz                      ║
╚═══════════════════════════════════════════════════════════════════════════╝{Color.END}
""")
    
    log_info(f"API URL: {API_URL}")
    log_info(f"Facturas: {DIR_PATH}")
    
    # FASE 1: OCR
    fase1_results = test_fase_1_ocr(DIR_PATH)
    
    # FASE 2: COMPARADOR
    fase2_results = test_fase_2_comparador(fase1_results)
    
    # REPORTE FINAL
    generate_report(fase1_results, fase2_results)

if __name__ == "__main__":
    main()

def _score_page_quality(text: str) -> float:
    """
    BUG B FIX: Score de calidad de una página (0.0 = basura, 1.0 = perfecto).
    Ratio de caracteres imprimibles vs no-imprimibles.
    """
    if not text or len(text) < 10:
        return 0.0
    
    printable = sum(1 for c in text if c.isprintable() or c.isspace())
    total = len(text)
    ratio = printable / total
    
    # Penalizar si hay demasiados caracteres raros consecutivos
    rare_chars = sum(1 for c in text if ord(c) > 127 and not c.isalpha())
    if rare_chars / total > 0.3:
        ratio *= 0.5
    
    return ratio


def extract_data_from_pdf_IMPROVED(file_bytes: bytes):
    """BUG B FIX: Versión mejorada que ignora páginas corruptas"""
    is_pdf = file_bytes.startswith(b"%PDF")

    if is_pdf:
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            
            # BUG B FIX: Extraer y evaluar cada página
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    quality = _score_page_quality(text)
                    pages_text.append({
                        "page": idx + 1,
                        "text": text,
                        "quality": quality
                    })
                    print(f"Página {idx+1}: calidad={quality:.2f}")
            
            # Filtrar páginas útiles (quality > 0.6)
            useful_pages = [p for p in pages_text if p["quality"] > 0.6]
            
            if not useful_pages and pages_text:
                # Todas malas pero hay texto, usar la mejor
                useful_pages = [max(pages_text, key=lambda p: p["quality"])]
                print(f"⚠️ Todas las páginas tienen calidad baja, usando la mejor: página {useful_pages[0]['page']}")
            
            if useful_pages:
                full_text = "\n".join([p["text"] for p in useful_pages])
                ignored = len(pages_text) - len(useful_pages)
                if ignored > 0:
                    print(f"📄 Páginas útiles: {len(useful_pages)}/{len(pages_text)} (ignoradas: {ignored})")
            else:
                full_text = ""

            if len(full_text.strip()) > 50:
                print("PDF digital detectado. Usando pypdf.")
                # Llamar a parse_invoice_text aquí (ya existe en ocr.py)
                return parse_invoice_text(full_text)
            else:
                msg = "PDF escaneado o sin texto útil. Sube una imagen (JPG/PNG)."
                return _empty_result(msg)
        except Exception as e:
            print(f"Error leyendo PDF con pypdf: {e}")
            pass

    # Resto del código (Vision API) continúa igual...

"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import { uploadFactura } from '@/lib/apiClient';

export default function Step1FacturaPage({ params }) {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [ocrData, setOcrData] = useState(null);
  const [error, setError] = useState(null);
  const [facturaId, setFacturaId] = useState(null); // BUG A FIX

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    handleFile(droppedFile);
  };

  const handleFileInput = (e) => {
    const selectedFile = e.target.files[0];
    handleFile(selectedFile);
  };

  const handleFile = async (selectedFile) => {
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploading(true);
    setError(null);

    try {
      const res = await uploadFactura(selectedFile);
      setFacturaId(res.id); // BUG A FIX: Siempre guardar ID
      setOcrData(res.ocr_preview);
      setUploading(false);
      
      // EXITO: Navegar al ID real devuelto por el servidor
      if (res.id) {
        setTimeout(() => {
          router.replace(`/wizard/${res.id}/step-2-validar`);
        }, 1200);
      }
    } catch (err) {
      console.error("Upload error:", err);
      // BUG D FIX: Manejar conflicto (409) con info de factura existente
      if (err.status === 409) {
        try {
          const errorText = err.message || "";
          const detailMatch = errorText.match(/\{[^}]+\}/);
          if (detailMatch) {
            const errorDetail = JSON.parse(detailMatch[0]);
            if (errorDetail.id) {
              setOcrData({
                duplicate: true,
                existing_id: errorDetail.id,
                existing_client: errorDetail.client,
                message: errorDetail.message || "Esta factura ya fue subida."
              });
              setUploading(false);
              return;
            }
          }
        } catch (parseErr) {
          console.log("No se pudo parsear detalle 409:", parseErr);
        }
        setError("Esta factura ya ha sido subida anteriormente.");
      } else {
        setError(err.message || "No se pudo procesar la factura. Inténtalo de nuevo.");
      }
      setUploading(false);
    }
  };

  const handleNext = () => {
    // Fallback por si la auto-redirección falla
    if (ocrData && params.id) {
      router.push(`/wizard/${params.id}/step-2-validar`);
    } else {
      router.push('/dashboard');
    }
  };

  return (
    <WizardLayout
      currentStep={1}
      nextLabel="SIGUIENTE"
      nextDisabled={!facturaId} // BUG A FIX: Solo necesita ID, no OCR
      onNext={handleNext}
    >
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gris-secundario mb-1">
            PASO 1 DE 3
          </p>
          <h1 className="text-2xl font-bold text-gris-texto">
            Sube la factura del cliente
          </h1>
        </div>

        {/* Drop zone */}
        {!file && (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-[rgba(255,255,255,0.1)] rounded-2xl p-16 text-center bg-[#0F172A] hover:border-[#1E3A8A] hover:bg-[#1E3A8A]/5 transition-all cursor-pointer group"
            onClick={() => document.getElementById('file-input').click()}
          >
            <div className="w-16 h-16 mx-auto mb-6 bg-[#1E3A8A]/10 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              📄
            </div>
            <p className="text-xl font-bold text-white mb-2">
              Arrastra la factura aquí.
            </p>
            <p className="text-sm text-[#94A3B8] mb-6">
              Nosotros hacemos el resto.
            </p>
            <span className="inline-flex py-2 px-4 rounded-full bg-[#1E3A8A] text-white text-xs font-bold uppercase tracking-wide">
              Seleccionar archivo
            </span>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileInput}
              className="hidden"
            />
          </div>
        )}

        {/* Uploading state */}
        {uploading && (
          <div className="card text-center">
            <div className="text-4xl mb-3">🔄</div>
            <p className="text-gris-texto font-medium">
              Extrayendo datos de la factura...
            </p>
            <p className="text-sm text-gris-secundario mt-1">
              Esto toma unos segundos
            </p>
          </div>
        )}

        {/* Success state */}
        {ocrData && !uploading && (
          <div className="card border-verde-ahorro bg-verde-ahorro/5">
            <div className="flex items-start gap-3">
              <span className="text-2xl">✓</span>
              <div className="flex-1">
                <h3 className="font-semibold text-gris-texto mb-3">
                  Datos extraídos correctamente
                </h3>
                <div className="space-y-2 text-sm text-gris-texto">
                  <div>
                    <span className="text-gris-secundario">• CUPS:</span> {ocrData.cups || 'No detectado'}
                  </div>
                  <div>
                    <span className="text-gris-secundario">• Total:</span> {ocrData.total_factura || ocrData.importe || '0'}€
                  </div>
                  <div>
                    <span className="text-gris-secundario">• Cliente:</span> {ocrData.titular || ocrData.cliente || 'No detectado'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Duplicate state - BUG D FIX */}
        {ocrData?.duplicate && !uploading && (
          <div className="card border-ambar-alerta bg-ambar-alerta/5">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📋</span>
              <div className="flex-1">
                <h3 className="font-semibold text-gris-texto mb-2">
                  Factura ya registrada
                </h3>
                <p className="text-sm text-gris-secundario mb-4">
                  {ocrData.message}
                </p>
                {ocrData.existing_client && (
                  <div className="text-sm text-gris-texto mb-4">
                    <span className="text-gris-secundario">Cliente:</span> {ocrData.existing_client.nombre || 'Sin nombre'}
                  </div>
                )}
                <div className="flex gap-3">
                  <Link href={`/wizard/${ocrData.existing_id}/step-2-validar`}>
                    <button className="px-4 py-2 bg-azul-control text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
                      Ir a validar
                    </button>
                  </Link>
                  <button 
                    onClick={() => window.location.href = '/dashboard'}
                    className="px-4 py-2 border border-gris-secundario text-gris-texto rounded-lg hover:bg-white/5 transition text-sm font-medium"
                  >
                    Volver al dashboard
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="card border-rojo-error bg-rojo-error/5">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <p className="text-rojo-error font-medium">
                  No pudimos leer la factura
                </p>
                <p className="text-sm text-gris-secundario mt-1">
                  Complétala manualmente en el siguiente paso
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </WizardLayout>
  );
}

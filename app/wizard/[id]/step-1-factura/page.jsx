"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import WizardLayout from '@/app/components/wizard/WizardLayout';

export default function Step1FacturaPage({ params }) {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [ocrData, setOcrData] = useState(null);
  const [error, setError] = useState(null);

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

    // TODO: Implement actual upload and OCR
    // Simulación temporal
    setTimeout(() => {
      setOcrData({
        cups: 'ES0123456789012345AB',
        total: '124.50',
        cliente: 'Juan López Martínez'
      });
      setUploading(false);
      // BUGFIX: Automatic redirection after success to maintain flow
      setTimeout(() => {
        router.push(`/wizard/${params.id}/step-2-validar`);
      }, 1500);
    }, 2000);
  };

  const handleNext = () => {
    // TODO: Navigate to step 2
    router.push(`/wizard/${params.id}/step-2-validar`);
  };

  return (
    <WizardLayout
      currentStep={1}
      nextLabel="SIGUIENTE"
      nextDisabled={!ocrData}
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
            className="border-2 border-dashed border-gris-secundario rounded-xl p-12 text-center bg-gris-fondo hover:border-azul-control hover:bg-azul-control/5 transition cursor-pointer"
            onClick={() => document.getElementById('file-input').click()}
          >
            <div className="text-6xl mb-4">📄</div>
            <p className="text-lg text-gris-texto mb-2">
              Arrastra la factura aquí
            </p>
            <p className="text-sm text-gris-secundario mb-4">
              o haz clic para seleccionar
            </p>
            <p className="text-xs text-gris-secundario">
              PDF, JPG, PNG · Máx 10MB
            </p>
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
                    <span className="text-gris-secundario">• CUPS:</span> {ocrData.cups}
                  </div>
                  <div>
                    <span className="text-gris-secundario">• Total:</span> {ocrData.total}€
                  </div>
                  <div>
                    <span className="text-gris-secundario">• Cliente:</span> {ocrData.cliente}
                  </div>
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

"use client";

import { useState } from 'react';
import Button from '@/app/components/Button';

export default function ComisionesPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setResult(null);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/webhook/comisiones/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Error al subir archivo');
      }
      
      const data = await res.json();
      setResult(data);
      setFile(null); // Limpiar input
      
    } catch (err) {
      setResult({
        status: 'error',
        error: err.message
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Card de upload */}
      <div className="card">
        <h3 className="text-lg font-bold text-white mb-4">📤 Subir comisiones (CSV/Excel)</h3>
        <p className="text-sm text-[#94A3B8] mb-4">
          Formato esperado: <code className="text-[#0073EC]">tarifa_id, comision_eur, vigente_desde, vigente_hasta</code>
        </p>
        
        <div className="space-y-4">
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-sm text-[#94A3B8]
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-semibold
              file:bg-[#1E3A8A] file:text-white
              hover:file:bg-blue-600
              file:cursor-pointer cursor-pointer"
          />
          
          <Button
            onClick={handleUpload}
            disabled={!file || uploading}
            variant="primary"
          >
            {uploading ? 'Subiendo...' : 'Cargar archivo'}
          </Button>
        </div>

        {/* Resultado */}
        {result && (
          <div className={`mt-4 p-4 rounded-lg border ${
            result.status === 'ok' 
              ? 'bg-green-500/10 border-green-500/30 text-green-400' 
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {result.status === 'ok' ? (
              <>
                <p className="font-semibold">✅ Importadas {result.importados} comisiones</p>
                {result.errores && result.errores.length > 0 && (
                  <details className="mt-2 text-xs">
                    <summary className="cursor-pointer">Ver errores ({result.errores.length})</summary>
                    <ul className="mt-2 space-y-1">
                      {result.errores.map((err, i) => (
                        <li key={i}>Fila {err.fila}: {err.motivo}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </>
            ) : (
              <p>❌ Error: {result.error || result.detail}</p>
            )}
          </div>
        )}
      </div>

      {/* Formato ejemplo */}
      <div className="card">
        <h3 className="text-lg font-bold text-white mb-4">📋 Ejemplo de formato</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-[#94A3B8]">
                <th className="text-left py-2 px-3">tarifa_id</th>
                <th className="text-left py-2 px-3">comision_eur</th>
                <th className="text-left py-2 px-3">vigente_desde</th>
                <th className="text-left py-2 px-3">vigente_hasta</th>
              </tr>
            </thead>
            <tbody className="text-[#F1F5F9]">
              <tr className="border-b border-white/5">
                <td className="py-2 px-3">45</td>
                <td className="py-2 px-3">15.00</td>
                <td className="py-2 px-3">2026-01-01</td>
                <td className="py-2 px-3">2026-12-31</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 px-3">46</td>
                <td className="py-2 px-3">18.50</td>
                <td className="py-2 px-3">2026-02-01</td>
                <td className="py-2 px-3"></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-xs text-[#94A3B8] mt-4">
          💡 <strong>vigente_hasta</strong> es opcional. Si se omite, la comisión queda abierta.
        </p>
      </div>
    </div>
  );
}

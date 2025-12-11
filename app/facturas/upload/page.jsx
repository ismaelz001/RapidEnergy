"use client";

import { useState } from "react";
import { uploadFactura } from "@/lib/apiClient";

export default function UploadFacturaPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Selecciona un fichero primero.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await uploadFactura(file);
      setResult(res);
    } catch (err) {
      console.error(err);
      setError("Error subiendo la factura.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="card">
        <h1 className="mb-2 text-xl font-semibold">Subir factura</h1>
        <p className="mb-4 text-xs text-slate-300">
          Esta pantalla envía el archivo al backend FastAPI (endpoint /webhook/upload) y
          muestra el JSON parseado (CUPS, consumo, importe, etc.).
        </p>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="label">Factura (PDF / imagen)</label>
            <input
              type="file"
              className="block w-full text-xs text-slate-200"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? "Procesando..." : "Subir y procesar"}
          </button>
          {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="mb-2 text-sm font-semibold">Resultado parseado</h2>
          <pre className="whitespace-pre-wrap break-all text-xs bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

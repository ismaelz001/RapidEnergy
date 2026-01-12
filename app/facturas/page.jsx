"use client";

import { useEffect, useState } from "react";
import { listFacturas, deleteFactura } from "@/lib/apiClient";
import Link from "next/link";
import Button from "../components/Button";

export default function FacturasPage() {
  const [facturas, setFacturas] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchFacturas = async () => {
    setLoading(true);
    const data = await listFacturas();
    setFacturas(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchFacturas();
  }, []);

  const handleDelete = async (id) => {
    const hasClient = facturas.find(f => f.id === id)?.cliente_id;
    const hasCups = facturas.find(f => f.id === id)?.cups;

    let confirmMsg = "¿Estás seguro de que deseas eliminar esta factura?";
    if (hasClient && hasCups) {
       confirmMsg = "ATENCIÓN: Esta factura es VÁLIDA y está enlazada a un cliente. La eliminación está restringida en el servidor si no hay errores.";
    }

    if (!confirm(confirmMsg)) return;

    try {
      await deleteFactura(id);
      alert("Factura eliminada correctamente");
      fetchFacturas();
    } catch (e) {
      alert(`No se pudo eliminar: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Facturas procesadas</h1>
          <p className="text-sm text-slate-400 mt-1">
            Gestión de documentos OCR y estados de comparación.
          </p>
        </div>
        <Link href="/wizard/new/step-1-factura">
          <Button variant="primary">+ Nueva Factura</Button>
        </Link>
      </div>

      <div className="card overflow-hidden p-0 border-white/5 bg-[#131C31]/50 backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#020617]/50 text-[#94A3B8] uppercase text-[10px] font-bold tracking-wider border-b border-white/5">
              <tr>
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">CUPS</th>
                <th className="px-6 py-4">Cliente</th>
                <th className="px-6 py-4 text-center">Importe</th>
                <th className="px-6 py-4">Fecha</th>
                <th className="px-6 py-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-blue"></div>
                  </td>
                </tr>
              ) : facturas && facturas.length > 0 ? (
                facturas.map((f) => (
                  <tr key={f.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4 font-mono text-xs text-slate-500">#{f.id}</td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-white">{f.cups || "---"}</span>
                    </td>
                    <td className="px-6 py-4">
                       {f.cliente?.nombre ? (
                         <span className="text-emerald-400 font-medium">{f.cliente.nombre}</span>
                       ) : (
                         <span className="text-slate-500">Sin asignar</span>
                       )}
                    </td>
                    <td className="px-6 py-4 text-center font-bold text-white">
                      {f.total_factura ? `${f.total_factura.toFixed(2)}€` : (f.importe ? `${f.importe.toFixed(2)}€` : "-")}
                    </td>
                    <td className="px-6 py-4 text-slate-400">{f.fecha || "---"}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-center gap-3">
                        <Link 
                          href={`/wizard/${f.id}/${f.estado_factura === 'pendiente_datos' ? 'step-2-validar' : 'step-3-comparar'}`}
                          className="text-xs font-bold text-primary-blue hover:underline"
                        >
                          Gestionar
                        </Link>
                        <button 
                          onClick={() => handleDelete(f.id)}
                          className="p-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                          title="Eliminar factura"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-20 text-center">
                    <div className="text-4xl mb-4 opacity-20">📂</div>
                    <p className="text-[#94A3B8]">No hay facturas procesadas todavía.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

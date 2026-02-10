"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const ESTADOS_LABELS = {
  lead: "Lead",
  contactado: "Contactado",
  en_estudio: "En Estudio",
  propuesta_enviada: "Propuesta Enviada",
  negociacion: "Negociación",
  contrato_enviado: "Contrato Enviado",
  pendiente_firma: "Pendiente Firma",
  firmado: "Firmado",
  validado: "Validado",
  activo: "✅ Activo",
  baja: "Baja",
  cancelado: "Cancelado",
  perdido: "Perdido",
};

const ESTADOS_COLORS = {
  lead: "bg-gray-500",
  contactado: "bg-blue-500",
  en_estudio: "bg-yellow-500",
  propuesta_enviada: "bg-purple-500",
  negociacion: "bg-orange-500",
  contrato_enviado: "bg-indigo-500",
  pendiente_firma: "bg-pink-500",
  firmado: "bg-cyan-500",
  validado: "bg-teal-500",
  activo: "bg-green-500",
  baja: "bg-gray-600",
  cancelado: "bg-red-500",
  perdido: "bg-red-700",
};

export default function CasosPage() {
  const router = useRouter();
  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState("");

  useEffect(() => {
    fetchCasos();
  }, [filtroEstado]);

  const fetchCasos = async () => {
    try {
      setLoading(true);
      const url = filtroEstado 
        ? `${API_BASE}/api/casos?estado=${filtroEstado}`
        : `${API_BASE}/api/casos`;
      const res = await fetch(url);
      const data = await res.json();
      setCasos(data);
    } catch (error) {
      console.error("Error fetching casos:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatFecha = (fecha) => {
    if (!fecha) return "-";
    return new Date(fecha).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Casos CRM</h1>
          <p className="text-sm text-[#94A3B8] mt-1">
            Gestión de pipeline comercial
          </p>
        </div>
        <button
          onClick={() => router.push('/gestion/casos/nuevo')}
          className="px-4 py-2 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white rounded-lg font-semibold transition-colors"
        >
          + Nuevo Caso
        </button>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-4">
        <select
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value)}
          className="px-4 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm"
        >
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        
        <span className="text-sm text-[#94A3B8]">
          {casos.length} caso{casos.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Tabla */}
      {loading ? (
        <div className="text-center py-12 text-[#94A3B8]">Cargando casos...</div>
      ) : casos.length === 0 ? (
        <div className="text-center py-12 text-[#94A3B8]">
          No hay casos. <button onClick={() => router.push('/gestion/casos/nuevo')} className="text-blue-400 hover:underline">Crear el primero</button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-[rgba(255,255,255,0.08)]">
          <table className="w-full">
            <thead className="bg-[rgba(255,255,255,0.02)] border-b border-[rgba(255,255,255,0.08)]">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">CUPS</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Asesor</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Comercializadora</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Ahorro Anual</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#94A3B8] uppercase">Creado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(255,255,255,0.05)]">
              {casos.map((caso) => (
                <tr 
                  key={caso.id}
                  className="hover:bg-[rgba(255,255,255,0.02)] transition-colors cursor-pointer"
                  onClick={() => router.push(`/gestion/casos/${caso.id}`)}
                >
                  <td className="px-4 py-3 text-sm text-white font-mono">#{caso.id}</td>
                  <td className="px-4 py-3 text-sm text-white font-medium">
                    {caso.cliente?.nombre || "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-[#94A3B8] font-mono">
                    {caso.cups ? caso.cups.substring(0, 16) + "..." : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full text-white ${ESTADOS_COLORS[caso.estado_comercial]}`}>
                      {ESTADOS_LABELS[caso.estado_comercial]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-[#94A3B8]">
                    {caso.asesor?.nombre || "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-[#94A3B8]">
                    {caso.nueva_compania_text || "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-white font-semibold">
                    {caso.ahorro_estimado_anual ? `${caso.ahorro_estimado_anual}€` : "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-[#94A3B8]">
                    {formatFecha(caso.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/gestion/casos/${caso.id}`);
                      }}
                      className="text-blue-400 hover:text-blue-300 text-sm font-semibold"
                    >
                      Ver →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

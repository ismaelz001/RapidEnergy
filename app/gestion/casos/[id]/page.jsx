"use client";

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TRANSICIONES = {
  lead: ["contactado", "perdido", "cancelado"],
  contactado: ["en_estudio", "perdido", "cancelado"],
  en_estudio: ["propuesta_enviada", "perdido", "cancelado"],
  propuesta_enviada: ["negociacion", "contrato_enviado", "perdido", "cancelado"],
  negociacion: ["contrato_enviado", "propuesta_enviada", "perdido", "cancelado"],
  contrato_enviado: ["pendiente_firma", "cancelado"],
  pendiente_firma: ["firmado", "cancelado"],
  firmado: ["validado", "cancelado"],
  validado: ["activo", "cancelado"],
  activo: ["baja"],
  baja: [],
  cancelado: [],
  perdido: [],
};

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
  activo: "Activo",
  baja: "Baja",
  cancelado: "Cancelado",
  perdido: "Perdido",
};

export default function CasoDetallePage() {
  const params = useParams();
  const router = useRouter();
  const [caso, setCaso] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cambiandoEstado, setCambiandoEstado] = useState(false);
  const [estadoNuevo, setEstadoNuevo] = useState("");
  const [notasCambio, setNotasCambio] = useState("");
  const [editandoCliente, setEditandoCliente] = useState(false);
  const [clienteEditado, setClienteEditado] = useState({});

  useEffect(() => {
    fetchCaso();
  }, [params.id]);

  const fetchCaso = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/casos/${params.id}`);
      const data = await res.json();
      setCaso(data);
    } catch (error) {
      console.error("Error fetching caso:", error);
    } finally {
      setLoading(false);
    }
  };

  const cambiarEstado = async () => {
    if (!estadoNuevo) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/casos/${params.id}/cambiar-estado`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          estado_nuevo: estadoNuevo,
          notas: notasCambio
        })
      });
      
      if (res.ok) {
        setCambiandoEstado(false);
        setEstadoNuevo("");
        setNotasCambio("");
        fetchCaso();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error cambiando estado:", error);
      alert("Error al cambiar estado");
    }
  };

  const guardarCliente = async () => {
    if (!caso.cliente?.id) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/clientes/${caso.cliente.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(clienteEditado)
      });
      
      if (res.ok) {
        setEditandoCliente(false);
        fetchCaso();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Error al actualizar cliente'}`);
      }
    } catch (error) {
      console.error("Error actualizando cliente:", error);
      alert("Error al actualizar cliente");
    }
  };

  const abrirEdicionCliente = () => {
    setClienteEditado({
      nombre: caso.cliente?.nombre || "",
      email: caso.cliente?.email || "",
      telefono: caso.cliente?.telefono || "",
      dni: caso.cliente?.dni || "",
      cups: caso.cups || "",
      direccion: caso.cliente?.direccion || "",
      provincia: caso.cliente?.provincia || ""
    });
    setEditandoCliente(true);
  };

  const formatFecha = (fecha) => {
    if (!fecha) return "-";
    return new Date(fecha).toLocaleString("es-ES");
  };

  if (loading) {
    return <div className="text-center py-12 text-[#94A3B8]">Cargando caso...</div>;
  }

  if (!caso) {
    return <div className="text-center py-12 text-red-400">Caso no encontrado</div>;
  }

  const transicionesPosibles = TRANSICIONES[caso.estado_comercial] || [];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/gestion/casos')}
            className="text-[#94A3B8] hover:text-white transition-colors"
          >
            ← Volver
          </button>
          <h1 className="text-3xl font-bold text-white">Caso #{caso.id}</h1>
        </div>
        
        {transicionesPosibles.length > 0 && (
          <button
            onClick={() => setCambiandoEstado(true)}
            className="px-4 py-2 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white rounded-lg font-semibold transition-colors"
          >
            Cambiar Estado
          </button>
        )}
      </div>

      {/* Grid de información */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna principal */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Datos del cliente */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Cliente</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-[#94A3B8]">Nombre:</span>
                <p className="text-white font-medium">{caso.cliente?.nombre || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Email:</span>
                <p className="text-white">{caso.cliente?.email || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Teléfono:</span>
                <p className="text-white">{caso.cliente?.telefono || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">CUPS:</span>
                <p className="text-white font-mono text-xs">{caso.cups || "-"}</p>
              </div>
            </div>
          </div>

          {/* Datos del caso */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Detalles del Contrato</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-[#94A3B8]">Servicio:</span>
                <p className="text-white">{caso.servicio}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Canal:</span>
                <p className="text-white">{caso.canal || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Nueva Comercializadora:</span>
                <p className="text-white font-medium">{caso.nueva_compania_text || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Antigua Comercializadora:</span>
                <p className="text-white">{caso.antigua_compania_text || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Tarifa:</span>
                <p className="text-white">{caso.tarifa_nombre_text || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Ahorro Estimado Anual:</span>
                <p className="text-white font-semibold text-lg">{caso.ahorro_estimado_anual ? `${caso.ahorro_estimado_anual}€` : "-"}</p>
              </div>
            </div>
          </div>

          {/* Notas */}
          {caso.notas && (
            <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Notas</h2>
              <p className="text-[#94A3B8] text-sm whitespace-pre-wrap">{caso.notas}</p>
            </div>
          )}

          {/* Historial */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Historial</h2>
            {caso.historial && caso.historial.length > 0 ? (
              <div className="space-y-3">
                {caso.historial.map((evento, idx) => (
                  <div key={idx} className="flex gap-4 pb-3 border-b border-[rgba(255,255,255,0.05)] last:border-0">
                    <div className="flex-shrink-0 text-xs text-[#94A3B8]">
                      {formatFecha(evento.created_at)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-white">{evento.descripcion}</p>
                      {evento.estado_anterior && evento.estado_nuevo && (
                        <p className="text-xs text-[#94A3B8] mt-1">
                          {ESTADOS_LABELS[evento.estado_anterior]} → {ESTADOS_LABELS[evento.estado_nuevo]}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[#94A3B8]">Sin historial</p>
            )}
          </div>
        </div>

        {/* Columna lateral */}
        <div className="flex flex-col gap-6">
          {/* Estado actual */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Estado Actual</h2>
            <div className="text-center">
              <span className="inline-block px-4 py-2 text-lg font-semibold rounded-lg text-white bg-[#1E3A8A]">
                {ESTADOS_LABELS[caso.estado_comercial]}
              </span>
            </div>
          </div>

          {/* Asignación */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Asignación</h2>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-[#94A3B8]">Asesor:</span>
                <p className="text-white font-medium">{caso.asesor?.nombre || "-"}</p>
              </div>
              <div>
                <span className="text-[#94A3B8]">Colaborador:</span>
                <p className="text-white">{caso.colaborador?.nombre || "-"}</p>
              </div>
            </div>
          </div>

          {/* Fechas */}
          <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Fechas</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#94A3B8]">Contacto:</span>
                <span className="text-white">{formatFecha(caso.fecha_contacto)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#94A3B8]">Propuesta:</span>
                <span className="text-white">{formatFecha(caso.fecha_propuesta)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#94A3B8]">Firma:</span>
                <span className="text-white">{formatFecha(caso.fecha_firma)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#94A3B8]">Activación:</span>
                <span className="text-white">{formatFecha(caso.fecha_activacion)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#94A3B8]">Baja:</span>
                <span className="text-white">{formatFecha(caso.fecha_baja)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal cambiar estado */}
      {cambiandoEstado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setCambiandoEstado(false)}>
          <div className="bg-[#0F172A] border border-[rgba(255,255,255,0.1)] rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-semibold text-white mb-4">Cambiar Estado</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Estado Actual</label>
                <div className="px-3 py-2 bg-[rgba(255,255,255,0.05)] rounded-lg text-white">
                  {ESTADOS_LABELS[caso.estado_comercial]}
                </div> [&>option]:bg-slate-800 [&>option]:text-white
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Nuevo Estado</label>
                <select
                  value={estadoNuevo}
                  onChange={(e) => setEstadoNuevo(e.target.value)}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                >
                  <option value="">Seleccionar...</option>
                  {transicionesPosibles.map((estado) => (
                    <option key={estado} value={estado}>
                      {ESTADOS_LABELS[estado]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Notas (opcional)</label>
                <textarea
                  value={notasCambio}
                  onChange={(e) => setNotasCambio(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm"
                  placeholder="Motivo del cambio..."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setCambiandoEstado(false);
                    setEstadoNuevo("");
                    setNotasCambio("");
                  }}
                  className="flex-1 px-4 py-2 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-white rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={cambiarEstado}
                  disabled={!estadoNuevo}
                  className="flex-1 px-4 py-2 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Confirmar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal editar cliente */}
      {editandoCliente && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEditandoCliente(false)}>
          <div className="bg-[#0F172A] border border-[rgba(255,255,255,0.1)] rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-semibold text-white mb-4">Editar Cliente</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Nombre *</label>
                <input
                  type="text"
                  value={clienteEditado.nombre}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, nombre: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">DNI/NIF *</label>
                <input
                  type="text"
                  value={clienteEditado.dni}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, dni: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Email</label>
                <input
                  type="email"
                  value={clienteEditado.email}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, email: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Teléfono</label>
                <input
                  type="text"
                  value={clienteEditado.telefono}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, telefono: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm text-[#94A3B8] mb-2">CUPS</label>
                <input
                  type="text"
                  value={clienteEditado.cups}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, cups: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Dirección</label>
                <input
                  type="text"
                  value={clienteEditado.direccion}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, direccion: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm text-[#94A3B8] mb-2">Provincia</label>
                <input
                  type="text"
                  value={clienteEditado.provincia}
                  onChange={(e) => setClienteEditado({ ...clienteEditado, provincia: e.target.value })}
                  className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setEditandoCliente(false)}
                className="flex-1 px-4 py-2 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={guardarCliente}
                disabled={!clienteEditado.nombre || !clienteEditado.dni}
                className="flex-1 px-4 py-2 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

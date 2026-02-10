"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NuevoCasoPage() {
  const router = useRouter();
  const [clientes, setClientes] = useState([]);
  const [asesores, setAsesores] = useState([]);
  const [colaboradores, setColaboradores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [guardando, setGuardando] = useState(false);

  const [formData, setFormData] = useState({
    cliente_id: "",
    asesor_id: "",
    colaborador_id: "",
    servicio: "contrato_luz_gas",
    cups: "",
    nueva_compania_text: "",
    antigua_compania_text: "",
    tarifa_nombre_text: "",
    ahorro_estimado_anual: "",
    canal: "presencial",
    notas: "",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [resClientes, resColabs] = await Promise.all([
        fetch(`${API_BASE}/api/clientes`),
        fetch(`${API_BASE}/api/colaboradores`)
      ]);
      
      const dataClientes = await resClientes.json();
      const dataColabs = await resColabs.json();
      
      setClientes(dataClientes);
      setColaboradores(dataColabs);
      setAsesores(dataColabs.filter(c => c.rol === "asesor" || c.rol === "gestor" || c.rol === "ceo"));
    } catch (error) {
      console.error("Error cargando datos:", error);
      alert("Error cargando clientes/colaboradores");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cliente_id || !formData.asesor_id) {
      alert("Cliente y Asesor son obligatorios");
      return;
    }

    const payload = {
      ...formData,
      cliente_id: parseInt(formData.cliente_id),
      asesor_id: parseInt(formData.asesor_id),
      colaborador_id: formData.colaborador_id ? parseInt(formData.colaborador_id) : null,
      ahorro_estimado_anual: formData.ahorro_estimado_anual ? parseFloat(formData.ahorro_estimado_anual) : null,
    };

    try {
      setGuardando(true);
      const res = await fetch(`${API_BASE}/api/casos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const caso = await res.json();
        router.push(`/gestion/casos/${caso.id}`);
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Error desconocido'}`);
      }
    } catch (error) {
      console.error("Error creando caso:", error);
      alert("Error al crear el caso");
    } finally {
      setGuardando(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-[#94A3B8]">Cargando...</div>;
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push('/gestion/casos')}
          className="text-[#94A3B8] hover:text-white transition-colors"
        >
          ← Volver
        </button>
        <h1 className="text-3xl font-bold text-white">Nuevo Caso</h1>
      </div>

      {/* Formulario */}
      <form onSubmit={handleSubmit} className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cliente */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Cliente *
            </label>
            <select
              required
              value={formData.cliente_id}
              onChange={(e) => setFormData({ ...formData, cliente_id: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="">Seleccionar cliente...</option>
              {clientes.map(c => (
                <option key={c.id} value={c.id}>
                  {c.nombre} - {c.email}
                </option>
              ))}
            </select>
          </div>

          {/* Asesor */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Asesor *
            </label>
            <select
              required
              value={formData.asesor_id}
              onChange={(e) => setFormData({ ...formData, asesor_id: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="">Seleccionar asesor...</option>
              {asesores.map(a => (
                <option key={a.id} value={a.id}>
                  {a.nombre} ({a.rol})
                </option>
              ))}
            </select>
          </div>

          {/* Colaborador */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Colaborador (opcional)
            </label>
            <select
              value={formData.colaborador_id}
              onChange={(e) => setFormData({ ...formData, colaborador_id: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="">Sin colaborador</option>
              {colaboradores.filter(c => c.rol === "colaborador").map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>

          {/* Servicio */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Servicio
            </label>
            <select
              value={formData.servicio}
              onChange={(e) => setFormData({ ...formData, servicio: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="contrato_luz">Solo Luz</option>
              <option value="contrato_gas">Solo Gas</option>
              <option value="contrato_luz_gas">Luz + Gas</option>
              <option value="instalacion_solar">Instalación Solar</option>
            </select>
          </div>

          {/* CUPS */}
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              CUPS
            </label>
            <input
              type="text"
              value={formData.cups}
              onChange={(e) => setFormData({ ...formData, cups: e.target.value })}
              placeholder="ES0031406483279001LZ0F"
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white font-mono text-sm"
            />
          </div>

          {/* Nueva Comercializadora */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Nueva Comercializadora
            </label>
            <input
              type="text"
              value={formData.nueva_compania_text}
              onChange={(e) => setFormData({ ...formData, nueva_compania_text: e.target.value })}
              placeholder="TotalEnergies"
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            />
          </div>

          {/* Antigua Comercializadora */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Antigua Comercializadora
            </label>
            <input
              type="text"
              value={formData.antigua_compania_text}
              onChange={(e) => setFormData({ ...formData, antigua_compania_text: e.target.value })}
              placeholder="Endesa"
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            />
          </div>

          {/* Tarifa */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Tarifa
            </label>
            <input
              type="text"
              value={formData.tarifa_nombre_text}
              onChange={(e) => setFormData({ ...formData, tarifa_nombre_text: e.target.value })}
              placeholder="2.0TD"
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            />
          </div>

          {/* Ahorro Anual */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Ahorro Estimado Anual (€)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.ahorro_estimado_anual}
              onChange={(e) => setFormData({ ...formData, ahorro_estimado_anual: e.target.value })}
              placeholder="450.00"
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            />
          </div>

          {/* Canal */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Canal
            </label>
            <select
              value={formData.canal}
              onChange={(e) => setFormData({ ...formData, canal: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="presencial">Presencial</option>
              <option value="telefono">Teléfono</option>
              <option value="web">Web</option>
              <option value="email">Email</option>
              <option value="redes_sociales">Redes Sociales</option>
            </select>
          </div>

          {/* Notas */}
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Notas
            </label>
            <textarea
              value={formData.notas}
              onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
              rows={4}
              placeholder="Información adicional sobre el caso..."
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm"
            />
          </div>
        </div>

        {/* Botones */}
        <div className="flex gap-4 mt-6 pt-6 border-t border-[rgba(255,255,255,0.1)]">
          <button
            type="button"
            onClick={() => router.push('/gestion/casos')}
            className="px-6 py-2 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-white rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={guardando}
            className="px-6 py-2 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {guardando ? "Guardando..." : "Crear Caso"}
          </button>
        </div>
      </form>
    </div>
  );
}

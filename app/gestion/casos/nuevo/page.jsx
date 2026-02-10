"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NuevoCasoPage() {
  const router = useRouter();
  const [clientes, setClientes] = useState([]);
  const [colaboradores, setColaboradores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [guardando, setGuardando] = useState(false);

  const [formData, setFormData] = useState({
    cliente_id: "",
    colaborador_id: "",
    servicio: "contrato_luz",
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
      // Cargar clientes
      const resClientes = await fetch(`${API_BASE}/api/clientes`);
      if (resClientes.ok) {
        const dataClientes = await resClientes.json();
        console.log("✅ Clientes cargados:", dataClientes.length);
        setClientes(Array.isArray(dataClientes) ? dataClientes : []);
      } else {
        console.error("❌ Error clientes:", resClientes.status);
        setClientes([]);
      }

      // Cargar colaboradores (users)
      const resUsers = await fetch(`${API_BASE}/api/users`);
      if (resUsers.ok) {
        const dataUsers = await resUsers.json();
        console.log("✅ Users cargados:", dataUsers.length);
        
        // Mapear name→nombre, role→rol para compatibilidad
        const mappedUsers = Array.isArray(dataUsers) 
          ? dataUsers.map(u => ({
              id: u.id,
              nombre: u.name || u.nombre || "Sin nombre",
              rol: u.role || u.rol || "unknown",
              email: u.email
            }))
          : [];
        
        console.log("✅ Colaboradores mapeados:", mappedUsers);
        setColaboradores(mappedUsers);
      } else {
        console.error("❌ Error users:", resUsers.status);
        setColaboradores([]);
      }
    } catch (error) {
      console.error("❌ Error general:", error);
      setClientes([]);
      setColaboradores([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cliente_id || !formData.colaborador_id) {
      alert("Cliente y Colaborador son obligatorios");
      return;
    }

    const payload = {
      cliente_id: parseInt(formData.cliente_id),
      asesor_user_id: parseInt(formData.colaborador_id),
      servicio: formData.servicio,
      cups: formData.cups || null,
      nueva_compania_text: formData.nueva_compania_text || null,
      antigua_compania_text: formData.antigua_compania_text || null,
      tarifa_nombre_text: formData.tarifa_nombre_text || null,
      ahorro_estimado_anual: formData.ahorro_estimado_anual ? parseFloat(formData.ahorro_estimado_anual) : null,
      canal: formData.canal || null,
      notas: formData.notas || null,
    };

    console.log("📤 Enviando:", payload);

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

  // Force client-side render
  const renderClienteOptions = () => {
    if (!clientes || clientes.length === 0) {
      return <option value="" disabled>No hay clientes disponibles</option>;
    }
    return clientes.map((cliente) => (
      <option key={`cliente-${cliente.id}`} value={cliente.id}>
        {cliente.nombre || 'Sin nombre'}
      </option>
    ));
  };

  const renderColaboradorOptions = () => {
    if (!colaboradores || colaboradores.length === 0) {
      return <option value="" disabled>No hay colaboradores disponibles</option>;
    }
    return colaboradores.map((colab) => (
      <option key={`colab-${colab.id}`} value={colab.id}>
        {colab.nombre || 'Sin nombre'} - {colab.rol || 'sin rol'}
      </option>
    ));
  };

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
              <option value="">-- Seleccionar cliente --</option>
              {renderClienteOptions()}
            </select>
          </div>

          {/* Colaborador */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Colaborador/Asesor *
            </label>
            <select
              required
              value={formData.colaborador_id}
              onChange={(e) => setFormData({ ...formData, colaborador_id: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="">-- Seleccionar colaborador --</option>
              {renderColaboradorOptions()}
            </select>
          </div>

          {/* Servicio */}
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Servicio *
            </label>
            <select
              required
              value={formData.servicio}
              onChange={(e) => setFormData({ ...formData, servicio: e.target.value })}
              className="w-full px-3 py-2 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white"
            >
              <option value="contrato_luz">⚡ Solo Luz</option>
              <option value="contrato_gas">🔥 Solo Gas</option>
              <option value="contrato_luz_gas">⚡🔥 Luz + Gas</option>
              <option value="instalacion_solar">☀️ Instalación Solar</option>
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

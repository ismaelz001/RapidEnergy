"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function NuevoClientePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    nombre: "",
    dni: "",
    email: "",
    telefono: "",
    cups: "",
    direccion: "",
    provincia: "",
    estado: "lead"
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/clientes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Error al crear cliente");
      }

      const nuevoCliente = await res.json();
      router.push(`/clientes/${nuevoCliente.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="text-xs uppercase tracking-wide text-emerald-400">CRM</p>
        <h1 className="text-2xl font-semibold">Nuevo Cliente</h1>
        <p className="text-xs text-slate-400">
          Crear un cliente manualmente sin subir factura
        </p>
      </div>

      <div className="bg-[#0F172A] rounded-[16px] p-6 max-w-2xl">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs text-slate-400 mb-1">
                Nombre completo <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="nombre"
                required
                value={formData.nombre}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                DNI/CIF <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="dni"
                required
                value={formData.dni}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Teléfono</label>
              <input
                type="tel"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">CUPS</label>
              <input
                type="text"
                name="cups"
                value={formData.cups}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Dirección</label>
              <input
                type="text"
                name="direccion"
                value={formData.direccion}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Provincia</label>
              <input
                type="text"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Estado inicial</label>
              <select
                name="estado"
                value={formData.estado}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded bg-[#1E293B] border border-white/10 text-sm text-[#F1F5F9]"
              >
                <option value="lead">Lead</option>
                <option value="seguimiento">Seguimiento</option>
                <option value="oferta_enviada">Oferta enviada</option>
                <option value="contratado">Contratado</option>
              </select>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-2 rounded text-xs">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 rounded bg-[#1E293B] text-sm hover:bg-[#334155] transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded bg-emerald-500 text-white text-sm hover:bg-emerald-600 transition-colors disabled:opacity-50"
            >
              {loading ? "Creando..." : "Crear cliente"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

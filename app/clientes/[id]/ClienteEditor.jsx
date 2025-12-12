"use client";

import { useState } from "react";
import { updateCliente } from "@/lib/apiClient";

export default function ClienteEditor({ cliente, onUpdated }) {
  const [formData, setFormData] = useState({
    nombre: cliente?.nombre || "",
    email: cliente?.email || "",
    telefono: cliente?.telefono || "",
    direccion: cliente?.direccion || "",
    provincia: cliente?.provincia || "",
    estado: cliente?.estado || "lead",
  });
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("saving");
    setMessage("");
    try {
      const updated = await updateCliente(cliente.id, formData);
      if (onUpdated) {
        onUpdated(updated);
      }
      setStatus("saved");
      setMessage("Cliente actualizado correctamente");
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("No se pudo actualizar. Revisa el backend.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label" htmlFor="nombre">
          Nombre
        </label>
        <input
          id="nombre"
          name="nombre"
          className="input"
          value={formData.nombre}
          onChange={handleChange}
          placeholder="Nombre del cliente"
        />
      </div>
      <div>
        <label className="label" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          name="email"
          className="input"
          type="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="correo@cliente.com"
        />
      </div>
      <div>
        <label className="label" htmlFor="telefono">
          Telefono
        </label>
        <input
          id="telefono"
          name="telefono"
          className="input"
          value={formData.telefono}
          onChange={handleChange}
          placeholder="612345678"
        />
      </div>
      <div>
        <label className="label" htmlFor="direccion">
          Direccion
        </label>
        <input
          id="direccion"
          name="direccion"
          className="input"
          value={formData.direccion}
          onChange={handleChange}
          placeholder="Calle y numero"
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="provincia">
            Provincia
          </label>
          <input
            id="provincia"
            name="provincia"
            className="input"
            value={formData.provincia}
            onChange={handleChange}
            placeholder="Provincia"
          />
        </div>
        <div>
          <label className="label" htmlFor="estado">
            Estado
          </label>
          <select
        id="estado"
        name="estado"
        className="input"
        value={formData.estado || "lead"}
        onChange={handleChange}
      >
        <option value="lead">Lead</option>
        <option value="seguimiento">Seguimiento</option>
        <option value="oferta_enviada">Oferta enviada</option>
        <option value="contratado">Contratado</option>
        <option value="descartado">Descartado</option>
      </select>
    </div>
  </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          className="btn-primary"
          disabled={status === "saving"}
        >
          {status === "saving" ? "Guardando..." : "Guardar cambios"}
        </button>
        {message && (
          <span
            className={`text-xs ${
              status === "error" ? "text-red-400" : "text-emerald-400"
            }`}
          >
            {message}
          </span>
        )}
      </div>
    </form>
  );
}

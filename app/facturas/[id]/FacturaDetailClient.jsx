"use client";

import { useState, useMemo } from "react";
import { updateFactura } from "@/lib/apiClient";

const numberFields = [
  "potencia_p1_kw",
  "potencia_p2_kw",
  "consumo_p1_kwh",
  "consumo_p2_kwh",
  "consumo_p3_kwh",
  "consumo_p4_kwh",
  "consumo_p5_kwh",
  "consumo_p6_kwh",
  "alquiler_contador",
  "impuesto_electrico",
  "iva",
  "total_factura",
];

const requiredFields = [
  "potencia_p1_kw",
  "potencia_p2_kw",
  "consumo_p1_kwh",
  "consumo_p2_kwh",
  "consumo_p3_kwh",
  "consumo_p4_kwh",
  "consumo_p5_kwh",
  "consumo_p6_kwh",
  "alquiler_contador",
  "impuesto_electrico",
  "iva",
  "total_factura",
];

export default function FacturaDetailClient({ factura }) {
  const [form, setForm] = useState({
    potencia_p1_kw: factura.potencia_p1_kw ?? "",
    potencia_p2_kw: factura.potencia_p2_kw ?? "",
    consumo_p1_kwh: factura.consumo_p1_kwh ?? "",
    consumo_p2_kwh: factura.consumo_p2_kwh ?? "",
    consumo_p3_kwh: factura.consumo_p3_kwh ?? "",
    consumo_p4_kwh: factura.consumo_p4_kwh ?? "",
    consumo_p5_kwh: factura.consumo_p5_kwh ?? "",
    consumo_p6_kwh: factura.consumo_p6_kwh ?? "",
    bono_social: factura.bono_social ?? false,
    servicios_vinculados: factura.servicios_vinculados ?? false,
    alquiler_contador: factura.alquiler_contador ?? "",
    impuesto_electrico: factura.impuesto_electrico ?? "",
    iva: factura.iva ?? "",
    total_factura: factura.total_factura ?? "",
  });
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  const isComplete = useMemo(() => {
    return requiredFields.every((field) => form[field] !== "" && form[field] !== null && form[field] !== undefined);
  }, [form]);

  const handleNumberChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value === "" ? "" : Number(value) }));
  };

  const handleCheckbox = (e) => {
    const { name, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: checked }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("saving");
    setMessage("");
    try {
      const payload = { ...form };
      // limpiar strings vacios a null
      numberFields.forEach((field) => {
        if (payload[field] === "") payload[field] = null;
      });
      payload.estado_factura = isComplete ? "lista_para_comparar" : "pendiente_datos";

      await updateFactura(factura.id, payload);
      setStatus("saved");
      setMessage("Factura guardada correctamente");
    } catch (err) {
      setStatus("error");
      setMessage("No se pudo guardar la factura");
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <span className={`rounded-full px-3 py-1 ${isComplete ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"}`}>
            {isComplete ? "🟢 Factura lista para comparar" : "🔴 Factura incompleta"}
          </span>
          <span className="text-xs text-slate-400">ID #{factura.id} · {factura.filename}</span>
        </div>
        {message && (
          <span className={`text-xs ${status === "error" ? "text-red-400" : "text-emerald-400"}`}>
            {message}
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="card">
          <h3 className="text-sm font-semibold mb-3">Potencia</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="potencia_p1_kw">Potencia P1 (kW)</label>
              <input id="potencia_p1_kw" name="potencia_p1_kw" type="number" step="0.01" className="input" value={form.potencia_p1_kw} onChange={handleNumberChange} />
            </div>
            <div>
              <label className="label" htmlFor="potencia_p2_kw">Potencia P2 (kW)</label>
              <input id="potencia_p2_kw" name="potencia_p2_kw" type="number" step="0.01" className="input" value={form.potencia_p2_kw} onChange={handleNumberChange} />
            </div>
          </div>
        </section>

        <section className="card">
          <h3 className="text-sm font-semibold mb-3">Consumo por periodos</h3>
          <div className="grid gap-4 md:grid-cols-3">
            {["p1", "p2", "p3", "p4", "p5", "p6"].map((p) => (
              <div key={p}>
                <label className="label" htmlFor={`consumo_${p}_kwh`}>Consumo {p.toUpperCase()} (kWh)</label>
                <input
                  id={`consumo_${p}_kwh`}
                  name={`consumo_${p}_kwh`}
                  type="number"
                  step="0.01"
                  className="input"
                  value={form[`consumo_${p}_kwh`]}
                  onChange={handleNumberChange}
                />
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <h3 className="text-sm font-semibold mb-3">Condiciones</h3>
          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="bono_social" checked={form.bono_social} onChange={handleCheckbox} />
              Bono social
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="servicios_vinculados" checked={form.servicios_vinculados} onChange={handleCheckbox} />
              Servicios vinculados
            </label>
          </div>
          <div className="mt-4">
            <label className="label" htmlFor="alquiler_contador">Alquiler contador (€)</label>
            <input
              id="alquiler_contador"
              name="alquiler_contador"
              type="number"
              step="0.01"
              className="input"
              value={form.alquiler_contador}
              onChange={handleNumberChange}
            />
          </div>
        </section>

        <section className="card">
          <h3 className="text-sm font-semibold mb-3">Impuestos y total</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="label" htmlFor="impuesto_electrico">Impuesto eléctrico (€)</label>
              <input
                id="impuesto_electrico"
                name="impuesto_electrico"
                type="number"
                step="0.01"
                className="input"
                value={form.impuesto_electrico}
                onChange={handleNumberChange}
              />
            </div>
            <div>
              <label className="label" htmlFor="iva">IVA (€)</label>
              <input id="iva" name="iva" type="number" step="0.01" className="input" value={form.iva} onChange={handleNumberChange} />
            </div>
            <div>
              <label className="label" htmlFor="total_factura">Total factura (€)</label>
              <input
                id="total_factura"
                name="total_factura"
                type="number"
                step="0.01"
                className="input"
                value={form.total_factura}
                onChange={handleNumberChange}
              />
            </div>
          </div>
        </section>

        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={status === "saving"}>
            {status === "saving" ? "Guardando..." : "Guardar datos de factura"}
          </button>
        </div>
      </form>
    </div>
  );
}

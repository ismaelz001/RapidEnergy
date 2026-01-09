"use client";

import { useState, useMemo } from "react";
import { updateFactura, compareFactura } from "@/lib/apiClient";

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
  const [compareStatus, setCompareStatus] = useState("idle"); // idle | loading | success | error
  const [compareError, setCompareError] = useState("");
  const [offers, setOffers] = useState(null);
  const [selectedOffer, setSelectedOffer] = useState(null);

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

      await updateFactura(factura.id, payload);
      setStatus("saved");
      setMessage("Factura guardada correctamente");
    } catch (err) {
      setStatus("error");
      setMessage("No se pudo guardar la factura");
    }
  };

  const handleCompare = async () => {
    setCompareStatus("loading");
    setCompareError("");
    setOffers(null);
    try {
      const result = await compareFactura(factura.id);
      setOffers(result);
      setCompareStatus("success");
    } catch (err) {
      setCompareStatus("error");
      setCompareError(err.message || "Error al generar ofertas");
    }
  };

  const handleSelectOffer = (offerIndex) => {
    setSelectedOffer(offerIndex);
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

        {/* Sección de Comparar Tarifas */}
        <div className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-sm font-semibold">Comparar tarifas</span>
              <span className="text-xs text-slate-400">
                {!isComplete
                  ? "Completa los datos de la factura antes de comparar tarifas."
                  : "Genera 3 ofertas personalizadas para esta factura."}
              </span>
            </div>
            <button
              type="button"
              className="btn-primary bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed"
              disabled={!isComplete || compareStatus === "loading"}
              onClick={handleCompare}
              title={!isComplete ? "Completa los datos de la factura antes de comparar tarifas" : "Generar ofertas"}
            >
              {compareStatus === "loading" ? "Generando..." : "Comparar"}
            </button>
          </div>

          {!isComplete && (
            <p className="text-xs text-red-300">
              Completa los datos de la factura antes de comparar tarifas
            </p>
          )}

          {compareError && (
            <div className="text-xs text-red-400 bg-red-950/30 border border-red-800 rounded-lg p-3">
              {compareError}
            </div>
          )}

          {/* Ofertas generadas */}
          {offers && offers.offers && (
            <div className="flex flex-col gap-4 mt-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-emerald-400">
                  Ofertas disponibles
                </h3>
                <span className="text-xs text-slate-400">
                  Factura actual: {offers.current_total?.toFixed(2) || "0.00"} €
                </span>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {offers.offers.map((offer, idx) => (
                  <div
                    key={idx}
                    className={`relative flex flex-col gap-2 rounded-xl border p-4 transition-all ${
                      selectedOffer === idx
                        ? "border-emerald-500 bg-emerald-950/30"
                        : "border-slate-700 bg-slate-900/50 hover:border-slate-600"
                    }`}
                  >
                    {/* Tag */}
                    {offer.tag === "best_saving" && (
                      <span className="absolute -top-2 -right-2 rounded-full bg-emerald-500 px-2 py-1 text-[10px] font-bold uppercase tracking-wide">
                        Mejor ahorro
                      </span>
                    )}
                    {offer.tag === "balanced" && (
                      <span className="absolute -top-2 -right-2 rounded-full bg-blue-500 px-2 py-1 text-[10px] font-bold uppercase tracking-wide">
                        Equilibrado
                      </span>
                    )}
                    {offer.tag === "best_commission" && (
                      <span className="absolute -top-2 -right-2 rounded-full bg-purple-500 px-2 py-1 text-[10px] font-bold uppercase tracking-wide">
                        Top comisión
                      </span>
                    )}

                    <div className="flex flex-col gap-1">
                      <h4 className="text-sm font-semibold text-slate-100">{offer.provider}</h4>
                      <p className="text-xs text-slate-400">{offer.plan_name}</p>
                    </div>

                    <div className="flex flex-col gap-1 border-t border-slate-700 pt-2 mt-2">
                      <div className="flex items-baseline justify-between">
                        <span className="text-xs text-slate-400">Nuevo total:</span>
                        <span className="text-base font-bold text-slate-100">
                          {offer.estimated_total?.toFixed(2)} €
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between">
                        <span className="text-xs text-emerald-400">Ahorro:</span>
                        <span className="text-sm font-semibold text-emerald-400">
                          -{offer.saving_amount?.toFixed(2)} € ({offer.saving_percent}%)
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between">
                        <span className="text-xs text-purple-400">Comisión:</span>
                        <span className="text-sm font-semibold text-purple-400">
                          +{offer.commission?.toFixed(2)} €
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      className={`mt-2 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                        selectedOffer === idx
                          ? "bg-emerald-600 text-white"
                          : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                      onClick={() => handleSelectOffer(idx)}
                    >
                      {selectedOffer === idx ? "✓ Seleccionada" : "Seleccionar"}
                    </button>
                  </div>
                ))}
              </div>

              {selectedOffer !== null && (
                <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800 rounded-lg p-3">
                  <span>✓</span>
                  <span>
                    Has seleccionado <strong>{offers.offers[selectedOffer].provider}</strong>. 
                    (La selección aún no se persiste en BD, solo estado local)
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

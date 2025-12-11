import { listFacturas } from "@/lib/apiClient";

export const dynamic = "force-dynamic";

export default async function FacturasPage() {
  const facturas = await listFacturas();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Facturas procesadas</h1>
      <p className="text-xs text-slate-300">
        Esta vista consumirá un endpoint de FastAPI que devuelva las facturas almacenadas
        en Neon. De momento asumimos un formato simple: id, cups, consumo_kwh, importe, fecha.
      </p>

      <div className="card">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Consumo (kWh)</th>
              <th className="py-2 text-left">Importe</th>
              <th className="py-2 text-left">Fecha</th>
            </tr>
          </thead>
          <tbody>
            {facturas && facturas.length > 0 ? (
              facturas.map((f) => (
                <tr key={f.id} className="border-b border-slate-900">
                  <td className="py-2">{f.id}</td>
                  <td className="py-2">{f.cups || "-"}</td>
                  <td className="py-2">{f.consumo_kwh || "-"}</td>
                  <td className="py-2">{f.importe || "-"}</td>
                  <td className="py-2">{f.fecha || "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-4 text-center text-slate-500">
                  No hay facturas todavía.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

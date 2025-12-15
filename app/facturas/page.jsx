import { listFacturas } from "@/lib/apiClient";

export const dynamic = "force-dynamic";

export default async function FacturasPage() {
  const facturas = await listFacturas();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Facturas procesadas</h1>
      <p className="text-xs text-slate-300">
        Esta vista consume el endpoint de FastAPI con facturas almacenadas en Neon. Formato: id, cups, consumo_kwh,
        importe, fecha.
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
              <th className="py-2 text-left"></th>
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
                  <td className="py-2">
                    <a href={`/facturas/${f.id}`} className="text-emerald-400 hover:text-emerald-300">
                      Ver/editar
                    </a>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-4 text-center text-slate-500">
                  No hay facturas todavia.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

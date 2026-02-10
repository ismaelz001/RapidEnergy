import Link from "next/link";
import { listClientes } from "@/lib/apiClient";

export const dynamic = "force-dynamic";

export default async function ClientesPage() {
  const clientes = await listClientes();

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-emerald-400">CRM</p>
          <h1 className="text-2xl font-semibold">Clientes</h1>
          <p className="text-xs text-slate-400">
            Listado de clientes enriquecidos desde facturas y creados manualmente.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/clientes/nuevo" className="btn-primary">
            + Nuevo cliente
          </Link>
          <Link href="/wizard/new/step-1-factura" className="btn-secondary">
            + Nueva factura
          </Link>
        </div>
      </div>

      <div className="bg-[#0F172A] rounded-[16px] p-6">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/8 text-[#F1F5F9]">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">Nombre</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Telefono</th>
              <th className="py-2 text-left">Estado</th>
              <th className="py-2 text-left">Facturas</th>
              <th className="py-2 text-left"></th>
            </tr>
          </thead>
          <tbody>
            {clientes && clientes.length > 0 ? (
              clientes.map((c) => (
                <tr key={c.id} className="border-b border-white/5 hover:bg-[#1E293B] transition-colors group">
                  <td className="py-3 text-[#94A3B8]">{c.id}</td>
                  <td className="py-3 font-medium text-[#F1F5F9]">{c.nombre || "Sin nombre"}</td>
                  <td className="py-3 text-[#94A3B8]">{c.cups || "-"}</td>
                  <td className="py-3 text-[#94A3B8]">{c.telefono || "-"}</td>
                  <td className="py-3">
                    <span className="rounded-full bg-[#1E3A8A] text-white px-2 py-1 text-[11px] font-medium uppercase tracking-wide">
                      {c.estado || "lead"}
                    </span>
                  </td>
                  <td className="py-3 text-[#94A3B8]">{c.facturas?.length || 0}</td>
                  <td className="py-3 text-right">
                    <Link href={`/clientes/${c.id}`} className="text-emerald-400 hover:text-emerald-300">
                      Ver detalle
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="py-4 text-center text-[#94A3B8]">
                  No hay clientes todavia.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import Link from "next/link";
import { getFactura } from "@/lib/apiClient";
import FacturaDetailClient from "./FacturaDetailClient";

export const dynamic = "force-dynamic";

export default async function FacturaDetailPage({ params }) {
  const factura = await getFactura(params.id);

  if (!factura) {
    return (
      <div className="card">
        <p className="text-sm text-red-300">Factura no encontrada</p>
        <Link href="/facturas" className="mt-4 inline-block text-emerald-400 hover:text-emerald-300">
          ← Volver al listado
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-emerald-400">Detalle de factura</p>
          <h1 className="text-2xl font-semibold">Factura #{factura.id}</h1>
          <p className="text-xs text-slate-400">
            Archivo: {factura.filename} · CUPS: {factura.cups || "N/A"} · Fecha: {factura.fecha || "N/A"}
          </p>
        </div>
        <Link href="/facturas" className="text-xs text-emerald-400 hover:text-emerald-300">
          ← Volver a facturas
        </Link>
      </div>

      <FacturaDetailClient factura={factura} />
    </div>
  );
}

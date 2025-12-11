import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6 py-4">
      <h1 className="text-2xl font-semibold">Panel general</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <h2 className="text-sm font-semibold">Facturas procesadas</h2>
          <p className="mt-2 text-3xl font-bold">--</p>
          <p className="mt-1 text-xs text-slate-400">
            Este KPI se conectará a la API del backend (FastAPI + Neon).
          </p>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold">Clientes activos</h2>
          <p className="mt-2 text-3xl font-bold">--</p>
          <p className="mt-1 text-xs text-slate-400">
            Placeholder para métricas de clientes / intermediarios.
          </p>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold">Ahorro estimado</h2>
          <p className="mt-2 text-3xl font-bold">-- €</p>
          <p className="mt-1 text-xs text-slate-400">
            Más adelante podremos estimar el ahorro total de todas las ofertas.
          </p>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-2 text-sm font-semibold">Acciones rápidas</h2>
        <div className="flex flex-wrap gap-3 text-xs">
          <Link href="/facturas/upload" className="btn-primary">
            Subir nueva factura
          </Link>
          <Link href="/facturas" className="btn-primary bg-slate-800 hover:bg-slate-700">
            Ver listado de facturas
          </Link>
        </div>
      </div>
    </div>
  );
}

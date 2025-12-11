import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6 py-10">
      <section className="card">
        <h1 className="mb-2 text-2xl font-semibold">
          MVP Energia CRM
        </h1>
        <p className="text-sm text-slate-300">
          Panel mínimo para probar el flujo de análisis de facturas energéticas:
          subida de factura, envío al backend FastAPI y visualización de datos
          parseados desde la base de datos en Neon.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/facturas/upload" className="btn-primary">
            Subir factura de prueba
          </Link>
          <Link href="/facturas" className="text-xs text-slate-300 underline underline-offset-4">
            Ver facturas procesadas
          </Link>
          <Link href="/dashboard" className="text-xs text-slate-300 underline underline-offset-4">
            Ir al panel
          </Link>
        </div>
      </section>
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import ClienteEditor from "./ClienteEditor";

export default function ClienteDetailShell({ initialCliente }) {
  const [cliente, setCliente] = useState(initialCliente);

  if (!cliente) {
    return (
      <div className="card">
        <p className="text-sm text-red-300">No se encontro el cliente solicitado.</p>
        <Link href="/clientes" className="mt-4 inline-block text-emerald-400 hover:text-emerald-300">
          Volver al listado
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-emerald-400">Detalle de cliente</p>
          <h1 className="text-2xl font-semibold">{cliente.nombre || "Cliente sin nombre"}</h1>
          <p className="text-xs text-slate-400">CUPS: {cliente.cups || "No informado"}</p>
        </div>
        <Link href="/clientes" className="text-xs text-emerald-400 hover:text-emerald-300">
          ← Volver a clientes
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <p className="text-[11px] uppercase text-slate-400">Estado</p>
          <p className="mt-1 text-xl font-semibold">{cliente.estado || "lead"}</p>
        </div>
        <div className="card">
          <p className="text-[11px] uppercase text-slate-400">Telefono</p>
          <p className="mt-1 text-xl font-semibold">{cliente.telefono || "Sin telefono"}</p>
        </div>
        <div className="card">
          <p className="text-[11px] uppercase text-slate-400">Facturas</p>
          <p className="mt-1 text-xl font-semibold">{cliente.facturas?.length || 0}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Datos de contacto</h2>
            <p className="text-xs text-slate-400">Edita nombre, email, telefono o direccion.</p>
          </div>
          <ClienteEditor cliente={cliente} onUpdated={setCliente} />
        </div>

        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Facturas asociadas</h2>
            <Link href="/facturas" className="text-xs text-emerald-400 hover:text-emerald-300">
              Ver todas
            </Link>
          </div>
          {cliente.facturas && cliente.facturas.length > 0 ? (
            <div className="overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 text-left">ID</th>
                    <th className="py-2 text-left">Archivo</th>
                    <th className="py-2 text-left">Importe</th>
                    <th className="py-2 text-left">Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {cliente.facturas.map((f) => (
                    <tr key={f.id} className="border-b border-slate-900">
                      <td className="py-2">{f.id}</td>
                      <td className="py-2">{f.filename}</td>
                      <td className="py-2">{f.importe || "-"}</td>
                      <td className="py-2">{f.fecha || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Este cliente aun no tiene facturas asociadas.</p>
          )}
        </div>
      </div>
    </div>
  );
}

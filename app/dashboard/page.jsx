"use client";

import { useState } from 'react';
import Link from "next/link";
import Button from '../components/Button';
import Badge from '../components/Badge';

export default function DashboardPage() {
  const [showKPIs, setShowKPIs] = useState(false);

  // Mock data
  const casosEnCurso = [
    {
      id: 123,
      cliente: 'López',
      estado: 'pendiente',
      action: 'Continuar',
      href: '/wizard/123/step-2-validar'
    },
    {
      id: 124,
      cliente: 'Martínez',
      estado: 'seleccionada',
      action: 'Generar presupuesto',
      href: '/wizard/124/step-3-comparar'
    }
  ];

  const kpis = [
    { label: 'Facturas', value: '12' },
    { label: 'Ahorro', value: '2.340€' },
    { label: 'Comisión', value: '156€' }
  ];

  return (
    <div className="flex flex-col gap-6 py-8">
      {/* CTA Principal */}
      <div className="flex justify-center">
        <Link href="/wizard/new/step-1-factura">
          <Button variant="primary" className="text-lg px-12 py-4">
            NUEVA FACTURA
          </Button>
        </Link>
      </div>

      {/* Casos en curso */}
      <div>
        <h2 className="text-xl font-bold text-gris-texto mb-4">
          Casos en curso
        </h2>
        {casosEnCurso.length > 0 ? (
          <div className="space-y-3">
            {casosEnCurso.map((caso) => (
              <div key={caso.id} className="card flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-gris-texto">
                      Factura #{caso.id} - Cliente: {caso.cliente}
                    </span>
                    <Badge variant={caso.estado}>
                      {caso.estado === 'pendiente' ? 'Validar datos' : 'Oferta seleccionada'}
                    </Badge>
                  </div>
                </div>
                <Link href={caso.href}>
                  <Button variant="secondary" className="text-sm">
                    {caso.action} →
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div className="card text-center text-gris-secundario">
            <p>No tienes casos en curso. Sube una factura para empezar.</p>
          </div>
        )}
      </div>

      {/* Resumen (colapsable) */}
      <div>
        <button
          onClick={() => setShowKPIs(!showKPIs)}
          className="text-sm text-azul-control hover:underline mb-3"
        >
          {showKPIs ? 'Ocultar resumen' : 'Mostrar resumen'}
        </button>

        {showKPIs && (
          <div className="grid grid-cols-3 gap-4">
            {kpis.map((kpi) => (
              <div key={kpi.label} className="card text-center">
                <div className="text-3xl font-bold text-gris-texto mb-1">
                  {kpi.value}
                </div>
                <div className="text-sm text-gris-secundario">
                  {kpi.label}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

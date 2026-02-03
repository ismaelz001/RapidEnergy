"use client";

import { useEffect, useState } from 'react';
import { listComisiones, validarComision, marcarComisionPagada, getComisionDetalle, exportarComisionesCSV } from '@/lib/apiClient';
import Badge from '@/app/components/Badge';
import Button from '@/app/components/Button';
import Modal from '@/app/components/Modal';

export default function PagosPage() {
  const [comisiones, setComisiones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState('pendiente');
  const [filtroFechaDesde, setFiltroFechaDesde] = useState('');
  const [filtroFechaHasta, setFiltroFechaHasta] = useState('');
  const [filtroAsesor, setFiltroAsesor] = useState('');
  const [selectedComision, setSelectedComision] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [detalleComision, setDetalleComision] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);

  useEffect(() => {
    loadComisiones();
  }, [filtroEstado, filtroFechaDesde, filtroFechaHasta, filtroAsesor]);

  const loadComisiones = async () => {
    setLoading(true);
    try {
      const filters = { estado: filtroEstado };
      if (filtroFechaDesde) filters.fecha_desde = filtroFechaDesde;
      if (filtroFechaHasta) filters.fecha_hasta = filtroFechaHasta;
      if (filtroAsesor) filters.comercial_id = parseInt(filtroAsesor);
      
      const data = await listComisiones(filters);
      setComisiones(data);
    } catch (error) {
      console.error('[PAGOS] Error cargando comisiones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidar = async (id) => {
    if (!confirm('¿Validar esta comisión?')) return;
    
    try {
      await validarComision(id);
      alert('✅ Comisión validada');
      loadComisiones();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const handlePagar = async (id) => {
    if (!confirm('¿Marcar como pagada?')) return;
    
    try {
      await marcarComisionPagada(id);
      alert('✅ Comisión marcada como pagada');
      loadComisiones();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const handleVerDetalle = async (id) => {
    setModalOpen(true);
    setLoadingDetalle(true);
    setDetalleComision(null);
    
    try {
      const detalle = await getComisionDetalle(id);
      setDetalleComision(detalle);
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
      setModalOpen(false);
    } finally {
      setLoadingDetalle(false);
    }
  };

  const handleExportar = async () => {
    try {
      await exportarComisionesCSV({ estado: filtroEstado });
    } catch (error) {
      alert(`❌ Error exportando: ${error.message}`);
    }
  };

  const estadoBadgeVariant = (estado) => {
    switch (estado) {
      case 'pendiente': return 'pendiente';
      case 'validada': return 'seleccionada';
      case 'pagada': return 'completada';
      case 'anulada': return 'error';
      default: return 'pendiente';
    }
  };

  const estados = [
    { value: 'pendiente', label: 'Pendientes', count: comisiones.length },
    { value: 'validada', label: 'Validadas', count: 0 },
    { value: 'pagada', label: 'Pagadas', count: 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Filtros y Acciones */}
      <div className="space-y-4">
        {/* Filtros de Estado */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {estados.map((estado) => (
              <button
                key={estado.value}
                onClick={() => setFiltroEstado(estado.value)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                  filtroEstado === estado.value
                    ? 'bg-[#1E3A8A] text-white'
                    : 'bg-[#0F172A] text-[#94A3B8] hover:text-white'
                }`}
              >
                {estado.label}
              </button>
            ))}
          </div>
          
          <Button onClick={handleExportar} variant="secondary">
            📥 Exportar CSV
          </Button>
        </div>

        {/* Filtros Avanzados */}
        <div className="card p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-[#94A3B8] mb-2 block">Fecha Desde</label>
              <input
                type="date"
                value={filtroFechaDesde}
                onChange={(e) => setFiltroFechaDesde(e.target.value)}
                className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
              />
            </div>
            <div>
              <label className="text-xs text-[#94A3B8] mb-2 block">Fecha Hasta</label>
              <input
                type="date"
                value={filtroFechaHasta}
                onChange={(e) => setFiltroFechaHasta(e.target.value)}
                className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
              />
            </div>
            <div>
              <label className="text-xs text-[#94A3B8] mb-2 block">Asesor</label>
              <input
                type="text"
                placeholder="ID del asesor"
                value={filtroAsesor}
                onChange={(e) => setFiltroAsesor(e.target.value)}
                className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC] placeholder:text-[#64748B]"
              />
            </div>
          </div>
          {(filtroFechaDesde || filtroFechaHasta || filtroAsesor) && (
            <button
              onClick={() => {
                setFiltroFechaDesde('');
                setFiltroFechaHasta('');
                setFiltroAsesor('');
              }}
              className="mt-3 text-xs text-[#0073EC] hover:underline"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

      {/* Tabla de comisiones */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0073EC]"></div>
        </div>
      ) : comisiones.length > 0 ? (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-[#020617] text-white uppercase text-xs font-bold border-b border-white/5">
              <tr>
                <th className="px-4 py-3 text-left">Factura</th>
                <th className="px-4 py-3 text-left">Cliente</th>
                <th className="px-4 py-3 text-left">Asesor</th>
                <th className="px-4 py-3 text-left">Comisión</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {comisiones.map((com) => (
                <tr 
                  key={com.id} 
                  onClick={() => handleVerDetalle(com.id)}
                  className="hover:bg-[#1E293B] transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3 text-[#94A3B8]">#{com.factura_id}</td>
                  <td className="px-4 py-3 text-white font-medium">
                    {com.cliente_nombre || 'Sin nombre'}
                  </td>
                  <td className="px-4 py-3 text-[#94A3B8]">
                    {com.asesor_nombre}
                  </td>
                  <td className="px-4 py-3 text-green-400 font-semibold">
                    €{com.comision_total_eur.toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={estadoBadgeVariant(com.estado)}>
                      {com.estado}
                    </Badge>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-2">
                      {com.estado === 'pendiente' && (
                        <Button
                          variant="secondary"
                          onClick={() => handleValidar(com.id)}
                          className="text-xs px-3 py-1"
                        >
                          Validar
                        </Button>
                      )}
                      {com.estado === 'validada' && (
                        <Button
                          variant="primary"
                          onClick={() => handlePagar(com.id)}
                          className="text-xs px-3 py-1"
                        >
                          Pagar
                        </Button>
                      )}
                      {com.estado === 'pagada' && (
                        <span className="text-xs text-green-400">
                          ✓ Pagada {com.fecha_pago && `(${new Date(com.fecha_pago).toLocaleDateString('es-ES')})`}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card py-16 text-center border-dashed border-2 border-[rgba(255,255,255,0.08)] bg-transparent">
          <div className="text-5xl mb-4 opacity-20">💳</div>
          <h3 className="text-lg font-bold text-white mb-2">
            No hay comisiones {filtroEstado === 'pendiente' ? 'pendientes' : filtroEstado === 'validada' ? 'validadas' : 'pagadas'}
          </h3>
          <p className="text-[#94A3B8] max-w-sm mx-auto">
            {filtroEstado === 'pendiente' 
              ? 'Las comisiones generadas al seleccionar ofertas aparecerán aquí.'
              : 'Cambia el filtro para ver otras comisiones.'}
          </p>
        </div>
      )}

      {/* Modal Detalle */}
      <Modal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)}
        title={`Detalle Comisión #${detalleComision?.id || ''}`}
      >
        {loadingDetalle ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0073EC]"></div>
          </div>
        ) : detalleComision ? (
          <div className="space-y-6">
            {/* Info General */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-[#94A3B8] mb-1">Factura</div>
                <div className="text-white font-semibold">#{detalleComision.factura_id}</div>
              </div>
              <div>
                <div className="text-xs text-[#94A3B8] mb-1">Cliente</div>
                <div className="text-white font-semibold">{detalleComision.cliente_nombre || 'N/A'}</div>
              </div>
              <div>
                <div className="text-xs text-[#94A3B8] mb-1">Asesor</div>
                <div className="text-white font-semibold">{detalleComision.asesor_nombre || 'N/A'}</div>
              </div>
              <div>
                <div className="text-xs text-[#94A3B8] mb-1">CUPS</div>
                <div className="text-white font-mono text-xs">{detalleComision.cups || 'N/A'}</div>
              </div>
            </div>

            {/* Comisión */}
            <div className="bg-[#1E293B] rounded-lg p-4">
              <div className="text-xs text-[#94A3B8] mb-2">Comisión Total</div>
              <div className="text-3xl font-bold text-green-400">
                €{detalleComision.comision_total_eur.toFixed(2)}
              </div>
              {detalleComision.ahorro_anual && (
                <div className="text-xs text-[#94A3B8] mt-2">
                  Ahorro anual cliente: €{detalleComision.ahorro_anual.toFixed(2)}
                </div>
              )}
            </div>

            {/* Estado */}
            <div>
              <div className="text-xs text-[#94A3B8] mb-2">Estado</div>
              <Badge variant={estadoBadgeVariant(detalleComision.estado)}>
                {detalleComision.estado}
              </Badge>
              {detalleComision.fecha_pago && (
                <div className="text-sm text-[#94A3B8] mt-2">
                  Pagada el {new Date(detalleComision.fecha_pago).toLocaleDateString('es-ES')}
                </div>
              )}
            </div>

            {/* Repartos */}
            {detalleComision.repartos && detalleComision.repartos.length > 0 && (
              <div>
                <div className="text-sm font-bold text-white mb-3">💰 Reparto de Comisión</div>
                <div className="space-y-2">
                  {detalleComision.repartos.map((reparto) => (
                    <div key={reparto.id} className="flex items-center justify-between bg-[#1E293B] p-3 rounded-lg">
                      <div>
                        <div className="text-white font-medium">{reparto.destinatario_nombre || reparto.tipo_destinatario}</div>
                        {reparto.destinatario_email && (
                          <div className="text-xs text-[#94A3B8]">{reparto.destinatario_email}</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-green-400 font-semibold">€{reparto.importe_eur.toFixed(2)}</div>
                        {reparto.porcentaje && (
                          <div className="text-xs text-[#94A3B8]">{reparto.porcentaje.toFixed(1)}%</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-[#94A3B8]">Error cargando detalle</div>
        )}
      </Modal>
    </div>
  );
}

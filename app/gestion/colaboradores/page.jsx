"use client";

import { useEffect, useState } from 'react';
import { listUsers, createUser, updateUser, deleteUser, getUserStats, listColaboradores, createColaborador, updateColaborador, deleteColaborador } from '@/lib/apiClient';
import Badge from '@/app/components/Badge';
import Button from '@/app/components/Button';
import Modal from '@/app/components/Modal';

export default function ColaboradoresPage() {
  const [activeTab, setActiveTab] = useState('asesores');
  const [loading, setLoading] = useState(true);
  
  // Asesores
  const [asesores, setAsesores] = useState([]);
  const [modalAsesor, setModalAsesor] = useState(false);
  const [editingAsesor, setEditingAsesor] = useState(null);
  
  // Colaboradores
  const [colaboradores, setColaboradores] = useState([]);
  const [modalColaborador, setModalColaborador] = useState(false);
  const [editingColaborador, setEditingColaborador] = useState(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'asesores') {
        const data = await listUsers({ role: 'comercial' });
        setAsesores(data);
      } else {
        const data = await listColaboradores({ company_id: 1 });
        setColaboradores(data);
      }
    } catch (error) {
      console.error('[COLABORADORES] Error cargando:', error);
    } finally {
      setLoading(false);
    }
  };

  // =========== ASESORES ===========
  
  const handleCreateAsesor = () => {
    setEditingAsesor(null);
    setModalAsesor(true);
  };

  const handleEditAsesor = (asesor) => {
    setEditingAsesor(asesor);
    setModalAsesor(true);
  };

  const handleSaveAsesor = async (data) => {
    try {
      if (editingAsesor) {
        await updateUser(editingAsesor.id, data);
        alert('✅ Asesor actualizado');
      } else {
        // Al crear, usar los datos del formulario (ya incluyen role y company_id)
        await createUser(data);
        alert('✅ Asesor creado');
      }
      setModalAsesor(false);
      loadData();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const handleDeleteAsesor = async (id, nombre) => {
    if (!confirm(`¿Desactivar asesor ${nombre}?`)) return;
    
    try {
      await deleteUser(id);
      alert('✅ Asesor desactivado');
      loadData();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const handleActivarAsesor = async (id, nombre) => {
    try {
      await updateUser(id, { is_active: true });
      alert(`✅ Asesor ${nombre} activado`);
      loadData();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  // =========== COLABORADORES ===========
  
  const handleCreateColaborador = () => {
    setEditingColaborador(null);
    setModalColaborador(true);
  };

  const handleEditColaborador = (colaborador) => {
    setEditingColaborador(colaborador);
    setModalColaborador(true);
  };

  const handleSaveColaborador = async (data) => {
    try {
      if (editingColaborador) {
        await updateColaborador(editingColaborador.id, data);
        alert('✅ Colaborador actualizado');
      } else {
        await createColaborador({ ...data, company_id: 1 });
        alert('✅ Colaborador creado');
      }
      setModalColaborador(false);
      loadData();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const handleDeleteColaborador = async (id, nombre) => {
    if (!confirm(`¿Eliminar colaborador ${nombre}?`)) return;
    
    try {
      await deleteColaborador(id);
      alert('✅ Colaborador eliminado');
      loadData();
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setActiveTab('asesores')}
          className={`px-6 py-3 rounded-lg text-sm font-semibold transition-colors ${
            activeTab === 'asesores'
              ? 'bg-[#1E3A8A] text-white'
              : 'bg-[#0F172A] text-[#94A3B8] hover:text-white'
          }`}
        >
          👥 Asesores ({asesores.length})
        </button>
        <button
          onClick={() => setActiveTab('externos')}
          className={`px-6 py-3 rounded-lg text-sm font-semibold transition-colors ${
            activeTab === 'externos'
              ? 'bg-[#1E3A8A] text-white'
              : 'bg-[#0F172A] text-[#94A3B8] hover:text-white'
          }`}
        >
          🤝 Colaboradores Externos ({colaboradores.length})
        </button>
      </div>

      {/* Contenido */}
      {activeTab === 'asesores' ? (
        <AsesoresTab
          asesores={asesores}
          loading={loading}
          onCreate={handleCreateAsesor}
          onEdit={handleEditAsesor}
          onDelete={handleDeleteAsesor}
          onActivar={handleActivarAsesor}
        />
      ) : (
        <ColaboradoresTab
          colaboradores={colaboradores}
          loading={loading}
          onCreate={handleCreateColaborador}
          onEdit={handleEditColaborador}
          onDelete={handleDeleteColaborador}
        />
      )}

      {/* Modales */}
      {modalAsesor && (
        <ModalFormAsesor
          isOpen={modalAsesor}
          onClose={() => setModalAsesor(false)}
          onSave={handleSaveAsesor}
          editing={editingAsesor}
        />
      )}

      {modalColaborador && (
        <ModalFormColaborador
          isOpen={modalColaborador}
          onClose={() => setModalColaborador(false)}
          onSave={handleSaveColaborador}
          editing={editingColaborador}
        />
      )}
    </div>
  );
}

// ========================================
// TAB ASESORES
// ========================================

function AsesoresTab({ asesores, loading, onCreate, onEdit, onDelete, onActivar }) {
  const activos = asesores.filter(a => a.is_active);
  const inactivos = asesores.filter(a => !a.is_active);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0073EC]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-white">Asesores Comerciales</h3>
        <Button onClick={onCreate} variant="primary">
          + Añadir Asesor
        </Button>
      </div>

      {/* Activos */}
      <div className="card">
        <h4 className="text-sm font-bold text-white mb-4">✅ Activos ({activos.length})</h4>
        {activos.length > 0 ? (
          <div className="space-y-3">
            {activos.map((asesor) => (
              <div key={asesor.id} className="flex items-center justify-between bg-[#1E293B] p-4 rounded-lg">
                <div>
                  <div className="text-white font-semibold">{asesor.name}</div>
                  <div className="text-xs text-[#94A3B8]">{asesor.email}</div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => onEdit(asesor)}
                    className="text-xs px-3 py-1"
                  >
                    Editar
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => onDelete(asesor.id, asesor.name)}
                    className="text-xs px-3 py-1"
                  >
                    Desactivar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-[#94A3B8]">No hay asesores activos</div>
        )}
      </div>

      {/* Inactivos */}
      {inactivos.length > 0 && (
        <details className="card cursor-pointer">
          <summary className="text-sm font-bold text-[#94A3B8] hover:text-white transition-colors">
            🔴 Inactivos ({inactivos.length})
          </summary>
          <div className="mt-4 space-y-3">
            {inactivos.map((asesor) => (
              <div key={asesor.id} className="flex items-center justify-between bg-[#0F172A] p-4 rounded-lg opacity-60">
                <div>
                  <div className="text-white font-semibold">{asesor.name}</div>
                  <div className="text-xs text-[#94A3B8]">{asesor.email}</div>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => onActivar(asesor.id, asesor.name)}
                  className="text-xs px-3 py-1"
                >
                  Reactivar
                </Button>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

// ========================================
// TAB COLABORADORES
// ========================================

function ColaboradoresTab({ colaboradores, loading, onCreate, onEdit, onDelete }) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0073EC]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-white">Colaboradores Externos</h3>
        <Button onClick={onCreate} variant="primary">
          + Añadir Colaborador
        </Button>
      </div>

      {colaboradores.length > 0 ? (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-[#020617] text-white uppercase text-xs font-bold border-b border-white/5">
              <tr>
                <th className="px-4 py-3 text-left">Nombre</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Teléfono</th>
                <th className="px-4 py-3 text-left">Notas</th>
                <th className="px-4 py-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {colaboradores.map((col) => (
                <tr key={col.id} className="hover:bg-[#1E293B] transition-colors">
                  <td className="px-4 py-3 text-white font-medium">{col.nombre}</td>
                  <td className="px-4 py-3 text-[#94A3B8]">{col.email || 'N/A'}</td>
                  <td className="px-4 py-3 text-[#94A3B8]">{col.telefono || 'N/A'}</td>
                  <td className="px-4 py-3 text-[#94A3B8] text-xs truncate max-w-xs">
                    {col.notas || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => onEdit(col)}
                        className="text-xs px-3 py-1"
                      >
                        Editar
                      </Button>
                      <Button
                        variant="danger"
                        onClick={() => onDelete(col.id, col.nombre)}
                        className="text-xs px-3 py-1"
                      >
                        Eliminar
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card py-16 text-center border-dashed border-2 border-[rgba(255,255,255,0.08)] bg-transparent">
          <div className="text-5xl mb-4 opacity-20">🤝</div>
          <h3 className="text-lg font-bold text-white mb-2">No hay colaboradores externos</h3>
          <p className="text-[#94A3B8] max-w-sm mx-auto mb-4">
            Los colaboradores son personas que reciben comisiones sin acceso al sistema.
          </p>
          <Button onClick={onCreate} variant="primary">
            + Añadir Primer Colaborador
          </Button>
        </div>
      )}
    </div>
  );
}

// ========================================
// MODAL FORM ASESOR
// ========================================

function ModalFormAsesor({ isOpen, onClose, onSave, editing }) {
  const [formData, setFormData] = useState({
    name: editing?.name || '',
    email: editing?.email || '',
    role: editing?.role || 'comercial',
    company_id: editing?.company_id || 1,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editing ? 'Editar Asesor' : 'Nuevo Asesor'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Nombre completo</label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="Juan Pérez"
          />
        </div>
        
        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Email</label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="juan@ejemplo.com"
          />
        </div>

        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Rol</label>
          <select
            required
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
          >
            <option value="comercial">Comercial</option>
            <option value="manager">Manager</option>
            <option value="ceo">CEO</option>
            <option value="dev">Desarrollador</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Company ID</label>
          <input
            type="number"
            required
            value={formData.company_id}
            onChange={(e) => setFormData({ ...formData, company_id: parseInt(e.target.value) })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="1"
          />
          <p className="text-xs text-[#64748B] mt-1">Por defecto: 1 (empresa principal)</p>
        </div>

        <div className="flex gap-3 pt-4">
          <Button type="submit" variant="primary" className="flex-1">
            {editing ? 'Guardar Cambios' : 'Crear Asesor'}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}

// ========================================
// MODAL FORM COLABORADOR
// ========================================

function ModalFormColaborador({ isOpen, onClose, onSave, editing }) {
  const [formData, setFormData] = useState({
    nombre: editing?.nombre || '',
    email: editing?.email || '',
    telefono: editing?.telefono || '',
    notas: editing?.notas || '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editing ? 'Editar Colaborador' : 'Nuevo Colaborador'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Nombre</label>
          <input
            type="text"
            required
            value={formData.nombre}
            onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="María García"
          />
        </div>
        
        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Email (opcional)</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="maria@ejemplo.com"
          />
        </div>

        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Teléfono (opcional)</label>
          <input
            type="tel"
            value={formData.telefono}
            onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="600123456"
          />
        </div>

        <div>
          <label className="text-xs text-[#94A3B8] mb-2 block">Notas (opcional)</label>
          <textarea
            value={formData.notas}
            onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
            className="w-full bg-[#1E293B] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#0073EC]"
            placeholder="Información adicional..."
            rows={3}
          />
        </div>

        <div className="flex gap-3 pt-4">
          <Button type="submit" variant="primary" className="flex-1">
            {editing ? 'Guardar Cambios' : 'Crear Colaborador'}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}

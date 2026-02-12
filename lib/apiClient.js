// Usa la URL de backend configurada; en prod debe estar definida en NEXT_PUBLIC_API_URL.
const getBackendUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return "http://localhost:8000";
  }
  return "https://rapidenergy.onrender.com";
};

const API_URL = getBackendUrl();

// ════════════════════════════════════════════════════════
// AUTH HELPERS - Sistema de autenticación mock
// ════════════════════════════════════════════════════════

/**
 * Obtiene el user_id del localStorage
 */
function getUserId() {
  if (typeof window === 'undefined') return 1; // Default para SSR
  return parseInt(localStorage.getItem('user_id') || '1');
}

/**
 * Obtiene el rol del usuario
 */
function getUserRole() {
  if (typeof window === 'undefined') return 'dev';
  return localStorage.getItem('user_role') || 'dev';
}

/**
 * Headers con autenticación automática
 */
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-User-Id': getUserId().toString(),
  };
}

/**
 * Helpers de permisos para usar en componentes
 */
export const auth = {
  getUserId,
  getUserRole,
  isDev: () => getUserRole() === 'dev',
  isCEO: () => ['dev', 'ceo'].includes(getUserRole()),
  isComercial: () => getUserRole() === 'comercial',
  canAccessGestion: () => ['dev', 'ceo'].includes(getUserRole()),
  canManagePayments: () => ['dev', 'ceo'].includes(getUserRole()),
};

// ════════════════════════════════════════════════════════
// API FUNCTIONS
// ════════════════════════════════════════════════════════

export async function uploadFactura(file) {
  if (process.env.NEXT_PUBLIC_TEST_MODE === 'true') {
    console.log(`🚀 [UPLOAD] Posteando a: ${API_URL}/webhook/upload`, {
      filename: file.name,
      size: file.size,
      type: file.type
    });
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/webhook/upload`, {
    method: "POST",
    headers: {
      'X-User-Id': getUserId().toString(),
    },
    body: formData,
  });

  if (!res.ok) {
    // P6: Incluimos el status para que el frontend detecte el 409 (Conflicto/Duplicado)
    const errorText = await res.text().catch(() => "Error subiendo factura");
    const error = new Error(errorText || "Error subiendo factura");
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export async function listFacturas() {
  try {
    const res = await fetch(`${API_URL}/webhook/facturas`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });

    if (!res.ok) {
      console.error("Error obteniendo facturas");
      return [];
    }

    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("Error en listFacturas:", e);
    return [];
  }
}

export async function getFactura(id) {
  try {
    const res = await fetch(`${API_URL}/webhook/facturas/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      console.error("Error obteniendo factura", id);
      return null;
    }
    return await res.json();
  } catch (e) {
    console.error("Error en getFactura:", e);
    return null;
  }
}

export async function updateFactura(id, payload) {
  const res = await fetch(`${API_URL}/webhook/facturas/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const contentType = res.headers.get("content-type") || "";
  if (!res.ok) {
    let data = null;
    let message = "Error actualizando factura";
    if (contentType.includes("application/json")) {
      data = await res.json().catch(() => null);
      message =
        data?.detail?.message ||
        data?.detail ||
        data?.message ||
        message;
    } else {
      const text = await res.text().catch(() => "");
      if (text) message = text;
    }
    const error = new Error(message);
    error.data = data;
    throw error;
  }
  return contentType.includes("application/json") ? res.json() : res.text();
}

/**
 * Valida comercialmente una factura (Step 2)
 * Marca validado_step2=True y permite comparar
 */
export async function validarFacturaComercialmente(id, payload) {
  const res = await fetch(`${API_URL}/webhook/facturas/${id}/validar`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ajustes_comerciales: payload.ajustes_comerciales || {},
      modo: payload.modo || "asesor"
    }),
  });
  
  if (!res.ok) {
    const contentType = res.headers.get("content-type") || "";
    let data = null;
    let message = "Error en validación comercial";
    
    if (contentType.includes("application/json")) {
      data = await res.json().catch(() => null);
      message =
        data?.detail?.message ||
        data?.detail ||
        data?.message ||
        message;
    } else {
      const text = await res.text().catch(() => "");
      if (text) message = text;
    }
    
    const error = new Error(message);
    error.data = data;
    throw error;
  }
  
  return res.json();
}

export async function listClientes() {
  try {
    const res = await fetch(`${API_URL}/api/clientes`, {
      cache: "no-store",
    });

    if (!res.ok) {
      console.error("Error obteniendo clientes");
      return [];
    }

    return await res.json();
  } catch (e) {
    console.error("Error en listClientes:", e);
    return [];
  }
}

export async function getCliente(id) {
  try {
    const res = await fetch(`${API_URL}/api/clientes/${id}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      console.error("Error obteniendo cliente", id);
      return null;
    }

    return await res.json();
  } catch (e) {
    console.error("Error en getCliente:", e);
    return null;
  }
}

export async function updateCliente(id, payload) {
  const res = await fetch(`${API_URL}/api/clientes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Error actualizando cliente");
    throw new Error(errorText || "Error actualizando cliente");
  }

  return res.json();
}

export async function compareFactura(facturaId, payload = null) {
  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  };
  
  if (payload) {
    options.body = JSON.stringify(payload);
  }

  const res = await fetch(`${API_URL}/webhook/comparar/facturas/${facturaId}`, options);

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Error comparando factura");
    throw new Error(errorText || "Error comparando factura");
  }

  return res.json();
}

export async function selectOffer(facturaId, offer) {
  const res = await fetch(`${API_URL}/webhook/facturas/${facturaId}/seleccion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(offer),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Error guardando oferta");
    throw new Error(errorText || "Error guardando oferta");
  }

  return res.json();
}

export async function downloadPresupuestoPDF(facturaId) {
  const res = await fetch(`${API_URL}/webhook/facturas/${facturaId}/presupuesto.pdf`, {
    method: "GET",
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Error generando PDF");
    throw new Error(errorText || "Error generando PDF");
  }

  return res.blob();
}
export async function deleteFactura(id) {
  const res = await fetch(`${API_URL}/webhook/facturas/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || "Error al eliminar factura";
    throw new Error(message);
  }

  return res.json();
}

export async function deleteCliente(id) {
  const res = await fetch(`${API_URL}/clientes/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || "Error al eliminar cliente";
    throw new Error(message);
  }

  return res.json();
}

// ========================================
// GESTIÓN: Stats & Comisiones
// ========================================

export async function getCeoStats() {
  const res = await fetch(`${API_URL}/api/stats/ceo`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo stats CEO");
    return { total_facturas_procesadas: 0, total_ahorro_generado: 0, comisiones_pendientes: 0, asesores_activos: 0, alertas: [] };
  }

  return res.json();
}

export async function getActividadReciente() {
  const res = await fetch(`${API_URL}/api/stats/actividad-reciente`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo actividad reciente");
    return [];
  }

  return res.json();
}

export async function listComisiones(filters = {}) {
  const params = new URLSearchParams();
  if (filters.estado) params.append('estado', filters.estado);
  if (filters.comercial_id) params.append('comercial_id', filters.comercial_id);
  
  const res = await fetch(`${API_URL}/api/comisiones?${params.toString()}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo comisiones");
    return [];
  }

  return res.json();
}

export async function validarComision(id) {
  const res = await fetch(`${API_URL}/api/comisiones/${id}/validar`, {
    method: "PATCH",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error validando comisión";
    throw new Error(message);
  }

  return res.json();
}

export async function marcarComisionPagada(id, fecha_pago = null) {
  const body = fecha_pago ? { fecha_pago } : {};
  
  const res = await fetch(`${API_URL}/api/comisiones/${id}/pagar`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error marcando comisión como pagada";
    throw new Error(message);
  }

  return res.json();
}

export async function getComisionDetalle(id) {
  const res = await fetch(`${API_URL}/api/comisiones/${id}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error obteniendo detalle";
    throw new Error(message);
  }

  return res.json();
}

export async function exportarComisionesCSV(filters = {}) {
  const params = new URLSearchParams();
  if (filters.estado) params.append('estado', filters.estado);
  if (filters.comercial_id) params.append('comercial_id', filters.comercial_id);
  if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
  if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
  
  const res = await fetch(`${API_URL}/api/comisiones/export/csv?${params.toString()}`);

  if (!res.ok) {
    throw new Error("Error exportando CSV");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `comisiones_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

// ========================================
// GESTIÓN: Users (Comerciales)
// ========================================

export async function listUsers(filters = {}) {
  const params = new URLSearchParams();
  if (filters.role) params.append('role', filters.role);
  if (filters.is_active !== undefined) params.append('is_active', filters.is_active);
  
  const res = await fetch(`${API_URL}/api/users?${params.toString()}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo users");
    return [];
  }

  return res.json();
}

export async function createUser(data) {
  const res = await fetch(`${API_URL}/api/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error creando comercial";
    throw new Error(message);
  }

  return res.json();
}

export async function updateUser(id, data) {
  const res = await fetch(`${API_URL}/api/users/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error actualizando comercial";
    throw new Error(message);
  }

  return res.json();
}

export async function getUserStats(id) {
  const res = await fetch(`${API_URL}/api/users/${id}/stats`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo stats user");
    return null;
  }

  return res.json();
}

export async function deleteUser(id) {
  const res = await fetch(`${API_URL}/api/users/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error desactivando comercial";
    throw new Error(message);
  }

  return res.json();
}

// ========================================
// GESTIÓN: Colaboradores
// ========================================

export async function listColaboradores(filters = {}) {
  const params = new URLSearchParams();
  if (filters.company_id) params.append('company_id', filters.company_id);
  if (filters.is_active !== undefined) params.append('is_active', filters.is_active);
  
  const res = await fetch(`${API_URL}/api/colaboradores?${params.toString()}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("Error obteniendo colaboradores");
    return [];
  }

  return res.json();
}

export async function createColaborador(data) {
  const res = await fetch(`${API_URL}/api/colaboradores`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error creando colaborador";
    throw new Error(message);
  }

  return res.json();
}

export async function updateColaborador(id, data) {
  const res = await fetch(`${API_URL}/api/colaboradores/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error actualizando colaborador";
    throw new Error(message);
  }

  return res.json();
}

export async function deleteColaborador(id) {
  const res = await fetch(`${API_URL}/api/colaboradores/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || "Error eliminando colaborador";
    throw new Error(message);
  }

  return res.json();
}

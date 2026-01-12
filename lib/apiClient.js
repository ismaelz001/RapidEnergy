// Usa la URL de backend configurada; en prod debe estar definida en NEXT_PUBLIC_API_URL.
const getBackendUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return "http://localhost:8000";
  }
  return "https://rapidenergy.onrender.com";
};

const API_URL = getBackendUrl();

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

export async function listClientes() {
  try {
    const res = await fetch(`${API_URL}/clientes`, {
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
    const res = await fetch(`${API_URL}/clientes/${id}`, {
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
  const res = await fetch(`${API_URL}/clientes/${id}`, {
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

export async function compareFactura(facturaId) {
  const res = await fetch(`${API_URL}/webhook/comparar/facturas/${facturaId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

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

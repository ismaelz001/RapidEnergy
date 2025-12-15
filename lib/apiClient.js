// Usa la URL de backend configurada; en prod debe estar definida en NEXT_PUBLIC_API_URL.
// Fallback a Render para evitar llamadas a localhost en Vercel si falta la env.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://rapidenergy.onrender.com";

export async function uploadFactura(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/webhook/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Error subiendo factura");
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
  if (!res.ok) {
    const text = await res.text().catch(() => "Error actualizando factura");
    throw new Error(text || "Error actualizando factura");
  }
  return res.json();
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

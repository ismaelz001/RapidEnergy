const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const res = await fetch(`${API_URL}/facturas`, {
      next: { revalidate: 0 },
    });
    if (!res.ok) {
      return [];
    }
    const data = await res.json();
    return Array.isArray(data) ? data : data.items || [];
  } catch (e) {
    console.error(e);
    return [];
  }
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ClienteDeleteButton({ clienteId, clienteNombre }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const res = await fetch(`/api/clientes/${clienteId}`, {
        method: "DELETE",
        credentials: "include", // Enviar cookies de sesión
      });

      if (res.ok) {
        // Éxito: recargar página para reflejar cambios
        router.refresh();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || "No se pudo eliminar el cliente"}`);
      }
    } catch (err) {
      alert(`Error de red: ${err.message}`);
    } finally {
      setIsDeleting(false);
      setShowModal(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="text-red-600 hover:text-red-800 font-medium"
        disabled={isDeleting}
      >
        Eliminar
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Confirmar eliminación</h3>
            <p className="text-gray-600 mb-6">
              ¿Seguro que quieres eliminar el cliente <strong>{clienteNombre}</strong>? 
              Esta acción anonizará sus datos (GDPR).
            </p>
            <div className="flex gap-4 justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={isDeleting}
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400"
                disabled={isDeleting}
              >
                {isDeleting ? "Eliminando..." : "Eliminar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

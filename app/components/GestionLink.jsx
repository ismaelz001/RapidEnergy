'use client';

import { useEffect, useState } from 'react';

export default function GestionLink() {
  const [canAccess, setCanAccess] = useState(false);

  useEffect(() => {
    const userRole = localStorage.getItem('user_role') || '';
    setCanAccess(['dev', 'ceo'].includes(userRole));
  }, []);

  if (!canAccess) {
    return null;
  }

  return (
    <a href="/gestion/resumen" className="text-sm font-medium text-[#94A3B8] hover:text-white transition">
      Gestión
    </a>
  );
}

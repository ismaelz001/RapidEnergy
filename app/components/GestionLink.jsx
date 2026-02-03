'use client';

import { useEffect, useState } from 'react';
import { getUserRole, canAccessGestion } from '@/lib/auth';

export default function GestionLink() {
  const [canAccess, setCanAccess] = useState(false);

  useEffect(() => {
    const role = getUserRole();
    setCanAccess(canAccessGestion(role));
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

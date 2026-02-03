"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function GestionIndexPage() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect automático a /resumen
    router.push('/gestion/resumen');
  }, [router]);
  
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-[#94A3B8]">Redirigiendo...</p>
    </div>
  );
}

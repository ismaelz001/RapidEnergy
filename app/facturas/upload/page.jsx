"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function UploadRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-gris-secundario">Redirigiendo al panel...</p>
    </div>
  );
}

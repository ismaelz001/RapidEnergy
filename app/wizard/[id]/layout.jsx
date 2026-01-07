"use client";

import WizardLayout from '@/app/components/wizard/WizardLayout';
import { WizardProvider } from '@/app/context/WizardContext';

export default function Layout({ children, params }) {
  // En Next.js 13+ App Router, usamos layout para persistir estado entre páginas hermanas
  // Pero necesitamos client components para Context. 
  // WizardLayout es client component, WizardProvider también.
  
  return (
    <WizardProvider>
      {/* Pasamos params y children hacia abajo */}
      {children}
    </WizardProvider>
  );
}

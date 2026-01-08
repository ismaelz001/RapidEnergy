"use client";

import { useRouter } from 'next/navigation';
import WizardStepper from './WizardStepper';
import Button from '../Button';

export default function WizardLayout({
  children,
  currentStep,
  onNext,
  onBack,
  nextDisabled = false,
  nextLabel = 'SIGUIENTE',
  showGenerateButton = false
}) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#0B1220] flex flex-col">
      {/* Header with stepper */}
      <header className="bg-[#0F172A] border-b border-white/8 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4">
          <WizardStepper currentStep={currentStep} />
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer with navigation */}
      <footer className="bg-[#0F172A] border-t border-white/8 p-4 sticky bottom-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Button
            variant="secondary"
            onClick={onBack || (() => router.back())}
            className={`bg-transparent border-white/10 text-[#94A3B8] hover:bg-white/5 ${currentStep === 1 ? 'invisible' : ''}`}
          >
            ← Volver
          </Button>

          <Button
            variant="primary"
            onClick={onNext}
            disabled={nextDisabled}
            className={`bg-[#1E3A8A] border-none text-white hover:bg-[#1E3A8A]/90 ${showGenerateButton ? 'text-lg px-8' : ''}`}
          >
            {nextLabel} →
          </Button>
        </div>
      </footer>
    </div>
  );
}

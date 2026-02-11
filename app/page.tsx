"use client";

import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1E3A8A] via-[#2563EB] to-[#16A34A] text-white">
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/10 backdrop-blur-md border-b border-white/20 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold tracking-tight">
            MecaEnergy
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="px-6 py-2.5 bg-[#16A34A] hover:bg-[#15803D] text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl"
            >
              Acceder al CRM
            </Link>
            <a
              href="#contacto"
              className="px-6 py-2.5 border-2 border-white/60 hover:border-white hover:bg-white/10 rounded-lg font-semibold transition-all"
            >
              Contacto
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="container mx-auto max-w-5xl text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6">
            MecaEnergy CRM
            <br />
            <span className="text-[#16A34A]">Comparador energético inteligente</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-3xl mx-auto">
            Sube tu factura, valida los datos y recibe la mejor oferta en segundos.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login"
              className="px-8 py-4 bg-[#16A34A] hover:bg-[#15803D] text-white text-lg font-bold rounded-xl shadow-2xl hover:shadow-[#16A34A]/50 transition-all transform hover:scale-105"
            >
              Entrar al CRM
            </Link>
            <a
              href="#valor"
              className="px-8 py-4 bg-white/10 hover:bg-white/20 backdrop-blur-sm border-2 border-white/40 hover:border-white text-white text-lg font-semibold rounded-xl transition-all"
            >
              Ver cómo funciona
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="valor" className="py-20 px-6 bg-white/5 backdrop-blur-sm">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">
            Todo lo que necesitas en un solo sistema
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 hover:bg-white/15 transition-all hover:shadow-2xl">
              <div className="text-5xl mb-4">📄</div>
              <h3 className="text-2xl font-bold mb-3">OCR Automático</h3>
              <p className="text-white/80 leading-relaxed">
                Extraemos CUPS, consumos y potencias de tu factura automáticamente con IA.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 hover:bg-white/15 transition-all hover:shadow-2xl">
              <div className="text-5xl mb-4">⚡</div>
              <h3 className="text-2xl font-bold mb-3">Comparador inteligente</h3>
              <p className="text-white/80 leading-relaxed">
                Calculamos 9 ofertas en tiempo real con precios reales del mercado energético.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 hover:bg-white/15 transition-all hover:shadow-2xl">
              <div className="text-5xl mb-4">📊</div>
              <h3 className="text-2xl font-bold mb-3">Presupuesto en PDF</h3>
              <p className="text-white/80 leading-relaxed">
                Genera un informe claro y auditable con desglose técnico para tu cliente.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contacto" className="py-12 px-6 bg-[#1E3A8A]/80 backdrop-blur-md border-t border-white/10">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-white/80">
              © 2026 MecaEnergy — <a href="https://rodorte.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors underline">rodorte.com</a>
            </div>
            <div className="flex gap-6 text-sm">
              <a href="#privacidad" className="text-white/60 hover:text-white transition-colors">
                Privacidad
              </a>
              <span className="text-white/30">|</span>
              <a href="#contacto" className="text-white/60 hover:text-white transition-colors">
                Contacto
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

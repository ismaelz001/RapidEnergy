import "./globals.css";

export const metadata = {
  title: "Energia CRM - MVP",
  description: "MVP CRM para automatización de facturas energéticas",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-[#0B1220] text-[#F1F5F9]">
        {/* Header Premium Gradient */}
        <header className="fixed top-0 w-full z-50 h-[72px] bg-gradient-premium border-b border-[rgba(255,255,255,0.08)] shadow-lg">
          <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 backdrop-blur border border-white/10">
                <span className="text-lg">⚡</span>
              </div>
              <span className="text-base font-bold tracking-wide text-white">
                MecaEnergy <span className="text-[#94A3B8] font-normal">CRM</span>
              </span>
            </div>

            {/* Actions */}
            <nav className="flex items-center gap-6">
              <a href="/dashboard" className="text-sm font-medium text-[#94A3B8] hover:text-white transition">
                Dashboard
              </a>
              <a href="/clientes" className="text-sm font-medium text-[#94A3B8] hover:text-white transition">
                Clientes
              </a>
              <a href="/facturas" className="text-sm font-medium text-[#94A3B8] hover:text-white transition">
                Facturas
              </a>
              <a href="/wizard/new/step-1-factura" className="inline-flex items-center justify-center h-10 px-5 text-sm font-bold text-white bg-[#1E3A8A] hover:bg-[#172554] rounded-lg shadow-lg shadow-blue-900/40 transition-all hover:scale-105 active:scale-95">
                + Nueva Factura
              </a>
            </nav>
          </div>
        </header>

        {/* Main Content Spacer */}
        <main className="mx-auto max-w-7xl px-6 pt-28 pb-12">
          {children}
        </main>
      </body>
    </html>
  );
}

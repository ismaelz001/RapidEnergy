import "./globals.css";
import { Poppins } from "next/font/google"; // EnergyLuz Font
/* eslint-disable @next/next/no-img-element */ // Using img for logo since it's in public

const poppins = Poppins({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-poppins",
});

export const metadata = {
  title: "EnergyLuz CRM",
  description: "CRM de asesoramiento energético EnergyLuz",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className={`min-h-screen bg-[#0B1220] text-[#F1F5F9] ${poppins.variable} font-sans`}>
        {/* Header EnergyLuz Gradient */}
        <header className="fixed top-0 w-full z-50 h-[72px] bg-gradient-premium border-b border-[rgba(255,255,255,0.08)] shadow-lg">
          <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
            {/* Logo */}
            <div className="flex items-center gap-3">
              {/* Logo Container with White Background */}
              <div className="flex bg-white px-2 py-1 rounded-md shadow-sm h-10 items-center justify-center">
                <img 
                  src="/energyluz_logo.png" 
                  alt="EnergyLuz" 
                  className="h-full w-auto object-contain" 
                />
              </div>
              {/* Text hidden on mobile, visible on desktop */}
              <span className="hidden ml-2 text-lg font-bold tracking-wide text-white md:block">
                EnergyLuz <span className="text-[#0073EC] font-normal">CRM</span>
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
              <a href="/wizard/new/step-1-factura" className="inline-flex items-center justify-center h-10 px-5 text-sm font-bold text-white bg-[#0073EC] hover:bg-blue-600 rounded-lg shadow-lg shadow-blue-500/40 transition-all hover:scale-105 active:scale-95">
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

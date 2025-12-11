import "./globals.css";

export const metadata = {
  title: "Energia CRM - MVP",
  description: "MVP CRM para automatización de facturas energéticas",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="min-h-screen">
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
          <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-2xl bg-emerald-500 text-xs font-bold">
                  EN
                </span>
                <span className="text-sm font-semibold tracking-wide">
                  Energia CRM
                </span>
              </div>
              <nav className="flex gap-4 text-xs text-slate-300">
                <a href="/dashboard" className="hover:text-emerald-400">
                  Panel
                </a>
                <a href="/facturas/upload" className="hover:text-emerald-400">
                  Subir factura
                </a>
                <a href="/facturas" className="hover:text-emerald-400">
                  Facturas
                </a>
                <a href="/login" className="hover:text-emerald-400">
                  Login
                </a>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-4 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

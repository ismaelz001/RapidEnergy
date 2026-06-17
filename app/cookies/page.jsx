export const metadata = {
  title: 'Politica de Cookies | EnergyLuz CRM',
  description: 'Informacion sobre el uso de cookies en EnergyLuz CRM.',
};

export default function CookiesPage() {
  return (
    <main style={{ maxWidth: '768px', margin: '0 auto', padding: '4rem 1.5rem', color: '#F1F5F9' }}>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '2rem' }}>Politica de Cookies</h1>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>1. Responsable del tratamiento</h2>
        <p style={{ color: '#94A3B8' }}>
          RodorteDev — ismael@rodorte.com<br />
          En cumplimiento del RGPD (UE) 2016/679 y la LSSI-CE.
        </p>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>2. Que son las cookies</h2>
        <p style={{ color: '#94A3B8' }}>
          Las cookies son pequenos ficheros de texto que se almacenan en tu dispositivo cuando visitas
          una pagina web. Permiten recordar tus preferencias y mejorar la experiencia de uso.
        </p>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>3. Cookies que utilizamos</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(115, 58, 237, 0.2)' }}>
                <th style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px', textAlign: 'left' }}>Nombre</th>
                <th style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px', textAlign: 'left' }}>Tipo</th>
                <th style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px', textAlign: 'left' }}>Finalidad</th>
                <th style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px', textAlign: 'left' }}>Duracion</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>mecaenergy-cookie-consent</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Propia / Tecnica</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Guardar tu eleccion sobre cookies</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Persistente (localStorage)</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Google Fonts</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Terceros / Tecnica</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Carga de tipografias (fonts.googleapis.com)</td>
                <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px' }}>Sesion</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>4. Como gestionar las cookies</h2>
        <p style={{ color: '#94A3B8', marginBottom: '0.75rem' }}>
          Puedes aceptar o rechazar las cookies desde el banner que aparece en tu primera visita,
          o desde el enlace &quot;Gestionar cookies&quot; en el menu de navegacion.
        </p>
        <p style={{ color: '#94A3B8' }}>
          Tambien puedes configurar tu navegador:{' '}
          <a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer" style={{ color: '#0073EC', textDecoration: 'underline' }}>Chrome</a>
          {' · '}
          <a href="https://support.mozilla.org/es/kb/cookies-informacion-que-los-sitios-web-guardan-en-" target="_blank" rel="noopener noreferrer" style={{ color: '#0073EC', textDecoration: 'underline' }}>Firefox</a>
          {' · '}
          <a href="https://support.apple.com/es-es/guide/safari/sfri11471/mac" target="_blank" rel="noopener noreferrer" style={{ color: '#0073EC', textDecoration: 'underline' }}>Safari</a>
        </p>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>5. Tus derechos</h2>
        <p style={{ color: '#94A3B8' }}>
          Tienes derecho a acceder, rectificar, suprimir y oponerte al tratamiento de tus datos.
          Escribe a ismael@rodorte.com para ejercerlos.
          Si no recibes respuesta satisfactoria, puedes reclamar ante la{' '}
          <a href="https://www.aepd.es" target="_blank" rel="noopener noreferrer" style={{ color: '#0073EC', textDecoration: 'underline' }}>AEPD</a>.
        </p>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>6. Actualizaciones</h2>
        <p style={{ color: '#94A3B8' }}>
          Esta politica puede actualizarse. El uso continuado del servicio tras un cambio implica su aceptacion.
        </p>
        <p style={{ fontSize: '0.75rem', color: 'rgba(241,245,249,0.4)', marginTop: '0.5rem' }}>Ultima actualizacion: junio 2025</p>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>7. Contacto</h2>
        <p style={{ color: '#94A3B8' }}>RodorteDev · ismael@rodorte.com</p>
      </section>
    </main>
  );
}

"""
Script de inicialización para datos de prueba del Panel CEO
Ejecutar SOLO en desarrollo/testing
"""

from sqlalchemy import text
from app.db.conn import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_test_data():
    """Crear datos de prueba si no existen"""
    db = SessionLocal()
    
    try:
        logger.info("🚀 Iniciando creación de datos de prueba...")
        
        # 1. Verificar/Crear Company
        company_check = db.execute(text("SELECT id FROM companies WHERE id = 1")).fetchone()
        if not company_check:
            logger.info("📦 Creando company de prueba...")
            db.execute(text("""
                INSERT INTO companies (id, name, nif, created_at)
                VALUES (1, 'EnergyLuz SA', 'B12345678', CURRENT_TIMESTAMP)
            """))
            db.commit()
        
        # 2. Verificar/Crear Users
        users_check = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
        if users_check.count == 0:
            logger.info("👥 Creando usuarios de prueba...")
            db.execute(text("""
                INSERT INTO users (email, name, role, company_id, is_active, created_at) VALUES
                ('admin@energyluz.com', 'Admin EnergyLuz', 'ceo', 1, true, CURRENT_TIMESTAMP),
                ('juan@energyluz.com', 'Juan Pérez', 'comercial', 1, true, CURRENT_TIMESTAMP),
                ('maria@energyluz.com', 'María López', 'comercial', 1, true, CURRENT_TIMESTAMP),
                ('carlos@energyluz.com', 'Carlos Ruiz', 'comercial', 1, false, CURRENT_TIMESTAMP)
            """))
            db.commit()
            logger.info("✅ 4 usuarios creados")
        
        # 3. Verificar/Crear Clientes
        clientes_check = db.execute(text("SELECT COUNT(*) as count FROM clientes")).fetchone()
        if clientes_check.count == 0:
            logger.info("👤 Creando clientes de prueba...")
            db.execute(text("""
                INSERT INTO clientes (nombre, email, telefono, cups, comercial_id, estado, created_at) VALUES
                ('ACME Corporation', 'contacto@acme.com', '600111222', 'ES0021000000000001JN0F', 2, 'cliente', CURRENT_TIMESTAMP),
                ('Industrias Pérez SL', 'info@perez.com', '600222333', 'ES0022000000000002KP1G', 2, 'cliente', CURRENT_TIMESTAMP),
                ('Cafetería Central', 'cafe@central.com', '600333444', 'ES0023000000000003LQ2H', 3, 'lead', CURRENT_TIMESTAMP)
            """))
            db.commit()
            logger.info("✅ 3 clientes creados")
        
        # 4. Verificar estado de comisiones
        comisiones_check = db.execute(text("SELECT COUNT(*) as count FROM comisiones_generadas")).fetchone()
        logger.info(f"📊 Comisiones existentes: {comisiones_check.count}")
        
        # 5. Mostrar resumen
        logger.info("\n" + "="*60)
        logger.info("✅ DATOS DE PRUEBA LISTOS")
        logger.info("="*60)
        
        stats = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM users WHERE is_active = true) as users_activos,
                (SELECT COUNT(*) FROM clientes) as clientes,
                (SELECT COUNT(*) FROM facturas) as facturas,
                (SELECT COUNT(*) FROM comisiones_generadas) as comisiones
        """)).fetchone()
        
        logger.info(f"👥 Users activos: {stats.users_activos}")
        logger.info(f"👤 Clientes: {stats.clientes}")
        logger.info(f"📄 Facturas: {stats.facturas}")
        logger.info(f"💰 Comisiones: {stats.comisiones}")
        logger.info("="*60)
        
        logger.info("\n🎯 Para probar el panel:")
        logger.info("1. Accede a /gestion/resumen")
        logger.info("2. LocalStorage: setItem('user_role', 'ceo')")
        logger.info("3. Navega entre las tabs: Resumen, Comisiones, Pagos, Colaboradores")
        logger.info("\n💡 Para generar comisiones:")
        logger.info("1. Sube una factura en /wizard/new/step-1-factura")
        logger.info("2. Completa el wizard hasta seleccionar oferta")
        logger.info("3. La comisión se generará automáticamente")
        logger.info("4. Verifica en /gestion/pagos")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_test_data()

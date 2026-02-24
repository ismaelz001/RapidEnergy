"""
Cron Job: Snapshot Mensual Automático
Ejecutar día 1 de cada mes a las 02:00 AM

Configuración Render:
1. Ir a: Dashboard > RapidEnergy > Cron Jobs
2. Crear nuevo Cron Job
3. Comando: python cron_snapshot_mensual.py
4. Schedule: 0 2 1 * * (día 1, a las 02:00 AM)
"""
import os
import sys
from datetime import date

# Asegurarse de que el path incluye el directorio raíz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.conn import SessionLocal
from app.services.snapshot_service import ejecutar_snapshot_mensual
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Ejecutar snapshot mensual automático"""
    logger.info("=" * 80)
    logger.info(f"CRON JOB: Snapshot Mensual - {date.today().isoformat()}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        resultado = ejecutar_snapshot_mensual(db)
        
        if resultado['ok']:
            logger.info(f"✅ Snapshot completado: {resultado['message']}")
            logger.info(f"   Periodo: {resultado['periodo']}")
            logger.info(f"   Snapshots creados: {len(resultado['snapshots_creados'])}")
            for tipo, snapshot_id in resultado['snapshots_creados']:
                logger.info(f"     - {tipo}: ID={snapshot_id}")
        else:
            logger.error(f"❌ Error en snapshot: {resultado['message']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 EXCEPCIÓN NO CONTROLADA: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()
    
    logger.info("=" * 80)
    logger.info("CRON JOB COMPLETADO")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

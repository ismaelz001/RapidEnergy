# PATCHES DE IMPLEMENTACIÓN: VERSIONADO TARIFAS + SOFT DELETE CLIENTES
**Fecha**: 24 Febrero 2026  
**Cambios mínimos - Sin refactor**

---

## 📦 TAREA 1: ADAPTAR COMPARADOR A VERSIONADO DE TARIFAS

### PATCH 1: `app/services/comparador.py` - Añadir import re

**Ubicación**: Línea 1-15 (imports)

**ANTES**:
```python
from datetime import date, datetime
from decimal import Decimal
import json
import logging
from typing import Dict, Any, Optional

from sqlalchemy import inspect, text
from app.exceptions import DomainError
from app.db.models import Comparativa
```

**DESPUÉS**:
```python
from datetime import date, datetime
from decimal import Decimal
import json
import logging
import re  # ⭐ AÑADIDO: usado en _parse_date()
from typing import Dict, Any, Optional

from sqlalchemy import inspect, text
from app.exceptions import DomainError
from app.db.models import Comparativa
```

---

### PATCH 2: `app/services/comparador.py` - Nuevo helper para prefetch de precios

**Ubicación**: Después de `_resolve_energy_prices()` (insertar en línea ~145)

**CÓDIGO NUEVO**:
```python


def _fetch_precios_versiones(db, version_ids: list) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch de precios de energía y potencia para múltiples versiones de tarifas.
    Query única para evitar N+1.
    
    Returns:
        {version_id: {'energia': {'P1': 0.15, 'P2': 0.12, '24H': None}, 
                     'potencia': {'P1': 0.08, 'P2': 0.04}}}
    """
    if not version_ids:
        return {}
    
    result = db.execute(
        text("""
            SELECT 
                tarifa_version_id,
                tipo_periodo,
                periodo_nombre,
                precio_eur_unidad
            FROM tarifa_precios
            WHERE tarifa_version_id = ANY(:version_ids)
        """),
        {"version_ids": version_ids}
    )
    
    rows = result.fetchall()
    precios_map = {}
    
    for row in rows:
        vid = row[0]
        tipo = row[1]  # 'energia' o 'potencia'
        periodo = row[2]  # 'P1', 'P2', '24H', etc.
        precio = float(row[3])
        
        if vid not in precios_map:
            precios_map[vid] = {'energia': {}, 'potencia': {}}
        
        precios_map[vid][tipo][periodo] = precio
    
    logger.info(f"[VERSIONADO] Prefetch precios: {len(precios_map)} versiones")
    return precios_map


def _get_precio_energia(precios_dict: Dict, periodo_idx: int) -> Optional[float]:
    """
    Obtiene precio de energía para periodo (1-6) desde dict de precios.
    Soporta: 24H (plana), P1-P6 (discriminación), fallback P1 (legacy).
    """
    if not precios_dict:
        return None
    
    # Prioridad 1: Tarifa plana 24H
    if '24H' in precios_dict:
        return precios_dict['24H']
    
    # Prioridad 2: Precio específico del periodo
    periodo_key = f'P{periodo_idx}'
    if periodo_key in precios_dict:
        return precios_dict[periodo_key]
    
    # Prioridad 3: Fallback a P1 si solo existe P1
    if periodo_idx > 1 and 'P1' in precios_dict and len(precios_dict) == 1:
        return precios_dict['P1']
    
    return None


def _get_precio_potencia(precios_dict: Dict, periodo_idx: int) -> Optional[float]:
    """Obtiene precio de potencia para periodo (1-2) desde dict."""
    if not precios_dict:
        return None
    periodo_key = f'P{periodo_idx}'
    return precios_dict.get(periodo_key)
```

---

### PATCH 3: `app/services/comparador.py` - Reemplazar query de tarifas

**Ubicación**: Línea ~635 (dentro de `compare_factura`)

**ANTES**:
```python
    result = db.execute(
        text("SELECT * FROM tarifas WHERE atr = :atr"),
        {"atr": atr},
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]
```

**DESPUÉS**:
```python
    # ⭐ VERSIONADO: Query a tarifa_versiones vigentes HOY
    fecha_hoy = date.today()
    
    result = db.execute(
        text("""
            SELECT 
                tv.id as tarifa_version_id,
                tv.nombre,
                tv.comercializadora,
                tv.atr,
                tv.tipo
            FROM tarifa_versiones tv
            WHERE tv.atr = :atr
              AND tv.vigente_desde <= :fecha
              AND (tv.vigente_hasta IS NULL OR tv.vigente_hasta >= :fecha)
            ORDER BY tv.comercializadora, tv.nombre
        """),
        {"atr": atr, "fecha": fecha_hoy}
    )
    
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]
    
    if not tarifas:
        logger.warning(f"[VERSIONADO] No hay tarifas vigentes para {atr}")
        return {
            "ok": False,
            "error_code": "NO_TARIFAS_VIGENTES",
            "message": f"No hay tarifas disponibles para {atr}",
            "factura_id": factura.id,
            "ofertas": []
        }
    
    # Prefetch precios
    version_ids = [t['tarifa_version_id'] for t in tarifas]
    precios_map = _fetch_precios_versiones(db, version_ids)
    
    logger.info(f"[VERSIONADO] {len(tarifas)} tarifas vigentes para {atr}")
```

---

### PATCH 4: `app/services/comparador.py` - Adaptar loop de ofertas (precios energía)

**Ubicación**: Línea ~665 (inicio loop de tarifas)

**ANTES**:
```python
    offers = []
    for tarifa in tarifas:
        # LOGICA DE PRECIOS ENERGÍA DINÁMICA (soporta 2.0TD y 3.0TD)
        # Para 2.0TD: P1, P2, P3
        # Para 3.0TD: P1, P2, P3, P4, P5, P6
        
        # Obtener precios de energía según número de periodos
        precios_energia = []
        for i in range(1, num_periodos_energia + 1):
            precio = _to_float(tarifa.get(f"energia_p{i}_eur_kwh"))
            
            # Fallback: Si P2+ son null, usar P1 (tarifa plana 24h)
            if precio is None and i > 1:
                precio = _to_float(tarifa.get("energia_p1_eur_kwh"))
            
            precios_energia.append(precio)
        
        # Validar que al menos P1 tenga precio
        if precios_energia[0] is None:
            continue  # Tarifa rota sin precio de energía
```

**DESPUÉS**:
```python
    offers = []
    for tarifa in tarifas:
        # ⭐ VERSIONADO: Obtener precios desde tarifa_precios
        version_id = tarifa['tarifa_version_id']
        precios_version = precios_map.get(version_id)
        
        if not precios_version:
            logger.warning(f"[VERSIONADO] Skip version_id={version_id}: sin precios")
            continue
        
        # LOGICA DE PRECIOS ENERGÍA DINÁMICA
        precios_energia = []
        for i in range(1, num_periodos_energia + 1):
            precio = _get_precio_energia(precios_version['energia'], i)
            precios_energia.append(precio)
        
        # Validar que al menos P1 tenga precio
        if precios_energia[0] is None:
            logger.warning(f"[VERSIONADO] Skip {tarifa['nombre']}: sin precio P1")
            continue
```

---

### PATCH 5: `app/services/comparador.py` - Adaptar precios potencia

**Ubicación**: Línea ~688 (precios potencia en loop)

**ANTES**:
```python
        # LOGICA DE PRECIOS POTENCIA DINÁMICA (soporta 2.0TD y 3.0TD)
        # Para 2.0TD: P1, P2 (con fallback BOE 2025 si null)
        # Para 3.0TD: P1, P2, P3, P4, P5, P6 (sin fallback, deben estar completos)
        
        precios_potencia = []
        tiene_precios_potencia = True
        
        for i in range(1, num_periodos_potencia + 1):
            precio = _to_float(tarifa.get(f"potencia_p{i}_eur_kw_dia"))
            
            # Fallback BOE 2025 SOLO para 2.0TD (P1 y P2)
            if precio is None and atr == "2.0TD":
                if i == 1:
                    precio = 0.073777  # BOE 2025 P1
                elif i == 2:
                    precio = 0.001911  # BOE 2025 P2
                tiene_precios_potencia = False  # Marca que usó fallback
            
            precios_potencia.append(precio or 0.0)
```

**DESPUÉS**:
```python
        # LOGICA DE PRECIOS POTENCIA DINÁMICA
        precios_potencia = []
        tiene_precios_potencia = True
        
        for i in range(1, num_periodos_potencia + 1):
            precio = _get_precio_potencia(precios_version['potencia'], i)
            
            # Fallback BOE 2025 SOLO para 2.0TD si no hay precio
            if precio is None and atr == "2.0TD":
                if i == 1:
                    precio = 0.073777  # BOE 2025 P1
                elif i == 2:
                    precio = 0.001911  # BOE 2025 P2
                tiene_precios_potencia = False
            
            precios_potencia.append(precio or 0.0)
```

---

### PATCH 6: `app/services/comparador.py` - Añadir tarifa_version_id al offer

**Ubicación**: Línea ~830 (mapeo de nombres)

**ANTES**:
```python
        # Mapeo de nombres
        tarifa_id = tarifa.get("id") or tarifa.get("tarifa_id")
        provider = _pick_value(
            tarifa,
            ["comercializadora", "provider", "empresa", "brand"],
            "Proveedor genérico",
        )
        plan_name = _pick_value(
            tarifa,
            ["nombre", "plan_name", "plan", "tarifa"],
            "Tarifa 2.0TD",
        )
```

**DESPUÉS**:
```python
        # ⭐ VERSIONADO: Mapeo desde dict de versiones
        tarifa_version_id = version_id
        tarifa_id = tarifa.get("id") or tarifa.get("tarifa_id") or version_id  # Legacy compat
        provider = tarifa.get("comercializadora") or "Proveedor genérico"
        plan_name = tarifa.get("nombre") or "Tarifa 2.0TD"
```

---

**Ubicación**: Línea ~845 (objeto offer)

**ANTES**:
```python
        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
```

**DESPUÉS**:
```python
        offer = {
            "tarifa_id": tarifa_id,
            "tarifa_version_id": tarifa_version_id,  # ⭐ NUEVO
            "provider": provider,
            "plan_name": plan_name,
```

---

### PATCH 7: `app/services/comparador.py` - Modificar _insert_ofertas

**Ubicación**: Línea ~430 (payload en _insert_ofertas)

**ANTES**:
```python
            payload = {
                "comparativa_id": comparativa_id,
                "tarifa_id": tid,
                "coste_estimado": offer.get("estimated_total_periodo"),
                "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
                "ahorro_anual": offer.get("ahorro_anual_equiv"),
                "comision_eur": comision_eur,  # Decimal directo para DB
                "comision_source": comision_source,
                "detalle_json": json.dumps(offer, ensure_ascii=False)
            }
```

**DESPUÉS**:
```python
            payload = {
                "comparativa_id": comparativa_id,
                "tarifa_id": tid,
                "tarifa_version_id": offer.get("tarifa_version_id"),  # ⭐ NUEVO
                "coste_estimado": offer.get("estimated_total_periodo"),
                "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
                "ahorro_anual": offer.get("ahorro_anual_equiv"),
                "comision_eur": comision_eur,
                "comision_source": comision_source,
                "detalle_json": json.dumps(offer, ensure_ascii=False)
            }
```

---

**Ubicación**: Línea ~443 (SQL INSERT)

**ANTES**:
```python
            # SQL explícito con CAST para JSONB en Postgres
            if is_postgres:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, CAST(:detalle_json AS jsonb))
                """)
            else:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, :detalle_json)
                """)
```

**DESPUÉS**:
```python
            # ⭐ VERSIONADO: Incluir tarifa_version_id
            if is_postgres:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, tarifa_version_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :tarifa_version_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, CAST(:detalle_json AS jsonb))
                """)
            else:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, tarifa_version_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :tarifa_version_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, :detalle_json)
                """)
```

---

## 🗑️ TAREA 2: SOFT DELETE DE CLIENTES

### MIGRATION: `migrations/20260224_soft_delete_clientes.sql`

```sql
ALTER TABLE clientes 
ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

CREATE INDEX idx_clientes_deleted_at ON clientes(deleted_at);

COMMENT ON COLUMN clientes.deleted_at IS 'Soft delete: NULL = activo, NOT NULL = eliminado';
```

---

### PATCH 8: `app/routes/clientes.py` - Soft delete endpoint

**Ubicación**: Línea 160 (función delete_cliente)

**ANTES**:
```python
@router.delete("/{cliente_id}")
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    try:
        db.delete(cliente)
        db.commit()
        return {"message": "Cliente eliminado correctamente", "id": cliente_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
```

**DESPUÉS**:
```python
@router.delete("/{cliente_id}")
def delete_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Soft delete: marca cliente como eliminado y anonimiza datos.
    Solo dev/ceo pueden ejecutar.
    """
    # Validar permisos
    if not current_user.is_dev() and not current_user.is_ceo():
        raise HTTPException(
            status_code=403,
            detail="Solo dev/ceo pueden eliminar clientes"
        )
    
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.deleted_at.is_(None)  # Solo clientes activos
    ).first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o ya eliminado")
    
    # CEO solo borra de su company
    if current_user.is_ceo():
        if cliente.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No puedes eliminar clientes de otras empresas")
    
    try:
        # Soft delete + anonimización
        cliente.deleted_at = datetime.utcnow()
        cliente.nombre = f"[ELIMINADO-{cliente_id}]"
        cliente.email = f"deleted_{cliente_id}@anonimo.local"
        cliente.telefono = None
        cliente.dni = None
        
        db.commit()
        
        logger.info(f"[SOFT DELETE] Cliente {cliente_id} eliminado por user {current_user.id}")
        
        return {
            "message": "Cliente eliminado correctamente",
            "id": cliente_id,
            "soft_delete": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"[SOFT DELETE] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
```

**⚠️ AÑADIR IMPORTS** al inicio del archivo:

```python
# Añadir en línea ~5
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
```

---

### PATCH 9: `app/routes/clientes.py` - Filtrar clientes eliminados en GET

**Ubicación**: Línea ~92 (función get_clientes)

**ANTES**:
```python
@router.get("/", response_model=List[ClienteDetail])
def get_clientes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    query = db.query(Cliente).options(joinedload(Cliente.facturas))
```

**DESPUÉS**:
```python
@router.get("/", response_model=List[ClienteDetail])
def get_clientes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # ⭐ SOFT DELETE: Filtrar eliminados
    query = db.query(Cliente).options(joinedload(Cliente.facturas)).filter(
        Cliente.deleted_at.is_(None)
    )
```

---

**Ubicación**: Línea ~123 (función get_cliente individual)

**ANTES**:
```python
@router.get("/{cliente_id}", response_model=ClienteDetail)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).options(joinedload(Cliente.facturas)).filter(Cliente.id == cliente_id).first()
```

**DESPUÉS**:
```python
@router.get("/{cliente_id}", response_model=ClienteDetail)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    # ⭐ SOFT DELETE: Filtrar eliminados
    cliente = db.query(Cliente).options(joinedload(Cliente.facturas)).filter(
        Cliente.id == cliente_id,
        Cliente.deleted_at.is_(None)
    ).first()
```

---

### PATCH 10: `app/clientes/ClienteDeleteButton.jsx` (NUEVO - Client Component)

**Archivo completo**:

```jsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ClienteDeleteButton({ clienteId, clienteNombre }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/clientes/${clienteId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Error al eliminar cliente");
      }

      alert("✅ Cliente eliminado correctamente");
      router.refresh();
      setIsModalOpen(false);
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className="text-red-400 hover:text-red-300 transition-colors"
        title="Eliminar cliente"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      </button>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0F172A] rounded-[16px] p-6 max-w-md w-full mx-4 border border-white/10">
            <h3 className="text-lg font-semibold text-white mb-2">
              ¿Eliminar cliente?
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              Estás a punto de eliminar a{" "}
              <span className="text-white font-medium">
                {clienteNombre || `Cliente #${clienteId}`}
              </span>
              .
            </p>
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 mb-4">
              <p className="text-xs text-yellow-300">
                ⚠️ Los datos se anonimizarán. Las facturas y casos permanecen
                en el sistema.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setIsModalOpen(false)}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {isDeleting ? "Eliminando..." : "Eliminar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

---

### PATCH 11: `app/clientes/page.jsx` - Integrar botón delete

**Ubicación**: Línea 1 (imports)

**ANTES**:
```jsx
import Link from "next/link";
import { listClientes } from "@/lib/apiClient";

export const dynamic = "force-dynamic";
```

**DESPUÉS**:
```jsx
import Link from "next/link";
import { listClientes } from "@/lib/apiClient";
import ClienteDeleteButton from "./ClienteDeleteButton";

export const dynamic = "force-dynamic";
```

---

**Ubicación**: Línea 30 (thead)

**ANTES**:
```jsx
            <tr className="border-b border-white/8 text-[#F1F5F9]">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">Nombre</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Telefono</th>
              <th className="py-2 text-left">Estado</th>
              <th className="py-2 text-left">Facturas</th>
              <th className="py-2 text-left"></th>
            </tr>
```

**DESPUÉS**:
```jsx
            <tr className="border-b border-white/8 text-[#F1F5F9]">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">Nombre</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Telefono</th>
              <th className="py-2 text-left">Estado</th>
              <th className="py-2 text-left">Facturas</th>
              <th className="py-2 text-left">Acciones</th>
            </tr>
```

---

**Ubicación**: Línea 57 (columna acciones en tbody)

**ANTES**:
```jsx
                  <td className="py-3 text-right">
                    <Link href={`/clientes/${c.id}`} className="text-emerald-400 hover:text-emerald-300">
                      Ver detalle
                    </Link>
                  </td>
```

**DESPUÉS**:
```jsx
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <Link href={`/clientes/${c.id}`} className="text-emerald-400 hover:text-emerald-300">
                        Ver detalle
                      </Link>
                      <ClienteDeleteButton clienteId={c.id} clienteNombre={c.nombre} />
                    </div>
                  </td>
```

---

## ✅ CHECKLIST DE PRUEBAS

### TAREA 1: Versionado de Tarifas

#### Test 1: Crear tarifa versionada
```sql
-- Insertar versión de tarifa
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, tipo, vigente_desde, version)
VALUES ('Plan Test Versionado', 'Test SA', '2.0TD', 'fija', '2026-02-01', 1)
RETURNING id;
-- Anotar ID (ej: 999)

-- Insertar precios energía (discriminación horaria)
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES 
(999, 'energia', 'P1', 0.150),
(999, 'energia', 'P2', 0.120),
(999, 'energia', 'P3', 0.095);

-- Insertar precios potencia
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES 
(999, 'potencia', 'P1', 0.085),
(999, 'potencia', 'P2', 0.042);
```

#### Test 2: Comparar factura con tarifa versionada
```bash
curl -X POST "http://localhost:8000/comparar/facturas/321" \
  -H "Authorization: Bearer ${TOKEN}"

# Verificar:
# - offers[0].tarifa_version_id existe y es 999
# - offers[0].estimated_total se calculó con precios correctos
# - Log: "[VERSIONADO] X tarifas vigentes"
```

#### Test 3: Verificar persistencia
```sql
SELECT 
    oc.id,
    oc.tarifa_version_id,
    tv.nombre,
    tv.comercializadora,
    oc.coste_estimado
FROM ofertas_calculadas oc
LEFT JOIN tarifa_versiones tv ON tv.id = oc.tarifa_version_id
WHERE oc.comparativa_id = (SELECT MAX(id) FROM comparativas)
ORDER BY oc.coste_estimado;

-- Esperado: tarifa_version_id = 999 en ofertas nuevas
```

#### Test 4: Tarifa 24H (plana)
```sql
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, vigente_desde, version)
VALUES ('Plan 24H Flat', 'Test SA', '2.0TD', '2026-02-01', 1)
RETURNING id;
-- ID = 1000

INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES (1000, 'energia', '24H', 0.135);

-- Comparar factura → debe usar 0.135 para P1, P2, P3
```

---

### TAREA 2: Soft Delete Clientes

#### Test 5: Aplicar migración
```bash
psql -U usuario -d mecaenergy -f migrations/20260224_soft_delete_clientes.sql

# Verificar columna
\d clientes
# Esperado: deleted_at | timestamp with time zone | default NULL
```

#### Test 6: Soft delete desde API (dev)
```bash
# Login como DEV
curl -X DELETE "http://localhost:8000/api/clientes/555" \
  -H "Authorization: Bearer ${DEV_TOKEN}"

# Verificar respuesta:
# {"message": "Cliente eliminado correctamente", "id": 555, "soft_delete": true}

# Verificar en DB
SELECT id, nombre, email, deleted_at FROM clientes WHERE id = 555;
# Esperado: deleted_at NOT NULL, nombre = "[ELIMINADO-555]"
```

#### Test 7: Cliente eliminado no aparece en GET
```bash
curl "http://localhost:8000/api/clientes" \
  -H "Authorization: Bearer ${TOKEN}"

# Verificar: cliente 555 NO está en la lista
```

#### Test 8: CEO solo borra de su company
```bash
# Login como CEO de company_id=1
curl -X DELETE "http://localhost:8000/api/clientes/666" \
  -H "Authorization: Bearer ${CEO_TOKEN}"

# Si cliente 666 tiene company_id=2:
# Esperado: HTTP 403 "No puedes eliminar clientes de otras empresas"
```

#### Test 9: COMERCIAL no puede borrar
```bash
# Login como COMERCIAL
curl -X DELETE "http://localhost:8000/api/clientes/777" \
  -H "Authorization: Bearer ${COMERCIAL_TOKEN}"

# Esperado: HTTP 403 "Solo dev/ceo pueden eliminar clientes"
```

#### Test 10: Frontend - Botón eliminar
```
1. Login en UI como CEO
2. Ir a /clientes
3. Buscar cliente con datos
4. Pulsar icono basura (🗑️)
5. Confirmar en modal
6. Verificar: alert "✅ Cliente eliminado correctamente"
7. Verificar: cliente desaparece de la tabla
8. Recargar página → cliente sigue sin aparecer
```

---

## 📊 RESUMEN DE CAMBIOS

### TAREA 1: Versionado de Tarifas
- **Archivos modificados**: 1 (`app/services/comparador.py`)
- **Líneas modificadas**: ~80
- **Líneas nuevas**: ~90 (3 helpers)
- **Queries nuevas**: 2 (tarifa_versiones + tarifa_precios)
- **Compatibilidad**: ✅ Mantiene tarifa_id legacy
- **Riesgo**: BAJO (cambio aislado en comparador)

### TAREA 2: Soft Delete Clientes
- **Archivos nuevos**: 1 (`ClienteDeleteButton.jsx`)
- **Archivos modificados**: 2 (`clientes.py`, `clientes/page.jsx`)
- **Migración SQL**: 1 (añade columna deleted_at)
- **Líneas modificadas backend**: ~50
- **Líneas nuevas frontend**: ~100
- **Estrategia**: SOFT DELETE (preserva FKs)
- **Riesgo**: BAJO (sin romper relaciones DB)

---

**FIN DE PATCHES**

Todos los cambios son copy-paste ready. ¿Necesitas aclaraciones?

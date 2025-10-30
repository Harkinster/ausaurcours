from __future__ import annotations
from typing import Any, Optional
from sqlalchemy.orm import Session
from .models import AuditLog

def log_action(
    db: Session,
    *,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: str,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    """Insère une ligne dans audit_logs."""
    print(f"[AUDIT] Tentative d'enregistrement d'une action: {action} sur {entity_type} {entity_id} par l'utilisateur {user_id}")
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta or {},
        )
        print(f"[AUDIT] Objet AuditLog créé: {audit_log}")
        
        db.add(audit_log)
        db.commit()
        print("[AUDIT] Action enregistrée avec succès")
    except Exception as e:
        print(f"[AUDIT] Erreur lors de l'enregistrement de l'action: {str(e)}")
        db.rollback()
        raise

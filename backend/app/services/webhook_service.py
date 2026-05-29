"""
Webhook Service
Delivers signed HTTP POST payloads to registered webhook URLs.

Delivery is best-effort fire-and-forget (no retry queue yet).
The last HTTP status code is recorded on the Webhook row so teams
can see failed deliveries in the dashboard.

Payload format
--------------
{
  "event":      "schema.enrichment.complete",
  "company_id": "...",
  "data":       { ... event-specific fields ... },
  "timestamp":  "2026-05-28T12:00:00Z"
}

Signature
---------
  X-Vernql-Signature: sha256=<hex>
  HMAC-SHA256(signing_secret, raw_body_bytes)
"""
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
import structlog
from sqlalchemy.orm import Session

from app.models.webhook import Webhook

logger = structlog.get_logger()

_DELIVERY_TIMEOUT = 10  # seconds


class WebhookService:

    # ------------------------------------------------------------------ #
    #  CRUD                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create(
        db: Session,
        company_id: UUID,
        url: str,
        events: List[str],
    ) -> tuple[Webhook, str]:
        """
        Register a new webhook.

        Returns (Webhook, raw_signing_secret). The secret is shown once;
        store it securely on your end.
        """
        raw_secret = secrets.token_hex(32)

        webhook = Webhook(
            company_id     = company_id,
            url            = url,
            events         = events,
            signing_secret = raw_secret,
            is_active      = True,
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        return webhook, raw_secret

    @staticmethod
    def list(db: Session, company_id: UUID) -> List[Webhook]:
        return (
            db.query(Webhook)
            .filter(Webhook.company_id == company_id, Webhook.is_active == True)
            .order_by(Webhook.created_at.desc())
            .all()
        )

    @staticmethod
    def get(db: Session, webhook_id: UUID, company_id: UUID) -> Optional[Webhook]:
        return db.query(Webhook).filter(
            Webhook.id         == webhook_id,
            Webhook.company_id == company_id,
        ).first()

    @staticmethod
    def delete(db: Session, webhook_id: UUID, company_id: UUID) -> bool:
        webhook = WebhookService.get(db, webhook_id, company_id)
        if not webhook:
            return False
        webhook.is_active = False
        db.commit()
        return True

    # ------------------------------------------------------------------ #
    #  Delivery                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def deliver_event(
        db: Session,
        company_id: UUID,
        event: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Find all active webhooks subscribed to `event` and POST to each.
        Errors are logged but never raised — delivery is best-effort.
        """
        webhooks = (
            db.query(Webhook)
            .filter(
                Webhook.company_id == company_id,
                Webhook.is_active  == True,
            )
            .all()
        )

        subscribed = [w for w in webhooks if event in (w.events or [])]
        if not subscribed:
            return

        payload = {
            "event":      event,
            "company_id": str(company_id),
            "data":       data,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }
        raw_body = json.dumps(payload, default=str).encode()

        async with httpx.AsyncClient(timeout=_DELIVERY_TIMEOUT) as client:
            for webhook in subscribed:
                await WebhookService._post(client, db, webhook, raw_body)

    @staticmethod
    async def _post(
        client: httpx.AsyncClient,
        db: Session,
        webhook: Webhook,
        raw_body: bytes,
    ) -> None:
        headers = {"Content-Type": "application/json"}

        if webhook.signing_secret:
            sig = hmac.new(
                webhook.signing_secret.encode(),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Vernql-Signature"] = f"sha256={sig}"

        status_code: Optional[int] = None
        try:
            response = await client.post(
                webhook.url,
                content=raw_body,
                headers=headers,
            )
            status_code = response.status_code
            logger.info(
                "webhook_delivered",
                webhook_id=str(webhook.id),
                url=webhook.url,
                status_code=status_code,
            )
        except Exception as exc:
            logger.error(
                "webhook_delivery_failed",
                webhook_id=str(webhook.id),
                url=webhook.url,
                error=str(exc),
            )
        finally:
            # Record delivery attempt metadata
            try:
                webhook.last_triggered_at = datetime.now(timezone.utc)
                if status_code is not None:
                    webhook.last_status_code = status_code
                db.commit()
            except Exception:
                pass

"""
Webhook Management Endpoints
Register, list, and delete webhook endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import CurrentCompanyEither
from app.models.webhook import WEBHOOK_EVENTS
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class WebhookCreateRequest(BaseModel):
    url: str = Field(
        ...,
        description="HTTPS URL that will receive POST payloads",
        max_length=2048,
    )
    events: List[str] = Field(
        ...,
        description=(
            f"Event names to subscribe to. "
            f"Supported: {WEBHOOK_EVENTS}"
        ),
        min_length=1,
    )


class WebhookCreateResponse(BaseModel):
    id:             UUID
    url:            str
    events:         List[str]
    signing_secret: str = Field(
        ...,
        description="HMAC-SHA256 signing secret. Shown once — store it securely.",
    )
    is_active:      bool
    created_at:     datetime


class WebhookResponse(BaseModel):
    id:                UUID
    url:               str
    events:            List[str]
    is_active:         bool
    created_at:        datetime
    last_triggered_at: Optional[datetime]
    last_status_code:  Optional[int]

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    webhooks: List[WebhookResponse]
    total:    int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=WebhookCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new webhook",
)
async def create_webhook(
    body: WebhookCreateRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """
    Register a URL to receive Vernql event notifications.

    ## Supported events
    - `schema.enrichment.complete` — fired when AI enrichment finishes successfully
    - `schema.enrichment.failed`   — fired when AI enrichment fails

    ## Payload
    ```json
    {
      "event":      "schema.enrichment.complete",
      "company_id": "...",
      "data":       { "schema_id": "...", "schema_name": "..." },
      "timestamp":  "2026-05-28T12:00:00Z"
    }
    ```

    ## Signature verification
    Every delivery includes an `X-Vernql-Signature: sha256=<hex>` header.
    Compute `HMAC-SHA256(signing_secret, raw_body_bytes)` and compare.

    **The signing secret is only shown once — save it now.**
    """
    # Validate event names
    invalid = [e for e in body.events if e not in WEBHOOK_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown event(s): {invalid}. Supported: {WEBHOOK_EVENTS}",
        )

    webhook, raw_secret = WebhookService.create(
        db=db,
        company_id=company.id,
        url=body.url,
        events=body.events,
    )

    return WebhookCreateResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        signing_secret=raw_secret,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
    )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List registered webhooks",
)
async def list_webhooks(
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """List all active webhooks for the authenticated company."""
    webhooks = WebhookService.list(db=db, company_id=company.id)
    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(w) for w in webhooks],
        total=len(webhooks),
    )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook",
)
async def delete_webhook(
    webhook_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """Deactivate (soft-delete) a registered webhook."""
    deleted = WebhookService.delete(
        db=db,
        webhook_id=webhook_id,
        company_id=company.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    return None

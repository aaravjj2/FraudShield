"""FraudShield — Webhook configuration for fraud alerts."""

import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

WEBHOOK_FILE = Path(__file__).parent.parent / "data" / "webhooks.json"


class WebhookConfig(BaseModel):
    """Webhook configuration for fraud alerts."""
    url: str = Field(..., description="Webhook URL to receive fraud alerts")
    secret: Optional[str] = Field(None, description="Secret for webhook signature verification")
    enabled: bool = Field(True, description="Whether the webhook is active")
    min_probability: float = Field(
        default=0.5, ge=0, le=1,
        description="Minimum fraud probability to trigger webhook"
    )


class WebhookPayload(BaseModel):
    """Payload sent to webhook on fraud detection."""
    event: str = "fraud_detected"
    transaction_id: int
    amount: float
    fraud_probability: float
    timestamp: str


def load_webhooks() -> list[WebhookConfig]:
    """Load webhook configurations from file."""
    if not WEBHOOK_FILE.exists():
        return []
    try:
        data = json.loads(WEBHOOK_FILE.read_text())
        return [WebhookConfig(**w) for w in data]
    except (json.JSONDecodeError, Exception):
        return []


def save_webhooks(webhooks: list[WebhookConfig]) -> None:
    """Save webhook configurations to file."""
    WEBHOOK_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEBHOOK_FILE.write_text(
        json.dumps([w.model_dump() for w in webhooks], indent=2)
    )


async def notify_webhooks(
    transaction_id: int,
    amount: float,
    fraud_probability: float,
    timestamp: str,
) -> int:
    """Send fraud alert to all configured webhooks. Returns count notified."""
    import httpx

    webhooks = load_webhooks()
    active = [w for w in webhooks if w.enabled and fraud_probability >= w.min_probability]
    if not active:
        return 0

    payload = WebhookPayload(
        transaction_id=transaction_id,
        amount=amount,
        fraud_probability=fraud_probability,
        timestamp=timestamp,
    )

    notified = 0
    async with httpx.AsyncClient(timeout=5.0) as client:
        for webhook in active:
            try:
                headers = {"Content-Type": "application/json"}
                if webhook.secret:
                    import hashlib, hmac
                    body = payload.model_dump_json()
                    sig = hmac.new(
                        webhook.secret.encode(), body.encode(), hashlib.sha256
                    ).hexdigest()
                    headers["X-FraudShield-Signature"] = f"sha256={sig}"
                resp = await client.post(webhook.url, json=payload.model_dump(), headers=headers)
                if resp.status_code < 400:
                    notified += 1
                    logger.info(f"Webhook notified: {webhook.url}")
                else:
                    logger.warning(f"Webhook failed: {webhook.url} status={resp.status_code}")
            except Exception as e:
                logger.warning(f"Webhook error: {webhook.url} error={e}")

    return notified

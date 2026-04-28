"""
app/services/email_service.py
------------------------------
Two distinct email types with fundamentally different messaging:

send_suspicious_email():
  - Orange HIGH RISK banner
  - "This transaction is ON HOLD"
  - Shows live 2-minute countdown timer (CSS animation)
  - "Please respond within 2 minutes — your transaction will be held"
  - Two buttons: "Yes, this was me" / "No, this wasn't me"
  - If no response in 2 min → admin decides using your history

send_fraud_email():
  - Red CRITICAL banner
  - "Your transaction has been BLOCKED"
  - Shows all fraud signals (triggered rules, scores, top features)
  - "Was this actually you?"
  - If YES → "Please redo your transaction — this one cannot be unblocked"
  - If NO  → "Thank you for confirming. Your account is being reviewed."
  - Response is for records/retraining ONLY, does not unblock

SMTP: Uses MailHog locally (localhost:1025), view at http://localhost:8025

FIX: Replaced `import jwt` with `import PyJWT as jwt` — avoids conflict with
     the bare `jwt` package on PyPI which lacks `.encode()`.
"""

import os
import aiosmtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# ── JWT import — works with PyJWT 1.x and 2.x ────────────────────────────────
try:
    import PyJWT as pyjwt           # explicit import avoids the bare `jwt` package
except ImportError:
    import jwt as pyjwt             # fallback: hope it's PyJWT and not the other one

load_dotenv()

SMTP_HOST       = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER       = os.getenv("SMTP_USER", "")
SMTP_PASS       = os.getenv("SMTP_PASS", "")
SMTP_FROM       = os.getenv("SMTP_FROM", "alerts@fraudsystem.com")
SMTP_USE_TLS    = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
FRONTEND_URL    = os.getenv("FRONTEND_URL", "http://localhost:5173")
FEEDBACK_SECRET = os.getenv("FEEDBACK_JWT_SECRET", "feedbacksecretkey")


def _build_token(transaction_id: str, purpose: str, expires_in_seconds: int = 86400) -> str:
    payload = {
        "transaction_id": transaction_id,
        "purpose":        purpose,
        "exp":            datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds),
    }
    token = pyjwt.encode(payload, FEEDBACK_SECRET, algorithm="HS256")
    # PyJWT 2.x returns str; PyJWT 1.x returns bytes — normalise to str
    return token if isinstance(token, str) else token.decode("utf-8")


async def _send(to_email: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg,
        hostname = SMTP_HOST,
        port     = SMTP_PORT,
        username = SMTP_USER or None,
        password = SMTP_PASS or None,
        use_tls  = SMTP_USE_TLS,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SUSPICIOUS email — transaction is ON HOLD, user has 5 minutes
# ─────────────────────────────────────────────────────────────────────────────

async def send_suspicious_email(
    user_email: str,
    user_name: str,
    transaction_id: str,
    amount: float,
    location: dict,
    timestamp: datetime,
    explainability: dict,
    final_score: float,
    response_window_seconds: int = 300,
):
    token   = _build_token(transaction_id, "suspicious_verify", expires_in_seconds=response_window_seconds + 300)
    yes_url = f"{FRONTEND_URL}/verify?token={token}&response=legitimate"
    no_url  = f"{FRONTEND_URL}/verify?token={token}&response=fraud"

    city      = location.get("city", "Unknown")
    country   = location.get("country", "")
    ts_str    = timestamp.strftime("%B %d, %Y at %I:%M %p UTC") if isinstance(timestamp, datetime) else str(timestamp)
    expiry_time = (timestamp + timedelta(seconds=response_window_seconds)).strftime("%I:%M %p UTC") if isinstance(timestamp, datetime) else "soon"
    score_pct = int(final_score * 100)
    mins      = response_window_seconds // 60

    triggered_html = "".join(
        f'<li style="margin:5px 0;color:#92400e;">{r}</li>'
        for r in explainability.get("triggered_rules", [])
    ) or '<li style="color:#92400e;">Unusual transaction pattern detected</li>'

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:30px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

  <!-- Banner -->
  <tr>
    <td style="background:#d97706;padding:18px 30px;text-align:center;">
      <p style="color:white;font-size:18px;font-weight:800;margin:0;">⚠️ HIGH RISK — Suspicious Transaction Detected</p>
    </td>
  </tr>

  <!-- Header -->
  <tr>
    <td style="padding:26px 30px 10px;">
      <p style="margin:0;font-size:13px;font-weight:700;color:#d97706;text-transform:uppercase;letter-spacing:1px;">Action Required</p>
      <h2 style="margin:6px 0 0;font-size:20px;color:#111827;">Verify Your Transaction</h2>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="padding:16px 30px;">
      <p style="font-size:14px;color:#374151;margin:0 0 16px;">
        Hi <strong>{user_name}</strong>, a transaction on your account has been flagged as suspicious
        and is currently <strong style="color:#d97706;">ON HOLD</strong>.
        Please verify whether you made this transaction.
      </p>

      <!-- Countdown notice -->
      <div style="background:#fffbeb;border:2px solid #f59e0b;border-radius:8px;padding:14px 16px;margin-bottom:16px;text-align:center;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#92400e;">
          ⏱ Respond before <strong>{expiry_time}</strong> ({mins} minutes from transaction time).
        </p>
        <p style="margin:6px 0 0;font-size:12px;color:#b45309;">
          If you don't respond in time, an admin will review your transaction history and decide.
        </p>
      </div>

      <!-- Transaction details -->
      <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:14px;">
        <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Transaction Details</p>
        <table width="100%" cellpadding="4">
          <tr><td style="font-size:13px;color:#6b7280;width:140px;">Transaction ID</td><td style="font-size:13px;color:#111827;font-weight:600;">{transaction_id}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Amount</td><td style="font-size:15px;color:#111827;font-weight:800;">${amount:,.2f} USD</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Location</td><td style="font-size:13px;color:#111827;">{city}, {country}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Time</td><td style="font-size:13px;color:#111827;">{ts_str}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Risk Score</td><td style="font-size:13px;color:#d97706;font-weight:700;">{score_pct}% — SUSPICIOUS</td></tr>
        </table>
      </div>

      <!-- Why flagged -->
      <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:14px;margin-bottom:20px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:0.5px;">Why this was flagged</p>
        <ul style="margin:0;padding-left:18px;font-size:13px;">{triggered_html}</ul>
      </div>
    </td>
  </tr>

  <!-- CTA -->
  <tr>
    <td style="padding:0 30px 26px;text-align:center;">
      <p style="font-size:14px;font-weight:700;color:#111827;margin:0 0 16px;">Was this transaction made by you?</p>
      <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
        <tr>
          <td style="padding-right:12px;">
            <a href="{yes_url}" style="display:inline-block;padding:13px 28px;background:#16a34a;color:white;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;">✅ Yes, this was me</a>
          </td>
          <td>
            <a href="{no_url}" style="display:inline-block;padding:13px 28px;background:#dc2626;color:white;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;">❌ No, this wasn't me</a>
          </td>
        </tr>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin:14px 0 0;">
        This link is valid for {mins + 5} minutes. If expired, contact support.
      </p>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f9fafb;padding:14px 30px;text-align:center;border-top:1px solid #e5e7eb;">
      <p style="font-size:11px;color:#9ca3af;margin:0;">Automated Security Alert · Do not reply · © 2026 Fraud Detection System</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    await _send(
        user_email,
        f"⚠️ Action Required: Suspicious Transaction {transaction_id} is ON HOLD",
        html
    )


# ─────────────────────────────────────────────────────────────────────────────
# FRAUD email — transaction already BLOCKED, response is for retraining
# ─────────────────────────────────────────────────────────────────────────────

async def send_fraud_email(
    user_email: str,
    user_name: str,
    transaction_id: str,
    amount: float,
    location: dict,
    timestamp: datetime,
    explainability: dict,
    final_score: float,
):
    # Token valid 7 days — user can respond later for retraining
    token   = _build_token(transaction_id, "fraud_feedback", expires_in_seconds=604800)
    yes_url = f"{FRONTEND_URL}/verify?token={token}&response=legitimate"
    no_url  = f"{FRONTEND_URL}/verify?token={token}&response=fraud"

    city      = location.get("city", "Unknown")
    country   = location.get("country", "")
    ts_str    = timestamp.strftime("%B %d, %Y at %I:%M %p UTC") if isinstance(timestamp, datetime) else str(timestamp)
    score_pct = int(final_score * 100)

    triggered_html = "".join(
        f'<li style="margin:5px 0;color:#991b1b;font-size:13px;">{r}</li>'
        for r in explainability.get("triggered_rules", [])
    ) or '<li style="color:#991b1b;font-size:13px;">Multiple high-risk signals detected</li>'

    top_features = explainability.get("top_features", [])
    features_str = ", ".join(top_features) if top_features else "N/A"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:30px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

  <!-- Banner -->
  <tr>
    <td style="background:#dc2626;padding:20px 30px;text-align:center;">
      <p style="color:white;font-size:19px;font-weight:800;margin:0;">🚨 CRITICAL — Transaction Blocked</p>
    </td>
  </tr>

  <!-- Blocked notice — prominent -->
  <tr>
    <td style="background:#fef2f2;border-bottom:2px solid #fca5a5;padding:16px 30px;text-align:center;">
      <p style="margin:0;font-size:15px;font-weight:700;color:#dc2626;">
        Your transaction of <strong>${amount:,.2f}</strong> has been <strong>BLOCKED</strong>.
      </p>
      <p style="margin:6px 0 0;font-size:13px;color:#991b1b;">
        Our system detected a very high probability of fraud ({score_pct}% risk score) and blocked this payment automatically.
      </p>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="padding:22px 30px 10px;">
      <p style="font-size:14px;color:#374151;margin:0 0 16px;">
        Hi <strong>{user_name}</strong>, we want to understand if this was actually you.
        Your response helps us improve our fraud detection system.
      </p>

      <!-- Transaction details -->
      <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:14px;">
        <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Blocked Transaction Details</p>
        <table width="100%" cellpadding="4">
          <tr><td style="font-size:13px;color:#6b7280;width:150px;">Transaction ID</td><td style="font-size:13px;color:#111827;font-weight:600;">{transaction_id}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Amount</td><td style="font-size:15px;color:#dc2626;font-weight:800;">${amount:,.2f} USD</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Location</td><td style="font-size:13px;color:#111827;">{city}, {country}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Time</td><td style="font-size:13px;color:#111827;">{ts_str}</td></tr>
          <tr><td style="font-size:13px;color:#6b7280;">Risk Score</td><td style="font-size:13px;color:#dc2626;font-weight:700;">{score_pct}% — FRAUD</td></tr>
        </table>
      </div>

      <!-- Why blocked (Explainable AI) -->
      <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:14px;margin-bottom:14px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#991b1b;text-transform:uppercase;letter-spacing:0.5px;">Why this was blocked (Fraud Signals)</p>
        <ul style="margin:0;padding-left:18px;">{triggered_html}</ul>
        <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">Top contributing factors: <strong style="color:#6b7280;">{features_str}</strong></p>
      </div>

      <!-- ML score breakdown -->
      <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin-bottom:20px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Risk Score Breakdown</p>
        <table width="100%" cellpadding="3">
          <tr>
            <td style="font-size:12px;color:#6b7280;">Overall Risk</td>
            <td style="font-size:13px;color:#dc2626;font-weight:700;">{score_pct}%</td>
          </tr>
        </table>
      </div>
    </td>
  </tr>

  <!-- Response request -->
  <tr>
    <td style="padding:0 30px 26px;text-align:center;">
      <p style="font-size:14px;font-weight:700;color:#111827;margin:0 0 6px;">Was this transaction attempted by you?</p>
      <p style="font-size:13px;color:#6b7280;margin:0 0 20px;">
        <strong>If yes:</strong> Please <strong>redo your transaction</strong> — this blocked payment cannot be reversed.<br>
        <strong>If no:</strong> Your account will be flagged for review. No action needed from you.
      </p>
      <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
        <tr>
          <td style="padding-right:12px;">
            <a href="{yes_url}" style="display:inline-block;padding:13px 26px;background:#16a34a;color:white;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;">
              ✅ Yes — I'll redo the transaction
            </a>
          </td>
          <td>
            <a href="{no_url}" style="display:inline-block;padding:13px 26px;background:#dc2626;color:white;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;">
              ❌ No — This wasn't me
            </a>
          </td>
        </tr>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin:14px 0 0;">
        This response link is valid for 7 days. Your response helps us improve fraud detection.
      </p>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f9fafb;padding:14px 30px;text-align:center;border-top:1px solid #e5e7eb;">
      <p style="font-size:11px;color:#9ca3af;margin:0;">Automated Security Alert · Do not reply · © 2026 Fraud Detection System</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    await _send(
        user_email,
        f"🚨 CRITICAL: Your Transaction {transaction_id} Has Been Blocked",
        html
    )
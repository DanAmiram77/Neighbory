import resend
from app.core.config import settings


def send_parent_approval_email(
    parent_email: str,
    child_name: str,
    child_username: str,
    approval_code: str,
) -> bool:
    if not settings.RESEND_API_KEY:
        print(f"[EMAIL SKIPPED] Approval code for {child_username}: {approval_code}")
        return False

    resend.api_key = settings.RESEND_API_KEY

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl; text-align: right;">
        <div style="background: #A78BFA; padding: 32px; border-radius: 16px 16px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Neighbory 🏪</h1>
            <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0;">השוק הקהילתי לבני נוער</p>
        </div>
        <div style="background: white; padding: 32px; border: 3px solid #1F2937; border-top: none; border-radius: 0 0 16px 16px;">
            <h2 style="color: #1F2937; margin-top: 0;">שלום,</h2>
            <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">
                <strong>{child_name}</strong> (@{child_username}) נרשם/ה ל-Neighbory וביקש/ה את אישורך.
            </p>
            <p style="color: #4B5563; font-size: 16px;">להשלמת ההרשמה, היכנס/י לאפליקציה והזן/י את קוד האישור:</p>
            <div style="background: #FEF3C7; border: 3px solid #1F2937; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                <div style="font-size: 36px; font-weight: 900; letter-spacing: 8px; color: #1F2937;">{approval_code}</div>
            </div>
            <p style="color: #9CA3AF; font-size: 13px;">אם לא הכרת את ההרשמה הזו, ניתן להתעלם מהמייל.</p>
        </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": parent_email,
            "subject": f"✅ אישור חשבון Neighbory עבור {child_name}",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {parent_email}: {e}")
        return False

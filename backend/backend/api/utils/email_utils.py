from django.core.mail import send_mail
import resend
from django.conf import settings
from zoneinfo import ZoneInfo

resend.api_key = settings.RESEND_API_KEY


def send_notification_email(subject, body, to_email):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)


def send_defense_scheduled_email(schedule_instance):
    group = schedule_instance.group
    manila_tz = ZoneInfo("Asia/Manila")
    # Convert start time
    start_time_manila = schedule_instance.start_at.astimezone(manila_tz)
    start_time = start_time_manila.strftime("%B %d, %Y at %I:%M %p")

    # Convert end time
    end_time_manila = schedule_instance.end_at.astimezone(manila_tz)

    # Calculate duration
    duration = str(end_time_manila - start_time_manila)
    # Collect unique emails
    recipients = list(set(
        [m.email for m in group.members.all()] +
        ([group.adviser.email] if group.adviser else []) +
        [p.email for p in group.panels.all()]
    ))
    recipients = [email for email in recipients if email]

    if not recipients:
        print("No recipients found — skipping email.")
        return

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2c3e50;">🛡️ Defense Schedule Confirmed!</h2>

            <p>Hello!</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3><strong>Group:</strong> {group.name}</h3>
                <p><strong>Date & Time:</strong> {start_time}</p>
                <p><strong>Duration:</strong> {duration}</p>
                <p><strong>Topic:</strong> {getattr(group, 'proposed_topic_title', 'Thesis Defense')}</p>
                <p><strong>Venue:</strong> {getattr(schedule_instance, 'location', 'To be announced')}</p>
            </div>

            <p>Please prepare your presentation and arrive 15 minutes early.</p>
            <p>If you have questions, contact your adviser.</p>

            <hr style="border: none; border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #666;">
                This is an automated message from the Thesis Defense System.<br>
                © 2025 Your University
            </p>
        </body>
    </html>
    """

    params = {
        "from": "Defense System <no-reply@mails.enviscy.site>",
        "to": recipients,
        "subject": f"🚀 Defense Scheduled: {group.name} - {start_time}",
        "html": html_body,
    }

    try:
        email = resend.Emails.send(params)
        print(f"✅ Email sent successfully! ID: {email['id']}")
        print(f"Sent to {len(recipients)} recipients: {recipients[:3]}{'...' if len(recipients) > 3 else ''}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

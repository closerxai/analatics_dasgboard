import logging

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Cc, Content, Email, Mail, To

logger = logging.getLogger(__name__)


def send_email(subject, message, recipient_list, cc_list=None):
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]
    if isinstance(cc_list, str):
        cc_list = [cc_list]

    try:
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL),
            subject=subject,
        )

        for recipient in recipient_list:
            mail.add_to(To(recipient))

        if cc_list:
            for cc in cc_list:
                mail.add_cc(Cc(cc))

        mail.add_content(Content("text/html", message))
        response = sg.send(mail)
        logger.info(
            "SendGrid email sent successfully | Status: %s | Recipients: %s",
            response.status_code,
            recipient_list,
        )
        return True
    except Exception as exc:
        logger.exception("SendGrid exception: %s", exc)
        return False


def welcome_template(email, password, first_name=None, last_name=None, company_name=None, is_admin=False, cc_list=None):
    full_name = f"{first_name or ''} {last_name or ''}".strip() or "there"
    role_label = "Admin" if is_admin else "User"
    company_line = f"<p><strong>Company:</strong> {company_name}</p>" if company_name else ""
    admin_line = (
        "<p>You have been added as an <strong>Admin</strong> and can start managing your company.</p>"
        if is_admin and company_name
        else ""
    )

    subject = "Welcome to Analytics Dashboard"
    message = f"""
    <html>
      <body>
        <h2>Welcome to Analytics Dashboard</h2>
        <p>Hello {full_name},</p>
        <p>Your account has been created successfully.</p>
        <p><strong>Role:</strong> {role_label}</p>
        {company_line}
        <p><strong>Login email:</strong> {email}</p>
        <p><strong>Temporary password:</strong> {password}</p>
        {admin_line}
        <p>Please log in and change your password.</p>
      </body>
    </html>
    """
    return send_email(subject, message, [email], cc_list=cc_list)

from fastapi_mail import MessageSchema, MessageType
from api.utils.email_functionality import fm
import logging, os

logger = logging.getLogger(__name__)

ADMIN_EMAILS = os.getenv(
    "ADMIN_EMAILS",
    "joseph.ayodele@stu.cu.edu.ng,talk2john40@yahoo.com,ayemoandrewgold@gmail.com",
).split(",")


async def send_hall_full_email(hall, total_beds: int, allocated_beds: int) -> None:
    if not hall:
        raise ValueError("Hall cannot be None")

    subject = f"Hall Full Alert: {hall.hall_name}"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; background: #ffffff;
                    border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <div style="background: #d9534f; color: #ffffff; padding: 16px; text-align: center;">
                <h2>Hall Capacity Alert</h2>
            </div>

            <div style="padding: 20px; color: #333333;">
                <p>The following hall has reached its maximum capacity:</p>

                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Hall Name</td>
                        <td style="padding: 8px;">{hall.hall_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Total Beds</td>
                        <td style="padding: 8px;">{total_beds}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Allocated Beds</td>
                        <td style="padding: 8px;">{allocated_beds}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">
                    Immediate administrative action is required.
                </p>
            </div>

            <div style="background: #f4f4f4; text-align: center; padding: 10px;
                        font-size: 12px; color: #888888;">
                <p>This is an automated notification. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=ADMIN_EMAILS,
        body=body,
        subtype=MessageType.html,
    )

    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.exception("Failed to send hall full email", exc_info=exc)
        raise

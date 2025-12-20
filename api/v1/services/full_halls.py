from fastapi_mail import MessageSchema, MessageType
from api.utils.email_functionality import fm

ADMIN_EMAILS = [
    "joseph.ayodele@stu.cu.edu.ng",
    "talk2john40@yahoo.com",
    "ayemoandrewgold@gmail.com",
]


async def send_hall_full_email(hall_record, category_name):
    subject = f"Hall Full Alert: {hall_record.hall_name}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: #d9534f; color: #ffffff; padding: 16px; text-align: center;">
                <h2 style="margin: 0;">Hall Capacity Alert</h2>
            </div>
            <div style="padding: 20px; color: #333333;">
                <p style="font-size: 15px;">The following hall has reached capacity:</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Hall Name:</td>
                        <td style="padding: 8px;">{hall_record.hall_name}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Category:</td>
                        <td style="padding: 8px;">{category_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Total Beds:</td>
                        <td style="padding: 8px;"></td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Allocated Beds:</td>
                        <td style="padding: 8px;"></td>
                    </tr>
                </table>
                <p style="margin-top: 20px; font-size: 14px;">Please take the necessary action immediately.</p>
            </div>
            <div style="background: #f4f4f4; text-align: center; padding: 10px; font-size: 12px; color: #888888;">
                <p style="margin: 0;">This is an automated notification.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject, recipients=ADMIN_EMAILS, body=body, subtype=MessageType.html
    )
    await fm.send_message(message)
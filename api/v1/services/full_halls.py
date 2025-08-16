from fastapi_mail import MessageSchema, MessageType
from api.utils.email import fm
import asyncio

ADMIN_EMAILS = ["joseph.ayodele@stu.cu.edu.ng", "talk2john40@yahoo.com", "ayemoandrewgold@gmail.com"]


async def send_hall_full_email(hall_record, category_name):
    subject = f"Hall Full Alert: {hall_record.hall_name}"
    body = f"""
    <h3>Hall Capacity Alert</h3>
    <p><b>Hall Name:</b> {hall_record.hall_name}</p>
    <p><b>Category:</b> {category_name}</p>
    <p><b>Total Beds:</b> {hall_record.no_beds}</p>
    <p><b>Allocated Beds:</b> {hall_record.no_allocated_beds}</p>
    <p>Please take the necessary action immediately.</p>
    """

    message = MessageSchema(
        subject=subject, recipients=ADMIN_EMAILS, body=body, subtype=MessageType.html
    )
    await fm.send_message(message)

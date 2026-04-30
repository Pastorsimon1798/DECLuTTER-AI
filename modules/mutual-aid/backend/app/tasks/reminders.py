"""Shift reminder tasks"""
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.shift import Shift, ShiftSignup
from app.models.user import User


@celery_app.task(name="app.tasks.reminders.send_24h_reminders")
def send_24h_reminders():
    """Send 24-hour reminders for upcoming shifts"""
    import asyncio
    asyncio.run(send_24h_reminders_async())


async def send_24h_reminders_async():
    """Async implementation of 24h reminders"""
    async with AsyncSessionLocal() as db:
        # Find shifts starting in 23-25 hours that haven't sent 24h reminder
        now = datetime.utcnow()
        window_start = now + timedelta(hours=23)
        window_end = now + timedelta(hours=25)

        result = await db.execute(
            select(ShiftSignup)
            .join(Shift)
            .options(
                selectinload(ShiftSignup.shift).selectinload(Shift.organization),
                selectinload(ShiftSignup.volunteer)
            )
            .where(
                and_(
                    Shift.start_time >= window_start,
                    Shift.start_time <= window_end,
                    Shift.reminder_24h == True,
                    ShiftSignup.reminder_24h_sent == False,
                    ShiftSignup.status == 'confirmed'
                )
            )
        )

        signups = result.scalars().all()

        for signup in signups:
            try:
                # Send reminder via user's preferred channels
                await send_shift_reminder(
                    signup.volunteer,
                    signup.shift,
                    hours_before=24
                )

                # Mark as sent
                signup.reminder_24h_sent = True
                await db.commit()

            except Exception as e:
                print(f"Error sending 24h reminder for signup {signup.id}: {e}")
                await db.rollback()

        print(f"Sent 24h reminders for {len(signups)} shift signups")


@celery_app.task(name="app.tasks.reminders.send_2h_reminders")
def send_2h_reminders():
    """Send 2-hour reminders for upcoming shifts"""
    import asyncio
    asyncio.run(send_2h_reminders_async())


async def send_2h_reminders_async():
    """Async implementation of 2h reminders"""
    async with AsyncSessionLocal() as db:
        # Find shifts starting in 1.5-2.5 hours that haven't sent 2h reminder
        now = datetime.utcnow()
        window_start = now + timedelta(hours=1, minutes=30)
        window_end = now + timedelta(hours=2, minutes=30)

        result = await db.execute(
            select(ShiftSignup)
            .join(Shift)
            .options(
                selectinload(ShiftSignup.shift).selectinload(Shift.organization),
                selectinload(ShiftSignup.volunteer)
            )
            .where(
                and_(
                    Shift.start_time >= window_start,
                    Shift.start_time <= window_end,
                    Shift.reminder_2h == True,
                    ShiftSignup.reminder_2h_sent == False,
                    ShiftSignup.status == 'confirmed'
                )
            )
        )

        signups = result.scalars().all()

        for signup in signups:
            try:
                # Send reminder via user's preferred channels
                await send_shift_reminder(
                    signup.volunteer,
                    signup.shift,
                    hours_before=2
                )

                # Mark as sent
                signup.reminder_2h_sent = True
                await db.commit()

            except Exception as e:
                print(f"Error sending 2h reminder for signup {signup.id}: {e}")
                await db.rollback()

        print(f"Sent 2h reminders for {len(signups)} shift signups")


async def send_shift_reminder(user: User, shift: Shift, hours_before: int):
    """Send shift reminder via user's preferred channels"""

    # Format reminder message
    time_str = shift.start_time.strftime("%I:%M %p")
    date_str = shift.start_time.strftime("%B %d, %Y")

    title = f"Shift Reminder: {shift.name}"
    body = f"You have a volunteer shift coming up in {hours_before} hours.\n\n"
    body += f"📅 {date_str} at {time_str}\n"
    body += f"📍 {shift.location or shift.organization.name}\n\n"

    if shift.description:
        body += f"Details: {shift.description}\n\n"

    body += "Thank you for volunteering!"

    # Get notification preferences
    prefs = user.notification_prefs or {}

    # Send via SMS if enabled and phone verified
    if prefs.get('sms', False) and user.phone_verified:
        try:
            await send_sms_reminder(user, title, body)
        except Exception as e:
            print(f"Error sending SMS reminder: {e}")

    # Send via email if enabled
    if prefs.get('email', True) and user.email:
        try:
            await send_email_reminder(user, title, body, shift)
        except Exception as e:
            print(f"Error sending email reminder: {e}")

    # Create in-app notification
    try:
        from app.models.notification import Notification
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            notification = Notification(
                user_id=user.id,
                type=f"shift_reminder_{hours_before}h",
                title=title,
                body=body,
                action_url=f"/shifts/{shift.id}",
                channels=['in_app'],
                status='sent'
            )
            db.add(notification)
            await db.commit()
    except Exception as e:
        print(f"Error creating in-app notification: {e}")


async def send_sms_reminder(user: User, title: str, body: str):
    """Send SMS reminder using Plivo"""
    try:
        from app.config import settings
        import plivo

        if not settings.PLIVO_AUTH_ID or not settings.PLIVO_AUTH_TOKEN:
            print("Plivo not configured, skipping SMS")
            return

        client = plivo.RestClient(settings.PLIVO_AUTH_ID, settings.PLIVO_AUTH_TOKEN)

        message = f"{title}\n\n{body}"

        response = client.messages.create(
            src=settings.PLIVO_PHONE_NUMBER,
            dst=user.phone_hash,  # Note: In production, decrypt real phone number
            text=message[:160]  # SMS limit
        )

        print(f"SMS sent to {user.pseudonym}: {response}")

    except Exception as e:
        print(f"Failed to send SMS: {e}")
        raise


async def send_email_reminder(user: User, title: str, body: str, shift: Shift):
    """Send email reminder using Brevo"""
    try:
        from app.config import settings
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException

        if not settings.BREVO_API_KEY:
            print("Brevo not configured, skipping email")
            return

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Create HTML email
        html_body = f"""
        <html>
        <body>
            <h2>{title}</h2>
            <p>{body.replace(chr(10), '<br>')}</p>
            <p>
                <a href="{settings.FRONTEND_URL}/shifts/{shift.id}"
                   style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Shift Details
                </a>
            </p>
        </body>
        </html>
        """

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.pseudonym}],
            sender={"email": settings.BREVO_SENDER_EMAIL, "name": settings.BREVO_SENDER_NAME},
            subject=title,
            html_content=html_body
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent to {user.email}: {api_response}")

    except ApiException as e:
        print(f"Failed to send email: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        raise

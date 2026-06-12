import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string


class EmailService:
    @staticmethod
    def send_email(to_email, subject, html_body, text_body=None):
        config = current_app.config
        if not config.get('MAIL_USERNAME'):
            current_app.logger.warning('Email not configured, skipping send to %s', to_email)
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT']) as server:
                if config.get('MAIL_USE_TLS'):
                    server.starttls()
                server.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
                server.sendmail(config['MAIL_DEFAULT_SENDER'], to_email, msg.as_string())
            return True
        except Exception as e:
            current_app.logger.error('Email send failed: %s', str(e))
            return False

    @staticmethod
    def send_verification_email(user, token):
        verify_url = f"{current_app.config['APP_URL']}/auth/verify-email/{token}"
        html = render_template_string('''
            <h2>Verify Your Email</h2>
            <p>Hello {{ name }},</p>
            <p>Please verify your email by clicking the link below:</p>
            <a href="{{ url }}">Verify Email</a>
            <p>This link expires in 24 hours.</p>
        ''', name=user.first_name, url=verify_url)
        return EmailService.send_email(user.email, 'Verify Your Email - RestaurantPro', html)

    @staticmethod
    def send_password_reset(user, token):
        reset_url = f"{current_app.config['APP_URL']}/auth/reset-password/{token}"
        html = render_template_string('''
            <h2>Password Reset</h2>
            <p>Hello {{ name }},</p>
            <p>Click the link below to reset your password:</p>
            <a href="{{ url }}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
        ''', name=user.first_name, url=reset_url)
        return EmailService.send_email(user.email, 'Password Reset - RestaurantPro', html)

    @staticmethod
    def send_booking_confirmation(booking, user):
        html = render_template_string('''
            <h2>Booking Confirmed!</h2>
            <p>Hello {{ name }},</p>
            <p>Your table reservation has been confirmed.</p>
            <p><strong>Confirmation Code:</strong> {{ code }}</p>
            <p><strong>Date:</strong> {{ date }}</p>
            <p><strong>Time:</strong> {{ time }}</p>
            <p><strong>Guests:</strong> {{ guests }}</p>
        ''', name=user.first_name, code=booking.confirmation_code,
            date=booking.booking_date, time=booking.booking_time, guests=booking.guests)
        return EmailService.send_email(user.email, 'Booking Confirmed - RestaurantPro', html)

    @staticmethod
    def send_otp_email(email, otp):
        html = render_template_string('''
            <h2>Your OTP Code</h2>
            <p>Your one-time password is: <strong>{{ otp }}</strong></p>
            <p>This code expires in 10 minutes.</p>
        ''', otp=otp)
        return EmailService.send_email(email, 'OTP Login - RestaurantPro', html)

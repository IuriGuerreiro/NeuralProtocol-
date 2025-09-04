# Email Verification Setup Guide

This guide will help you set up email verification using Gmail for your Todoist application.

## 🚀 Quick Setup

### 1. Create Environment File

Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Configure Gmail Settings

Edit your `.env` file with your Gmail credentials:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=Todoist <your-email@gmail.com>
```

## 📧 Gmail App Password Setup

Since Gmail requires 2-Factor Authentication for app passwords, follow these steps:

### Step 1: Enable 2-Factor Authentication
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the setup process to enable 2FA

### Step 2: Generate App Password
1. After enabling 2FA, go back to **Security**
2. Under "Signing in to Google", click **App passwords**
3. Select **Mail** and **Other (Custom name)**
4. Enter "Todoist App" as the custom name
5. Click **Generate**
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)
7. Use this password in your `.env` file (remove spaces)

### Step 3: Update Django Settings

Install python-dotenv to load environment variables:
```bash
pip install python-dotenv
```

Update your `settings.py` to use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Email settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@todoist.com')
```

## 🔧 Alternative Email Providers

### Outlook/Hotmail
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### Yahoo Mail
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
```

### SendGrid (Recommended for Production)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## 🧪 Testing Email Configuration

### Method 1: Django Shell
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from Django.',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

### Method 2: Test Registration
1. Start your Django server: `python manage.py runserver`
2. Start your React app: `npm run dev`
3. Go to `http://localhost:5173` and register a new account
4. Check your email for the verification link

## 🚨 Troubleshooting

### "Authentication failed" Error
- **Solution**: Make sure you're using an App Password, not your regular Gmail password
- Verify 2FA is enabled on your Google account

### "Connection refused" Error
- **Solution**: Check your firewall settings
- Ensure EMAIL_USE_TLS=True for Gmail

### "Invalid sender" Error
- **Solution**: Make sure EMAIL_HOST_USER matches the "From" address
- Use the same email for both EMAIL_HOST_USER and DEFAULT_FROM_EMAIL

### Emails going to Spam
- **Solutions**:
  - Add SPF record to your domain (if you have one)
  - Use a consistent "From" name and email
  - Avoid spam trigger words in subject/content

## 🏭 Production Considerations

### Use a Dedicated Email Service
For production, consider using:
- **SendGrid** (99 emails/month free)
- **Mailgun** (10,000 emails/month free for 3 months)
- **Amazon SES** (62,000 emails/month free for 12 months)
- **Postmark** (100 emails/month free)

### Environment Variables
Never commit your `.env` file to version control:
```bash
echo ".env" >> .gitignore
```

### Security Best Practices
1. Use different credentials for development and production
2. Regularly rotate your app passwords
3. Monitor email sending limits
4. Implement rate limiting for email sending

## 📝 Example Email Flow

1. **User Registration**: User enters email and password
2. **Email Sent**: Verification email sent to user's inbox
3. **User Clicks Link**: Link format: `http://localhost:5173/verify-email/{token}`
4. **Token Verification**: Backend validates token and activates user
5. **Success**: User can now log in

## 🔗 Useful Links

- [Google App Passwords Help](https://support.google.com/accounts/answer/185833)
- [Django Email Documentation](https://docs.djangoproject.com/en/4.2/topics/email/)
- [SendGrid Django Integration](https://docs.sendgrid.com/for-developers/sending-email/django)

## 💡 Development vs Production

### Development
```env
# Print emails to console (no actual sending)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production
```env
# Actually send emails via SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

---

**Need help?** Check the Django server console for error messages when testing email sending.
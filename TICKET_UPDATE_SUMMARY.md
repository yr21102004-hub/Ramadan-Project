# Ticket & Notifications Update

## 1. User Ticket System
- **New Page**: `user_tickets.html` created for users to manage their support requests.
- **Access**: "الدعم الفني" (Support) tab added to `user_dashboard.html`.
- **Functionality**:
    - Users can see their tickets (Open/Progress/Closed).
    - Users can create new tickets via a Modal.
    - Fields: Subject, Category, Priority, Message.

## 2. Email Notifications (Simulated)
- **Dependency**: Installed `flask-mail` (ready for future use).
- **Service**: Created `utils/email_sender.py` to handle sending.
- **Logic**:
    - Checks for ADMIN_EMAIL, MAIL_SERVER, etc. in `.env`.
    - If credentials missing (Dev Mode), logs email to **Console/Terminal** instead of crashing.
    - Sends an email to Admin when a user opens a new ticket.

## 3. Configuration
- **Environment**: You must set `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` in `.env` to enable real emails.
- **Fallback**: System works perfectly without real emails (logs to console).

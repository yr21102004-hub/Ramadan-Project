# New Business Features Summary

## 1. Automated Reports
- **Module**: New reporting system accessible via `/admin/reports`.
- **Formats**: PDF (via ReportLab) and Excel (via OpenPyXL).
- **Types**: 
    - Monthly Summary (Users, Requests, Revenue).
    - Tickets Status.
    - Revenue Reports.
- **Data Export**: Full CSV/Excel dumps for Users, Tickets, Payments, Messages.

## 2. Ticket System
- **Module**: Dedicated support ticket management `/admin/tickets`.
- **Status Workflow**: Open -> In Progress -> Closed.
- **Priority**: High / Medium / Low.
- **Integration**: Database model `TicketModel` integrated with Admin Dashboard.

## 3. CRM Integration
- **UI**: New integrations page `/admin/integrations`.
- **Supported placeholders**: Zoho, HubSpot, Salesforce.
- **Function**: Setup modals for API Key input (ready for backend logic implementation).

## 4. Roles & Permissions
- **Security**: Added `@role_required` decorator for granular access control.
- **Roles**:
    - **Admin**: Full access.
    - **Manager**: Tickets & Projects.
    - **Viewer**: Read-only (partial).
- **User Model**: Updated with `is_admin`, `is_manager` properties.

## 5. Setup Instructions
- **Dependencies**: Required libraries installed (`reportlab`, `openpyxl`).
- **Database**: Ensure `tickets` table exists (auto-created in `database.py`).

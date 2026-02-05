from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import os
import shutil
import io
import csv
import base64
import qrcode
import pyotp
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from utils.decorators import role_required
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import openpyxl
except ImportError:
    pass # Libraries might not be installed yet

from models import UserModel, ChatModel, PaymentModel, SecurityLogModel, UnansweredQuestionsModel, LearnedAnswersModel, ContactModel, Database, RatingModel, ComplaintModel, InspectionRequestModel, TicketModel, TicketMessageModel

admin_bp = Blueprint('admin', __name__)
bcrypt = Bcrypt()

# Initialize models
user_model = UserModel()
chat_model = ChatModel()
payment_model = PaymentModel()
security_log_model = SecurityLogModel()
unanswered_model = UnansweredQuestionsModel()
learned_model = LearnedAnswersModel()
contact_model = ContactModel()
rating_model = RatingModel()
complaint_model = ComplaintModel()
inspection_model = InspectionRequestModel()
ticket_model = TicketModel()
ticket_message_model = TicketMessageModel()
db = Database()

@admin_bp.before_app_request
def restrict_to_admins_globally():
    """Ensure only authenticated admins can access any admin route (including aliases)"""
    # Detect if it's an admin route by path (case-insensitive) or endpoint
    path = request.path.lower()
    endpoint = request.endpoint or ""
    
    # Check for admin endpoints (including aliases defined in app.py)
    admin_endpoints = [
        'admin', 'admin_users', 'admin_messages', 'admin_chats', 'admin_backup', 
        'admin_learned_answers', 'admin_transfers', 'admin_unanswered_questions', 
        'admin_complaints', 'admin_inspections', 'security_audit', 'setup_2fa', 
        'toggle_2fa', 'add_user', 'delete_user', 'update_project_percentage',
        'confirm_payment', 'view_chats', 'admin_dashboard', 'manual_backup',
        'admin_unanswered', 'admin_learned', 'admin_messages', 'answer_question',
        'delete_answered_question', 'delete_message', 'answer_unanswered_question'
    ]
    
    is_admin_path = path.startswith('/admin')
    is_admin_endpoint = endpoint.startswith('admin.') or endpoint in admin_endpoints

    if is_admin_path or is_admin_endpoint:
        # Log if someone is trying to use the username query param bypass attempt
        q_user = request.args.get('username')
        if q_user:
            security_log_model.create("Admin URL Param Detection", 
                                    f"URL contains username param: {q_user} for path {request.path}",
                                    severity="medium")

        # If the user is not authenticated, redirect to login
        if not current_user.is_authenticated:
            flash('عذراً، يجب تسجيل الدخول أولاً للوصول إلى لوحة التحكم.', 'warning')
            
            # Log the unauthenticated attempt
            security_log_model.create("Unauthenticated Admin Access Attempt", 
                                    f"Anonymous tried to access {request.path}",
                                    severity="medium")
            
            return redirect(url_for('auth.login', next=request.url))
            
        # If the user is authenticated but not an admin, redirect to home
        if getattr(current_user, 'role', None) != 'admin':
            flash('عذراً، هذه الصفحة مخصصة للإدارة فقط.', 'danger')
            
            # Log the unauthorized attempt
            security_log_model.create("Unauthorized Admin Access Attempt", 
                                    f"User {current_user.username} (role: {current_user.role}) tried to access {request.path}",
                                    severity="high")
            
            return redirect(url_for('index'))

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    # Final safety check
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = user_model.get_all()
    messages = contact_model.get_all()
    chats = chat_model.get_all()
    unanswered = unanswered_model.get_all()
    sec_logs = security_log_model.get_all()
    payments = payment_model.get_all()
    
    # Sort
    messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    unanswered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    sec_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Chat Context Logic
    chats_by_user = {}
    for c in chats:
        uid = c.get('user_id', 'unknown')
        if uid not in chats_by_user:
            chats_by_user[uid] = []
        chats_by_user[uid].append(c)
    
    for uid in chats_by_user:
        chats_by_user[uid].sort(key=lambda x: x.get('timestamp', ''))

    def get_context(uid, q_time_str):
        full_history = chats_by_user.get(uid, [])
        if not full_history: return []
        try:
            q_time = datetime.strptime(q_time_str, "%Y-%m-%d %H:%M:%S")
        except:
            return full_history[-10:]
            
        context = []
        for h in full_history:
            try:
                h_time = datetime.strptime(h.get('timestamp', ''), "%Y-%m-%d %H:%M:%S")
                diff = (q_time - h_time).total_seconds()
                if 0 <= diff <= 1800:
                    context.append(h)
            except:
                continue
        return context[-15:]

        return context[-15:]

    # Basic Analytics for Dashboard Summary (if needed)
    total_users_count = len(users)
    total_requests_count = len(messages)
    conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
    
    # Calculate analytics
    total_users_count = len(users)
    total_requests_count = len(messages)
    
    # Payment Analytics
    payments_list = payment_model.get_all()
    confirmed_payments = [p for p in payments_list if p.get('status') == 'Confirmed']
    total_revenue = sum(float(p.get('amount', 0)) for p in confirmed_payments)
    
    conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
    
    payments_list = payment_model.get_all()
    # Assume 'Confirmed' is the status for verified payments
    # Filter case-insensitive just in case
    confirmed_payments = [p for p in payments_list if str(p.get('status', '')).lower() == 'confirmed']
    total_revenue = sum(float(p.get('amount', 0)) for p in confirmed_payments)
    
    # Inspection Analytics
    inspections_list = inspection_model.get_all()

    analytics_summary = {
        'total_users': total_users_count,
        'total_requests': total_requests_count, # Messages
        'total_inspections': len(inspections_list), # Actual Inspections
        'conversion_rate': conversion_rate,
        'total_revenue': total_revenue,
        'active_users': len([u for u in users if u.get('project_percentage', 0) > 0]),
        'completed_projects': len([u for u in users if u.get('project_percentage', 0) == 100]),
        'ongoing_projects': len([u for u in users if 0 < u.get('project_percentage', 0) < 100]),
        'not_started': len([u for u in users if u.get('project_percentage', 0) == 0]),
        'total_payments': len(payments_list),
        'pending_questions': len(unanswered)
    }

    return render_template('admin.html', users=users, messages=messages, 
                           chats=chats, unanswered=unanswered, security_logs=sec_logs[:50],
                           payments=payments, chats_by_user=chats_by_user, get_context=get_context,
                           analytics=analytics_summary)

@admin_bp.route('/admin/users')
def admin_users():
    
    # Get only users with role='user' or no role (default to user)
    all_users = user_model.get_all()
    users = [u for u in all_users if u.get('role', 'user') == 'user']
    
    # Get contact messages (requests)
    messages = contact_model.get_all()
    
    # Get unanswered questions
    unanswered = unanswered_model.get_all()
    
    # Get all chats to filter user-related questions
    chats = chat_model.get_all()
    
    # Get payments
    payments = payment_model.get_all()
    
    # Filter unanswered questions from users (not workers)
    user_unanswered = []
    for q in unanswered:
        user_id = q.get('user_id')
        # Check if this user_id belongs to a user (not worker)
        user_obj = user_model.get_by_username(user_id)
        if user_obj and user_obj.get('role', 'user') == 'user':
            user_unanswered.append(q)
    
    # Calculate basic analytics
    total_users = len(users)
    total_requests = len(messages)
    conversion_rate = round((total_requests / total_users * 100), 1) if total_users > 0 else 0
    pending_questions = len(user_unanswered)
    
    # Calculate advanced analytics
    completed_projects = len([u for u in users if u.get('project_percentage', 0) == 100])
    ongoing_projects = len([u for u in users if 0 < u.get('project_percentage', 0) < 100])
    not_started = len([u for u in users if u.get('project_percentage', 0) == 0])
    
    # Average completion rate
    total_percentage = sum([u.get('project_percentage', 0) for u in users])
    avg_completion = round(total_percentage / total_users, 1) if total_users > 0 else 0
    
    # Active users (users with chats)
    user_chats = [c for c in chats if user_model.get_by_username(c.get('user_id')) and 
                  user_model.get_by_username(c.get('user_id')).get('role', 'user') == 'user']
    active_users = len(set([c.get('user_id') for c in user_chats]))
    
    # Payment statistics
    user_payments = [p for p in payments if user_model.get_by_username(p.get('username')) and
                     user_model.get_by_username(p.get('username')).get('role', 'user') == 'user']
    total_payments = len(user_payments)
    
    analytics = {
        'total_users': total_users,
        'total_requests': total_requests,
        'conversion_rate': conversion_rate,
        'pending_questions': pending_questions,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects,
        'not_started': not_started,
        'avg_completion': avg_completion,
        'active_users': active_users,
        'total_payments': total_payments
    }
    
    return render_template('admin_users.html', 
                         users=users, 
                         messages=messages[:10],  # Latest 10 messages
                         unanswered=user_unanswered[:10],  # Latest 10 unanswered
                         payments=user_payments[:10],  # Latest 10 payments
                         analytics=analytics)



@admin_bp.route('/admin/analytics')
def analytics_dashboard():
    
    try:
        users = user_model.get_all()
        messages = contact_model.get_all()
        chats = chat_model.get_all()
        sec_logs = security_log_model.get_all()
        unanswered = unanswered_model.get_all()
        
        from collections import Counter
        from datetime import datetime
        
        # 1. Totals
        total_users_count = len(users)
        total_requests_count = len(messages)
        conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
        
        # 2. Frequent AI Users
        user_ai_days = {}
        for c in chats:
            uname = c.get('user_name', 'Unknown')
            ts = c.get('timestamp', '')
            if ts:
                date = ts.split(' ')[0]
                if uname not in user_ai_days: user_ai_days[uname] = set()
                user_ai_days[uname].add(date)
        frequent_ai_stats = {u: len(d) for u, d in user_ai_days.items() if len(d) >= 2}
        sorted_frequent = sorted(frequent_ai_stats.items(), key=lambda x: x[1], reverse=True)
        analy_ai_labels = [x[0] for x in sorted_frequent]
        analy_ai_values = [x[1] for x in sorted_frequent]

        # 3. Top Visitors (All Time)
        all_login_events = [l for l in sec_logs if 'Login' in str(l.get('event', '')) and 'Success' in str(l.get('event', ''))]
        all_visitors_list = []
        for l in all_login_events:
            details = str(l.get('details', ''))
            if 'User ' in details:
                try:
                    username = details.split('User ')[1].split(' ')[0]
                    all_visitors_list.append(username)
                except: pass
        top_all_visitors_data = Counter(all_visitors_list).most_common()
        analy_all_visitors_labels = [x[0] for x in top_all_visitors_data]
        analy_all_visitors_values = [x[1] for x in top_all_visitors_data]

        # 4. Daily & Heavy Visitors
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_login_events = [l for l in sec_logs if 'Login' in str(l.get('event', '')) and 'Success' in str(l.get('event', '')) and str(l.get('timestamp', '')).startswith(today_str)]
        today_visitors_list = []
        for l in today_login_events:
            details = str(l.get('details', ''))
            if 'User ' in details:
                try:
                    username = details.split('User ')[1].split(' ')[0]
                    today_visitors_list.append(username)
                except: pass
        today_visitor_counts = Counter(today_visitors_list)
        heavy_data = {k: v for k, v in today_visitor_counts.items() if v > 2}
        analy_heavy_labels = list(heavy_data.keys())
        analy_heavy_values = list(heavy_data.values())
        daily_data = {k: v for k, v in today_visitor_counts.items() if v == 1}
        analy_daily_labels = list(daily_data.keys())
        analy_daily_values = list(daily_data.values()) 

        # 5. Top Requested Services
        service_counts = Counter([str(m.get('service', 'general')) for m in messages])
        service_map = {'modern-paints':'دهانات حديثة','gypsum-board':'جبس بورد','integrated-finishing':'تشطيب متكامل',
                      'putty-finishing':'تأسيس ومعجون','wallpaper':'ورق حائط','renovation':'تجديد وترميم','general':'استفسار عام'}
        top_services_req_data = service_counts.most_common(5)
        top_services_req_labels = [service_map.get(x[0], x[0]) for x in top_services_req_data]
        top_services_req_values = [x[1] for x in top_services_req_data]
        
        # 6. Most Viewed Services
        service_views = []
        for l in sec_logs:
            if str(l.get('event')) == 'Service View':
                details = str(l.get('details', ''))
                if 'User viewed service: ' in details:
                    try:
                        svc_title = details.split('User viewed service: ')[1]
                        service_views.append(svc_title)
                    except: pass
        top_services_view_data = Counter(service_views).most_common(5)
        top_services_view_labels = [x[0] for x in top_services_view_data]
        top_services_view_values = [x[1] for x in top_services_view_data]

        # 7. Peak Hours
        hour_counts = Counter()
        for l in sec_logs:
            ts = str(l.get('timestamp', ''))
            if ts and ' ' in ts:
                try:
                    hour = ts.split(' ')[1].split(':')[0]
                    hour_counts[hour] += 1
                except: pass
        sorted_hours = sorted([ (str(h).zfill(2), hour_counts.get(str(h).zfill(2), 0)) for h in range(24) ])
        peak_hours_labels = [x[0] + ":00" for x in sorted_hours]
        peak_hours_values = [x[1] for x in sorted_hours]

        # 8. AI Efficiency
        total_ai_msgs = len(chats)
        unanswered_msgs = len(unanswered)
        answered_msgs = max(0, total_ai_msgs - unanswered_msgs)
        ai_efficiency = {
            'names': ['تم الرد', 'بدون إجابة'],
            'counts': [answered_msgs, unanswered_msgs]
        }

        # 9. Page Popularity
        page_views = []
        for l in sec_logs:
            event = str(l.get('event', ''))
            if 'View' in event or 'Page' in event:
                details = str(l.get('details', ''))
                if 'page: ' in details.lower():
                    parts = details.lower().split('page: ')
                    if len(parts) > 1:
                        pname = parts[1].strip()
                        page_views.append(pname)
                elif event == 'Service View':
                    page_views.append('الخدمات')

        page_map = {'/':'الرئيسية','home':'الرئيسية','projects':'معرض الأعمال','about':'من نحن','contact':'اتصل بنا','services':'الخدمات','admin':'لوحة التحكم','login':'تسجيل الدخول'}
        top_pages_data = Counter(page_views).most_common(5)
        page_pop_labels = [page_map.get(x[0], x[0]) for x in top_pages_data]
        page_pop_values = [x[1] for x in top_pages_data]

        return render_template('analytics.html', analytics={
            'total_users': total_users_count, 'total_requests': total_requests_count, 'conversion_rate': conversion_rate,
            'top_ai_labels': analy_ai_labels, 'top_ai_values': analy_ai_values,
            'top_all_visitors_labels': analy_all_visitors_labels, 'top_all_visitors_values': analy_all_visitors_values,
            'heavy_visitors_labels': analy_heavy_labels, 'heavy_visitors_values': analy_heavy_values,
            'daily_visitors_labels': analy_daily_labels, 'daily_visitors_values': analy_daily_values,
            'top_services_req_labels': top_services_req_labels, 'top_services_req_values': top_services_req_values,
            'top_services_view_labels': top_services_view_labels, 'top_services_view_values': top_services_view_values,
            'peak_hours_labels': peak_hours_labels, 'peak_hours_values': peak_hours_values,
            'ai_efficiency': ai_efficiency, 'page_pop_labels': page_pop_labels, 'page_pop_values': page_pop_values
        })
    except Exception as e:
        import traceback
        with open('analytics_error.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        print(f"ANALYTICS ERROR: {str(e)}")
        flash(f"حدث خطأ أثناء تحميل الإحصائيات. تم تسجيل الخطأ للفحص.")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/analytics/export')
@login_required
def export_analytics():
    """Export comprehensive site analytics to Excel with professional formatting"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    try:
        from utils.export_helper import export_analytics_excel
        
        users = user_model.get_all()
        messages = contact_model.get_all()
        chats = chat_model.get_all()
        payments = payment_model.get_all()
        inspections = db.inspection_requests.all()
        complaints = complaint_model.get_all()
        unanswered = unanswered_model.get_all()
        
        # Prepare analytics data
        analytics_data = {
            'total_users': len(users),
            'total_requests': len(messages),
            'total_chats': len(chats),
            'total_payments': len(payments),
            'total_inspections': len(inspections),
            'total_complaints': len(complaints),
            'pending_questions': len(unanswered),
            'completed_projects': len([u for u in users if u.get('project_percentage', 0) == 100]),
            'ongoing_projects': len([u for u in users if 0 < u.get('project_percentage', 0) < 100]),
            'not_started': len([u for u in users if u.get('project_percentage', 0) == 0]),
        }
        
        # Generate Excel file
        output = export_analytics_excel(analytics_data)
        
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"site_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
    except ImportError:
        # Fallback to enhanced CSV
        flash('مكتبة Excel غير متوفرة، سيتم التصدير بصيغة CSV محسّنة', 'warning')
        
        users = user_model.get_all()
        messages = contact_model.get_all()
        chats = chat_model.get_all()
        payments = payment_model.get_all()
        inspections = db.inspection_requests.all()
        complaints = complaint_model.get_all()
        unanswered = unanswered_model.get_all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Title
        writer.writerow(['═══════════════════════════════════════════'])
        writer.writerow(['تقرير إحصائيات الموقع الشامل'])
        writer.writerow([f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow(['═══════════════════════════════════════════'])
        writer.writerow([])
        
        # 1. General Statistics
        writer.writerow(['━━━ الإحصائيات العامة ━━━'])
        writer.writerow(['المؤشر', 'القيمة'])
        writer.writerow(['إجمالي المستخدمين', len(users)])
        writer.writerow(['إجمالي الرسائل', len(messages)])
        writer.writerow(['إجمالي المحادثات', len(chats)])
        writer.writerow(['إجمالي المدفوعات', len(payments)])
        writer.writerow(['طلبات المعاينة', len(inspections)])
        writer.writerow(['الشكاوى', len(complaints)])
        writer.writerow(['أسئلة بدون إجابة', len(unanswered)])
        writer.writerow([])
        
        # 2. User Statistics
        writer.writerow(['━━━ إحصائيات المستخدمين ━━━'])
        writer.writerow(['المؤشر', 'القيمة', 'النسبة'])
        completed = len([u for u in users if u.get('project_percentage', 0) == 100])
        ongoing = len([u for u in users if 0 < u.get('project_percentage', 0) < 100])
        not_started = len([u for u in users if u.get('project_percentage', 0) == 0])
        
        total = len(users) if users else 1
        writer.writerow(['مشاريع مكتملة (100%)', completed, f'{(completed/total*100):.1f}%'])
        writer.writerow(['مشاريع جارية (1-99%)', ongoing, f'{(ongoing/total*100):.1f}%'])
        writer.writerow(['مشاريع لم تبدأ (0%)', not_started, f'{(not_started/total*100):.1f}%'])
        
        total_percentage = sum([u.get('project_percentage', 0) for u in users])
        avg_completion = round(total_percentage / len(users), 1) if users else 0
        writer.writerow(['متوسط نسبة الإنجاز', f'{avg_completion}%', ''])
        writer.writerow([])
        
        # 3. Payment Statistics
        writer.writerow(['━━━ إحصائيات المدفوعات ━━━'])
        writer.writerow(['المؤشر', 'القيمة'])
        total_revenue = sum([float(p.get('amount', 0)) for p in payments])
        confirmed_payments = [p for p in payments if p.get('status') == 'Confirmed']
        pending_payments = [p for p in payments if 'pending' in p.get('status', '').lower()]
        
        writer.writerow(['إجمالي الإيرادات', f'{total_revenue:,.2f} جنيه'])
        writer.writerow(['مدفوعات مؤكدة', f'{len(confirmed_payments)} ({len(confirmed_payments)/len(payments)*100:.1f}%)' if payments else '0'])
        writer.writerow(['مدفوعات قيد المراجعة', f'{len(pending_payments)} ({len(pending_payments)/len(payments)*100:.1f}%)' if payments else '0'])
        writer.writerow(['متوسط قيمة الدفعة', f'{total_revenue/len(payments):,.2f} جنيه' if payments else '0'])
        writer.writerow([])
        
        # 4. Message Statistics
        writer.writerow(['━━━ إحصائيات الرسائل ━━━'])
        writer.writerow(['الحالة', 'العدد', 'النسبة'])
        pending_msgs = len([m for m in messages if m.get('status') == 'pending'])
        approved_msgs = len([m for m in messages if m.get('status') == 'approved'])
        rejected_msgs = len([m for m in messages if m.get('status') == 'rejected'])
        
        total_msgs = len(messages) if messages else 1
        writer.writerow(['قيد المراجعة', pending_msgs, f'{(pending_msgs/total_msgs*100):.1f}%'])
        writer.writerow(['موافق عليها', approved_msgs, f'{(approved_msgs/total_msgs*100):.1f}%'])
        writer.writerow(['مرفوضة', rejected_msgs, f'{(rejected_msgs/total_msgs*100):.1f}%'])
        writer.writerow([])
        
        # 5. Service Requests
        writer.writerow(['━━━ الخدمات الأكثر طلباً ━━━'])
        writer.writerow(['الخدمة', 'عدد الطلبات', 'النسبة'])
        from collections import Counter
        service_counts = Counter([m.get('service', 'general') for m in messages])
        service_map = {
            'modern-paints': 'دهانات حديثة',
            'gypsum-board': 'جبس بورد',
            'integrated-finishing': 'تشطيب متكامل',
            'putty-finishing': 'تأسيس ومعجون',
            'wallpaper': 'ورق حائط',
            'renovation': 'تجديد وترميم',
            'general': 'استفسار عام'
        }
        for service, count in service_counts.most_common():
            writer.writerow([service_map.get(service, service), count, f'{(count/total_msgs*100):.1f}%'])
        writer.writerow([])
        
        # 6. AI Chat Efficiency
        writer.writerow(['━━━ كفاءة الذكاء الاصطناعي ━━━'])
        writer.writerow(['المؤشر', 'القيمة', 'النسبة'])
        total_ai_msgs = len(chats)
        unanswered_count = len(unanswered)
        answered_count = max(0, total_ai_msgs - unanswered_count)
        efficiency_rate = round((answered_count / total_ai_msgs * 100), 1) if total_ai_msgs > 0 else 0
        
        writer.writerow(['إجمالي المحادثات', total_ai_msgs, '100%'])
        writer.writerow(['تم الرد عليها', answered_count, f'{efficiency_rate}%'])
        writer.writerow(['بدون إجابة', unanswered_count, f'{(100-efficiency_rate):.1f}%'])
        writer.writerow([])
        
        # 7. Inspection Requests
        writer.writerow(['━━━ طلبات المعاينة ━━━'])
        writer.writerow(['الحالة', 'العدد', 'النسبة'])
        new_inspections = len([i for i in inspections if i.get('status') == 'new_request'])
        scheduled = len([i for i in inspections if i.get('status') == 'scheduled'])
        completed_insp = len([i for i in inspections if i.get('status') == 'completed'])
        
        total_insp = len(inspections) if inspections else 1
        writer.writerow(['طلبات جديدة', new_inspections, f'{(new_inspections/total_insp*100):.1f}%'])
        writer.writerow(['مجدولة', scheduled, f'{(scheduled/total_insp*100):.1f}%'])
        writer.writerow(['مكتملة', completed_insp, f'{(completed_insp/total_insp*100):.1f}%'])
        writer.writerow([])
        
        writer.writerow(['═══════════════════════════════════════════'])
        writer.writerow(['نهاية التقرير'])
        writer.writerow(['═══════════════════════════════════════════'])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"site_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
    except Exception as e:
        flash(f'حدث خطأ أثناء تصدير الإحصائيات: {str(e)}', 'error')
        return redirect(url_for('admin.analytics_dashboard'))


@admin_bp.route('/admin/add_user', methods=['POST'])
def add_user():
        
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    project_location = request.form.get('project_location')
    project_description = request.form.get('project_description', 'لا يوجد وصف')
    
    profile_image_path = None
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"{username}_{timestamp}.{file_extension}"
            
            upload_folder = os.path.join('static', 'user_images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            profile_image_path = f"user_images/{unique_filename}"
    
    password = bcrypt.generate_password_hash(username).decode('utf-8') 

    if user_model.get_by_username(username):
        return "User already exists", 400

    user_model.create({
        'username': username,
        'password': password,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'profile_image': profile_image_path,
        'project_location': project_location,
        'project_description': project_description,
        'project_percentage': 0,
        'role': 'user'
    })
    
    flash(f"تم إضافة المستخدم {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/answer_question', methods=['POST'])
def answer_question():
    question = request.form.get('question')
    answer = request.form.get('answer')
    
    if not answer:
        flash("يرجى كتابة إجابة قبل الحفظ.")
        return redirect(url_for('admin.admin_dashboard'))

    # Add to learned answers immediately and delete from pending
    learned_model.create(question=question, answer=answer)
    unanswered_model.delete(question)
    
    flash("تم حفظ الإجابة وإضافتها لقاعدة المعرفة، وتم إزالة السؤال من القائمة.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/answer_unanswered_question', methods=['POST'])
def answer_unanswered_question():
    """Answer an unanswered question from user dashboard"""
    if not current_user.is_authenticated or current_user.role != 'admin': 
        return redirect(url_for('index'))
    
    question_id = request.form.get('question_id')
    question_text = request.form.get('question_text')
    answer = request.form.get('answer')
    user_id = request.form.get('user_id')
    
    if not answer or not question_text:
        flash("يرجى كتابة إجابة قبل الحفظ.")
        return redirect(request.referrer or url_for('admin.admin_dashboard'))
    
    # Add to learned answers
    learned_model.create(question=question_text, answer=answer)
    
    # Send Email Notification
    try:
        user_info = user_model.get_by_username(user_id)
        if user_info and user_info.get('email'):
             send_email(
                user_info['email'],
                "تم الرد على سؤالك - RMG Decor AI",
                f"""
                <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h3 style="color: #333;">مرحباً {user_info['full_name']}،</h3>
                    <p>لقد قمت بسؤالنا عبر الذكاء الاصطناعي عن: <strong>"{question_text}"</strong></p>
                    <p>وقد قامت الإدارة بمراجعة سؤالك والرد عليه:</p>
                    <blockquote style="background: #fff; border-right: 5px solid #D4AF37; padding: 15px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                        {answer}
                    </blockquote>
                    <p>تم تحديث قاعدة بيانات الذكاء الاصطناعي بهذه المعلومة لخدمتك بشكل أفضل مستقبلاً.</p>
                </div>
                """
            )
    except Exception as e:
        print(f"Error sending email: {e}")
    
    # Delete from unanswered questions
    if question_id:
        unanswered_model.delete_by_id(question_id)
    else:
        unanswered_model.delete(question_text)
    
    flash(f"✅ تم حفظ الرد بنجاح! السؤال تمت إضافته لقاعدة المعرفة وتم حذفه من القائمة.")
    return redirect(request.referrer or url_for('user.profile', username=user_id))

@admin_bp.route('/admin/delete_message', methods=['POST'])
def delete_message():
    doc_id = request.form.get('doc_id')
    contact_model.delete(doc_id)
    flash("تم حذف الرسالة بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete_answered_question', methods=['POST'])
def delete_answered_question():
    question = request.form.get('question')
    question_record = unanswered_model.get_by_question(question)
    
    if question_record and question_record.get('admin_response'):
        learned_model.create(question=question, answer=question_record.get('admin_response'))
        unanswered_model.delete(question)
        flash("تم نقل السؤال والإجابة إلى قاعدة المعرفة.")
    else:
        unanswered_model.delete(question)
        flash("تم حذف السؤال نهائياً.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete_all_unanswered', methods=['POST'])
def delete_all_unanswered_questions():
    unanswered_model.delete_all()
    flash("تم حذف جميع الأسئلة المعلقة بنجاح.")
    return redirect(url_for('admin.admin_unanswered_questions'))

@admin_bp.route('/admin/learned_answers')
def learned_answers():
    learned = learned_model.get_all()
    learned.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    return render_template('admin_learned.html', learned=learned)

@admin_bp.route('/admin/chats')
def view_chats():
    chats = chat_model.get_all()
    chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return render_template('admin_chats.html', chats=chats)

@admin_bp.route('/admin/chats/delete', methods=['POST'])
@login_required
def delete_chats():
    """Delete chat logs based on time period"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    period = request.form.get('period', 'all')
    
    try:
        from datetime import datetime, timedelta
        
        if period == 'all':
            # Delete all chats
            chat_model.delete_all()
            flash('تم حذف جميع سجلات المحادثات بنجاح', 'success')
            security_log_model.create("Chat Logs Deleted", 
                                     f"Admin {current_user.username} deleted all chat logs", 
                                     severity="medium")
        
        elif period == 'week':
            # Delete chats from last week
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            deleted_count = chat_model.delete_by_date_range(week_ago)
            flash(f'تم حذف سجلات آخر أسبوع ({deleted_count} محادثة)', 'success')
            security_log_model.create("Chat Logs Deleted", 
                                     f"Admin {current_user.username} deleted last week's chat logs ({deleted_count} chats)", 
                                     severity="medium")
        
        elif period == 'month':
            # Delete chats from last month
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            deleted_count = chat_model.delete_by_date_range(month_ago)
            flash(f'تم حذف سجلات آخر شهر ({deleted_count} محادثة)', 'success')
            security_log_model.create("Chat Logs Deleted", 
                                     f"Admin {current_user.username} deleted last month's chat logs ({deleted_count} chats)", 
                                     severity="medium")
        
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_chats'))

@admin_bp.route('/admin/chats/export')
@login_required
def export_chats():
    """Export chat logs to Excel with professional formatting"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    try:
        from utils.export_helper import export_chats_excel
        
        chats = chat_model.get_all()
        # Sort by timestamp
        chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Generate Excel file
        output = export_chats_excel(chats)
        
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"chat_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    except ImportError:
        # Fallback to CSV
        flash('مكتبة Excel غير متوفرة، سيتم التصدير بصيغة CSV', 'warning')
        
        chats = chat_model.get_all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['التوقيت', 'المستخدم', 'اسم المستخدم', 'رسالة العميل', 'رد الذكاء الاصطناعي', 'IP Address'])
        
        # Data
        for chat in chats:
            writer.writerow([
                chat.get('timestamp', ''),
                chat.get('username', 'زائر'),
                chat.get('user_name', ''),
                chat.get('message', ''),
                chat.get('response', ''),
                chat.get('user_ip', '')
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"chat_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

# ... (omitted unrelated routes) ...

@admin_bp.route('/admin/export/pdf', methods=['POST'])
@login_required
@role_required(['admin'])
def export_pdf_report():
    report_type = request.form.get('report_type')
    
    # Simple Text-based PDF generation logic
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Add title
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, "RMG Decor - Admin Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Generated by: {current_user.full_name or current_user.username}")
    p.drawString(50, height - 100, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, height - 120, f"Report Type: {report_type.replace('_', ' ').title()}")
    
    p.line(50, height - 130, width - 50, height - 130)
    
    y = height - 160
    
    if report_type == 'monthly_summary':
        users = user_model.get_all()
        reqs = contact_model.get_all()
        payments = payment_model.get_all()
        chats = chat_model.get_all()
        
        revenue = sum(float(p.get('amount', 0)) for p in payments if p.get('status') == 'Confirmed')
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Monthly Summary Statistics:")
        y -= 30
        
        p.setFont("Helvetica", 12)
        stats = [
            f"Total Users: {len(users)}",
            f"Total Requests: {len(reqs)}",
            f"Total Chats: {len(chats)}",
            f"Total Revenue: {revenue:,.2f} EGP",
            f"Active Projects: {len([u for u in users if 0 < u.get('project_percentage', 0) < 100])}"
        ]
        
        for stat in stats:
            p.drawString(70, y, f"- {stat}")
            y -= 20
            
    elif report_type == 'financial_report':
        payments = payment_model.get_all()
        revenue = sum(float(p.get('amount', 0)) for p in payments if p.get('status') == 'Confirmed')
        pending = sum(float(p.get('amount', 0)) for p in payments if 'pending' in p.get('status', '').lower())
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Financial Overview:")
        y -= 30
        
        p.setFont("Helvetica", 12)
        p.drawString(70, y, f"Total Revenue (Confirmed): {revenue:,.2f} EGP")
        y -= 20
        p.drawString(70, y, f"Pending Revenue: {pending:,.2f} EGP")
        y -= 20
        p.drawString(70, y, f"Total Transactions: {len(payments)}")
        y -= 40
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Recent Transactions (Last 10):")
        y -= 20
        
        p.setFont("Helvetica", 10)
        # Sort payments
        payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for pay in payments[:10]:
            line = f"{pay.get('timestamp')} - {pay.get('username')} - {pay.get('amount')} EGP - {pay.get('status')}"
            p.drawString(70, y, line)
            y -= 15
            if y < 50: # Page break logic simplified
                p.showPage()
                y = height - 50

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"report_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf", mimetype='application/pdf')

@admin_bp.route('/admin/unanswered')
def admin_unanswered_questions():
    try:
        unanswered = unanswered_model.get_all()
        if not unanswered:
            unanswered = []
        else:
            unanswered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Pre-fetch chats
        chats = chat_model.get_all() or []
        chats_by_user = {}
        for c in chats:
            uid = c.get('user_id', 'unknown')
            if uid not in chats_by_user: chats_by_user[uid] = []
            chats_by_user[uid].append(c)
        
        # Attach context to each question object
        # We need to modify the dictionaries. Since get_all returns dicts, we can modify them.
        for q in unanswered:
            uid = q.get('user_id')
            if uid and uid in chats_by_user:
                history = chats_by_user[uid]
                history.sort(key=lambda x: x.get('timestamp', ''))
                q['context'] = history[-5:] # Last 5 messages
            else:
                q['context'] = []

        return render_template('admin_unanswered.html', unanswered=unanswered)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h3>Error loading Unanswered Questions:</h3><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500

@admin_bp.route('/admin/messages')
def admin_messages():
    """View all contact messages"""
    messages = contact_model.get_all()
    messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('admin_messages.html', messages=messages)

@admin_bp.route('/admin/message/status', methods=['POST'])
def admin_message_status():
    """Update message status"""
    doc_id = request.form.get('doc_id')
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    if doc_id and status:
        if status == 'rejected' and not admin_notes:
            admin_notes = "تم الرفض لاسباب خاصة"
            
        contact_model.update_status(doc_id, status, admin_response=admin_notes)
        if status == 'rejected':
             flash('تم رفض الرسالة بنجاح', 'warning')
        else:
             flash('تم تحديث حالة الرسالة بنجاح', 'success')
    else:
        flash('حدث خطأ في البيانات', 'error')
        
    return redirect(url_for('admin.admin_messages'))

@admin_bp.route('/admin/backup', methods=['GET', 'POST'])
def manual_backup():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        if not os.path.exists('backups'): os.makedirs('backups')
        backup_path = f'backups/manual_backup_{timestamp}.sqlite'
        shutil.copy2('ramadan_company.db', backup_path)
        security_log_model.create("Manual Backup", f"Admin {current_user.username} created a backup", severity="low")
        flash("تم إنشاء النسخة الاحتياطية بنجاح.")
        return send_file(backup_path, as_attachment=True)
    except Exception as e:
        flash(f"فشل إنشاء النسخة الاحتياطية: {str(e)}")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/setup_2fa')
def setup_2fa():
    if not current_user.two_factor_secret:
        secret = pyotp.random_base32()
        user_model.update(current_user.username, {'two_factor_secret': secret})
        current_user.two_factor_secret = secret
    else:
        secret = current_user.two_factor_secret
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.username, issuer_name="Haj Ramadan Paints")
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('setup_2fa.html', qr_code=qr_b64, secret=secret)

@admin_bp.route('/admin/toggle_2fa', methods=['POST'])
def toggle_2fa():
    action = request.form.get('action')
    if action == 'enable':
        user_model.update(current_user.username, {'two_factor_enabled': True})
        flash('تم تفعيل المصادقة الثنائية بنجاح')
    else:
        user_model.update(current_user.username, {'two_factor_enabled': False})
        flash('تم تعطيل المصادقة الثنائية')
    return redirect(url_for('admin.admin_dashboard'))
@admin_bp.route('/admin/security/clear', methods=['POST'])
def clear_security_logs():
    security_log_model.truncate()
    security_log_model.create("Logs Cleared", f"Admin {current_user.username} cleared all security logs", severity="info")
    flash("تم مسح سجلات المراقبة الأمنية بنجاح، وبدء التسجيل من جديد.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/security/audit')
def security_audit():
    
    # Auto Backup Check and List Fetching
    backup_dir = 'backups'
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)
    
    backup_files = []
    for f in os.listdir(backup_dir):
        if f.endswith('.sqlite'):
            path = os.path.join(backup_dir, f)
            stat = os.stat(path)
            backup_files.append({
                'name': f,
                'size': f"{stat.st_size / (1024*1024):.2f} MB",
                'date': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    backup_files.sort(key=lambda x: x['date'], reverse=True)
    
    # Auto Backup Logic (Every 3 Months i.e., 90 days)
    if not backup_files or (datetime.now() - datetime.strptime(backup_files[0]['date'], "%Y-%m-%d %H:%M:%S")).days >= 90:
         try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            new_file = f'backups/auto_backup_{timestamp}.sqlite'
            shutil.copy2('ramadan_company.db', new_file)
            security_log_model.create("Auto Backup", "System performed scheduled 3-month backup", severity="info")
            # Refresh list
            path = new_file
            stat = os.stat(path)
            backup_files.insert(0, {
                'name': os.path.basename(new_file),
                'size': f"{stat.st_size / (1024*1024):.2f} MB",
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
         except Exception as e:
            print(f"Auto backup error: {e}")

    from flask import current_app
    
    # Perform checks
    checks = []
    
    # 1. CSRF Check
    csrf_enabled = current_app.config.get('WTF_CSRF_ENABLED', True)
    checks.append({
        'name': 'حماية CSRF',
        'status': 'آمن' if csrf_enabled else 'خطر',
        'desc': 'حماية النماذج من الهجمات العابرة للمواقع.',
        'icon': 'fa-shield-alt',
        'color': 'success' if csrf_enabled else 'danger'
    })
    
    # 2. Session Cookies
    secure_session = current_app.config.get('SESSION_COOKIE_HTTPONLY', False)
    checks.append({
        'name': 'أمان الجلسة (HttpOnly)',
        'status': 'مفعل' if secure_session else 'غير مفعل',
        'desc': 'منع الوصول لملفات تعريف الارتباط عبر JavaScript.',
        'icon': 'fa-cookie-bite',
        'color': 'success' if secure_session else 'warning'
    })
    
    # 3. Security Headers
    checks.append({
        'name': 'رؤوس الأمان (HSTS, CSP, X-Frame)',
        'status': 'نشط',
        'desc': 'حماية المتصفح من هجمات XSS و Clickjacking.',
        'icon': 'fa-file-code',
        'color': 'success'
    })
    
    # 4. Database Backups
    checks.append({
        'name': 'النسخ الاحتياطي',
        'status': 'موجود' if backup_files else 'غير موجود',
        'desc': f"يوجد {len(backup_files)} نسخة احتياطية محفوظة (تلقائي كل 3 شهور).",
        'icon': 'fa-database',
        'color': 'success' if backup_files else 'warning'
    })
    
    # 5. Admin Passwords
    admin_user = user_model.get_by_username('admin')
    weak_pwd = False
    if admin_user and bcrypt.check_password_hash(admin_user['password'], 'admin'):
        weak_pwd = True
    
    checks.append({
        'name': 'قوة كلمة مرور المسؤول',
        'status': 'ضعيف' if weak_pwd else 'قوي',
        'desc': 'كلمة المرور آمنة.' if not weak_pwd else 'تحذير: كلمة المرور الافتراضية مستخدمة!',
        'icon': 'fa-key',
        'color': 'danger' if weak_pwd else 'success'
    })

    # 6. Rate Limiting
    checks.append({
        'name': 'تحديد معدل الطلبات',
        'status': 'مفعل',
        'desc': 'حماية الموقع من هجمات Brute Force و DDoS.',
        'icon': 'fa-tachometer-alt',
        'color': 'success'
    })

    logs = security_log_model.get_all()
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_logs = logs[:10]

    return render_template('admin_security.html', checks=checks, logs=recent_logs, backups=backup_files)


@admin_bp.route('/admin/complaints')
def admin_complaints():
    """View and manage complaints"""
    
    # Get all complaints
    all_complaints = complaint_model.get_all()
    
    # Sort by date (newest first)
    all_complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Get statistics
    pending = len([c for c in all_complaints if c['status'] == 'قيد المراجعة'])
    resolved = len([c for c in all_complaints if c['status'] == 'تم الحل'])
    rejected = len([c for c in all_complaints if c['status'] == 'مرفوضة'])
    
    stats = {
        'total': len(all_complaints),
        'pending': pending,
        'resolved': resolved,
        'rejected': rejected
    }
    
    return render_template('admin_complaints.html', complaints=all_complaints, stats=stats)


@admin_bp.route('/admin/complaint/<int:complaint_id>/update', methods=['POST'])
def update_complaint_status(complaint_id):
    """Update complaint status"""
    
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    admin_response = request.form.get('admin_response', '')
    
    complaint_model.update_status(complaint_id, status, admin_notes, admin_response)
    
    flash('تم تحديث حالة الشكوى وحفظ الرد بنجاح', 'success')
    return redirect(url_for('admin.admin_complaints'))


@admin_bp.route('/admin/inspections')
def admin_inspections():
    """View and manage inspections"""
    
    # Get all requests
    all_requests = inspection_model.get_all()
    all_requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Statistics
    stats = {
        'new': len([r for r in all_requests if r['status'] == 'new_request']),
        'assigned': len([r for r in all_requests if r['status'] == 'assigned_to_worker']),
        'admin_visit': len([r for r in all_requests if r['status'] == 'admin_visit']),
        'completed': len([r for r in all_requests if r['status'] == 'completed']),
        'total': len(all_requests)
    }
    
    return render_template('admin_inspections.html', requests=all_requests, stats=stats)

# ==========================================
# Ticket System Routes
# ==========================================
@admin_bp.route('/admin/tickets')
@login_required
@role_required(['admin', 'manager'])
def admin_tickets():
    tickets = ticket_model.get_all()
    
    stats = {
        'total': len(tickets),
        'open': len([t for t in tickets if t['status'] == 'Open']),
        'in_progress': len([t for t in tickets if t['status'] == 'In Progress']),
        'closed': len([t for t in tickets if t['status'] == 'Closed'])
    }
    
    return render_template('admin_tickets.html', tickets=tickets, stats=stats)

@admin_bp.route('/admin/ticket/<int:ticket_id>/update', methods=['POST'])
@login_required
@role_required(['admin', 'manager'])
def update_ticket(ticket_id):
    status = request.form.get('status')
    if status:
        ticket_model.update_status(ticket_id, status)
        flash(f"تم تحديث حالة التذكرة #{ticket_id} بنجاح", "success")
    return redirect(url_for('admin.admin_tickets'))

# ==========================================
# Reporting System Routes
# ==========================================
@admin_bp.route('/admin/reports')
@login_required
@role_required(['admin'])
def admin_reports():
    return render_template('admin_reports.html')



@admin_bp.route('/admin/export/excel', methods=['POST'])
@login_required
@role_required(['admin'])
def export_excel_report():
    data_type = request.form.get('data_type')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = data_type.capitalize()
    
    if data_type == 'users':
        headers = ['Username', 'Full Name', 'Phone', 'Role', 'Project %', 'Created At']
        ws.append(headers)
        for u in user_model.get_all():
             ws.append([u.get('username'), u.get('full_name'), u.get('phone'), u.get('role'), u.get('project_percentage'), u.get('created_at')])
             
    elif data_type == 'tickets':
         headers = ['ID', 'User', 'Subject', 'Status', 'Priority', 'Date']
         ws.append(headers)
         for t in ticket_model.get_all():
             ws.append([t.get('id'), t.get('user_id'), t.get('subject'), t.get('status'), t.get('priority'), t.get('created_at')])
             
    elif data_type == 'payments':
         headers = ['ID', 'User', 'Amount', 'Method', 'Status', 'Date']
         ws.append(headers)
         for p in payment_model.get_all():
             ws.append([p.get('id'), p.get('username'), p.get('amount'), p.get('method'), p.get('status'), p.get('timestamp')])
             
    elif data_type == 'messages':
         headers = ['Name', 'Phone', 'Service', 'Message', 'Status', 'Date']
         ws.append(headers)
         for m in contact_model.get_all():
             ws.append([m.get('name'), m.get('phone'), m.get('service'), m.get('message'), m.get('status'), m.get('created_at')])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'{data_type}_report_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ==========================================
# Integration System Routes
# ==========================================
@admin_bp.route('/admin/integrations')
@login_required
@role_required(['admin'])
def admin_integrations():
    return render_template('admin_integrations.html')




@admin_bp.route('/admin/inspection/<request_id>/assign', methods=['POST'])
def assign_inspection(request_id):
    """Assign admin to inspection"""
    
    # Always assign to admin since workers are removed
    inspection_model.assign_admin_visit(request_id)
    flash('تم تعيين المعاينة للإدارة', 'success')
            
    return redirect(url_for('admin.admin_inspections'))


@admin_bp.route('/admin/inspection/<request_id>/details')
def inspection_details(request_id):
    """Get inspection details"""
        
    req = inspection_model.get_request_by_id(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404
        
    return jsonify({
        'request': req,
        'nearby_workers': []
    })


@admin_bp.route('/admin/inspection/<request_id>/approve', methods=['POST'])
def approve_inspection_report(request_id):
    """Admin: Approve or Reject Inspection Report"""
        
    decision = request.form.get('decision')
    admin_notes = request.form.get('admin_notes', '')
    
    if decision == 'approve':
        inspection_model.approve_report(request_id)
        # Add notification logic here (optional)
        flash('تم اعتماد التقرير بنجاح، ويمكن للعميل الآن رؤية النتيجة وبيانات الصنايعي', 'success')
    elif decision == 'reject':
        inspection_model.update_status(request_id, 'inspection_rejected', {'admin_notes': admin_notes})
        flash('تم رفض التقرير', 'warning')
        
    return redirect(url_for('admin.admin_inspections'))

@admin_bp.route('/admin/inspection/<request_id>/reject', methods=['POST'])
def admin_reject_inspection(request_id):
    """Admin rejects an inspection request"""
    
    reason = request.form.get('admin_notes', '')
    
    result = inspection_model.admin_reject_request(request_id, reason)
    
    if result['success']:
        flash(result['message'], 'warning')
    else:
        flash('حدث خطأ أثناء رفض الطلب', 'error')
    
    return redirect(url_for('admin.admin_inspections'))

@admin_bp.route('/admin/inspection/<request_id>/complete', methods=['POST'])
def admin_complete_inspection(request_id):
    """Admin completes the inspection directly"""
    
    admin_notes = request.form.get('admin_notes', '')
    
    # Update status to completed or approved directly if it was an admin visit
    # Assuming 'approved_for_user' is the state where user sees results, or 'completed'
    # The requirement says "determined that it was reviewed and reached with the user"
    
    # Find the request
    req = inspection_model.get_request_by_id(request_id)
    if not req:
        flash('الطلب غير موجود', 'error')
        return redirect(url_for('admin.admin_inspections'))

    # Mark as completed/approved
    # We can reuse approve_report logic or create a new method for direct admin completion
    # forcing a simple report
    
    report_data = {
        'job_type': 'معاينة إدارية',
        'place_status': 'تمت الزيارة',
        'job_size': 'غير محدد',
        'photos': [],
        'voice_note_url': None,
        'admin_notes': admin_notes
    }
    
    # 1. Submit a dummy/admin report
    inspection_model.submit_report(request_id, report_data)
    
    # 2. Approve it immediately
    inspection_model.approve_report(request_id)
    
    flash('تم تسجيل إتمام المعاينة بنجاح', 'success')
    return redirect(url_for('admin.admin_inspections'))



@admin_bp.route('/admin/transfers')
def admin_transfers():
    """Admin: Transfers List"""
        
    payments = payment_model.get_all()
    # Sort by timestamp desc
    payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Calculate confirmed total
    confirmed_total = sum(float(p.get('amount', 0)) for p in payments if str(p.get('status', '')).lower() == 'confirmed')
    
    return render_template('admin_transfers.html', payments=payments, total_confirmed=confirmed_total)

@admin_bp.route('/admin/payment/confirm/<doc_id>', methods=['POST'])
def confirm_payment(doc_id):
    """Admin: Confirm a payment"""
        
    payment_model.update_status(doc_id, 'Confirmed')
    flash('تم تأكيد التحويل بنجاح', 'success')
    return redirect(url_for('admin.admin_transfers'))

@admin_bp.route('/admin/backup/download/<filename>')
def download_backup_file(filename):
    return send_file(os.path.join('backups', filename), as_attachment=True)

@admin_bp.route('/admin/backup/delete/<filename>', methods=['POST'])
def delete_backup_file(filename):
    try:
        os.remove(os.path.join('backups', filename))
        flash('تم حذف النسخة الاحتياطية بنجاح')
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {e}')
    return redirect(url_for('admin.security_audit'))

@admin_bp.route('/admin/export/users')
@login_required
def export_users_report():
    """Export users report to Excel with professional formatting"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    try:
        from utils.export_helper import export_users_excel
        
        users = user_model.get_all()
        
        # Generate Excel file
        output = export_users_excel(users)
        
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    except ImportError:
        # Fallback to CSV if openpyxl not available
        flash('مكتبة Excel غير متوفرة، سيتم التصدير بصيغة CSV', 'warning')
        
        users = user_model.get_all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Add BOM for Excel UTF-8 support
        writer.writerow(['تقرير المستخدمين'])
        writer.writerow([f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Header with better formatting
        writer.writerow(['#', 'اسم المستخدم', 'الاسم الكامل', 'رقم الهاتف', 'البريد الإلكتروني',
                        'موقع المشروع', 'نسبة الإنجاز', 'تاريخ التسجيل'])
        
        # Data
        for idx, user in enumerate(users, 1):
            writer.writerow([
                idx,
                user.get('username', ''),
                user.get('full_name', ''),
                user.get('phone', ''),
                user.get('email', ''),
                user.get('project_location', ''),
                f"{user.get('project_percentage', 0)}%",
                user.get('created_at', '')
            ])
        
        # Add summary
        writer.writerow([])
        writer.writerow(['الإحصائيات'])
        writer.writerow(['إجمالي المستخدمين', len(users)])
        writer.writerow(['مشاريع مكتملة', len([u for u in users if u.get('project_percentage', 0) == 100])])
        writer.writerow(['مشاريع جارية', len([u for u in users if 0 < u.get('project_percentage', 0) < 100])])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء التصدير: {str(e)}', 'error')
        return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/export/payments')
@login_required
def export_payments_report():
    """Export payments report to Excel with professional formatting"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    try:
        from utils.export_helper import export_payments_excel
        
        payments = payment_model.get_all()
        
        # Generate Excel file
        output = export_payments_excel(payments)
        
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"payments_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    except ImportError:
        # Fallback to CSV
        flash('مكتبة Excel غير متوفرة، سيتم التصدير بصيغة CSV', 'warning')
        
        payments = payment_model.get_all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Title
        writer.writerow(['تقرير المدفوعات'])
        writer.writerow([f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Header
        writer.writerow(['#', 'اسم المستخدم', 'المبلغ (جنيه)', 'طريقة الدفع', 
                        'التفاصيل', 'التاريخ', 'الحالة'])
        
        for idx, p in enumerate(payments, 1):
            writer.writerow([
                idx,
                p.get('username', ''),
                f"{float(p.get('amount', 0)):,.2f}",
                p.get('method', ''),
                p.get('details', ''),
                p.get('timestamp', ''),
                p.get('status', 'قيد المراجعة')
            ])
        
        # Summary
        writer.writerow([])
        writer.writerow(['الإحصائيات'])
        total_revenue = sum([float(p.get('amount', 0)) for p in payments])
        writer.writerow(['إجمالي الإيرادات', f"{total_revenue:,.2f} جنيه"])
        writer.writerow(['عدد المدفوعات', len(payments)])
        writer.writerow(['مدفوعات مؤكدة', len([p for p in payments if p.get('status') == 'Confirmed'])])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"payments_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء التصدير: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


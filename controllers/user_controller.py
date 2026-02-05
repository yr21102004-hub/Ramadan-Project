from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import UserModel, ContactModel, PaymentModel, ChatModel, UnansweredQuestionsModel, SubscriptionModel, ComplaintModel, RatingModel, TicketModel, TicketMessageModel
from websockets import notify_admins, broadcast_percentage_update
from utils.email_sender import send_email

user_bp = Blueprint('user', __name__)
bcrypt = Bcrypt()
user_model = UserModel()
contact_model = ContactModel()
payment_model = PaymentModel()
chat_model = ChatModel()
unanswered_model = UnansweredQuestionsModel()
subscription_model = SubscriptionModel()
complaint_model = ComplaintModel()
rating_model = RatingModel()
ticket_model = TicketModel()
ticket_message_model = TicketMessageModel()

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email', '')
        project_description = request.form.get('project_description', 'لا يوجد وصف للمشروع')
        
        # Handle profile image upload
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
        
        # Check if user exists
        if user_model.get_by_username(username):
            flash('اسم المستخدم مسجل بالفعل')
            return redirect(url_for('user.register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # First user is admin, otherwise use selected role
        all_users = user_model.get_all()
        if len(all_users) == 0:
            role = 'admin'
        else:
            role = request.form.get('role', 'user')
            
        # Create user
        user_data = {
            'username': username,
            'password': hashed_password,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'role': role,
            'profile_image': profile_image_path,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if role == 'worker':
            user_data.update({
                'specialization': request.form.get('specialization'),
                'experience_years': request.form.get('experience_years', 0),
                'status': 'available' # Default status for workers
            })
        else:
            user_data.update({
                'project_location': 'غير محدد',
                'project_description': project_description,
                'project_percentage': 0
            })
            
        user_model.create(user_data)
        
        # Notify admins
        notify_admins('new_user', {
            'username': username,
            'full_name': full_name
        })
        
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')


@user_bp.route('/user/<username>')
def profile(username):
    """Get user profile"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if current_user.role != 'admin' and current_user.username != username:
        return "Access Denied", 403
        
    user_data = user_model.get_by_username(username)
    if not user_data:
        return "User not found", 404
        
    # If worker, render worker dashboard
    if user_data.get('role') == 'worker':
        worker_obj = {
            'full_name': user_data.get('full_name'),
            'username': user_data.get('username'),
            'email': user_data.get('email', 'لا يوجد'),
            'phone': user_data.get('phone'),
            'profile_image': user_data.get('profile_image'),
            'specialization': user_data.get('specialization'),
            'experience_years': user_data.get('experience_years'),
            'status': user_data.get('status', 'available'),
            'created_at': user_data.get('created_at')
        }
        return render_template('worker_dashboard.html', worker=worker_obj)

    # Standard User Dashboard logic
    try:
        user_obj = {
            'id': user_data.get('id'),
            'role': user_data.get('role'),
            'full_name': user_data.get('full_name'),
            'username': user_data.get('username'),
            'email': user_data.get('email', 'لا يوجد'),
            'phone': user_data.get('phone'),
            'profile_image': user_data.get('profile_image'),
            'project_location': user_data.get('project_location', 'غير محدد'),
            'project_description': user_data.get('project_description', 'لا يوجد وصف'),
            'project_percentage': user_data.get('project_percentage', 0),
            'chat_memory_enabled': user_data.get('chat_memory_enabled', 1),
            'created_at': user_data.get('created_at')
        }
        
        # Fetch user's previous requests (Inquiries/Inspections)
        user_requests = contact_model.get_by_user(username) or []
        user_requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Fetch user's payments
        user_payments = payment_model.get_by_user(username) or []
        user_payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Fetch user's chat history
        user_chats = chat_model.get_by_user(username) or []
        user_chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Fetch user's unanswered questions (Pending AI questions)
        user_unanswered = unanswered_model.get_by_user(username) or []
        user_unanswered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Fetch user's subscriptions
        user_subscriptions = subscription_model.get_by_user(username) or []

        # Fetch user's complaints
        user_complaints = complaint_model.get_by_user(username) or []
        user_complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Fetch Project Rating
        project_rating = rating_model.get_user_project_rating(username)

        # Smart User Insights (Timeline) - Admin Only
        user_timeline = []
        if current_user.role == 'admin':
            # Add Registration
            if user_data.get('created_at'):
                user_timeline.append({'type': 'register', 'date': user_data.get('created_at'), 'details': 'تسجيل حساب جديد'})
            
            # Add Payments
            for p in user_payments:
                user_timeline.append({'type': 'payment', 'date': p.get('timestamp'), 'details': f"دفع {p.get('amount')} ج.م ({p.get('status')})"})
                
            # Add Requests
            for r in user_requests:
                user_timeline.append({'type': 'request', 'date': r.get('created_at'), 'details': f"طلب {r.get('service')}: {r.get('message')[:30]}..."})

            # Add Complaints
            for c in user_complaints:
                user_timeline.append({'type': 'complaint', 'date': c.get('created_at'), 'details': f"شكوى: {c.get('subject')}"})
            
            # Add Unanswered Questions (as indicators of interest)
            for q in user_unanswered:
                user_timeline.append({'type': 'question', 'date': q.get('timestamp'), 'details': f"سؤال: {q.get('question')}"})
                
            # Add Completed Project
            if user_data.get('project_percentage') == 100:
                 # We don't have exact completion date, assume last update or arbitrary
                 pass

            # Sort by date descending
            user_timeline.sort(key=lambda x: x.get('date', ''), reverse=True)

        return render_template('user_dashboard.html', 
                            user=user_obj, 
                            requests=user_requests,
                            payments=user_payments,
                            chats=user_chats,
                            unanswered=user_unanswered,
                            subscriptions=user_subscriptions,
                            complaints=user_complaints,
                            project_rating=project_rating,
                            timeline=user_timeline)

    except Exception as e:
        print(f"Error accessing profile for {username}: {e}")
        import traceback
        traceback.print_exc()
        return f"<h3>حدث خطأ أثناء تحميل الملف الشخصي:</h3><p>{str(e)}</p>", 500


@user_bp.route('/admin/update_project_percentage', methods=['POST'])
def update_percentage():
    """Update user project percentage"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('عذراً، هذه العملية مخصصة للإدارة فقط.', 'warning')
        return redirect(url_for('index'))
        
    username = request.form.get('username')
    percentage = request.form.get('percentage')
    
    try:
        percentage = int(percentage)
        if percentage < 0: percentage = 0
        if percentage > 100: percentage = 100
    except:
        percentage = 0
        
    user_model.update(username, {'project_percentage': percentage})
    
    # Broadcast update via WebSocket
    broadcast_percentage_update(username, percentage)
    
    # Send Email Notification
    try:
        user_info = user_model.get_by_username(username)
        if user_info and user_info.get('email'):
            send_email(
                user_info['email'],
                "تحديث حالة مشروعك - RMG Decor",
                f"""
                <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h3 style="color: #333;">مرحباً {user_info['full_name']}،</h3>
                    <p>يسعدنا إخبارك بأنه تم تحديث نسبة إنجاز مشروعك لتصبح:</p>
                    <h2 style="color: #D4AF37; margin: 20px 0;">{percentage}%</h2>
                    <p>يمكنك الدخول إلى <a href="{url_for('auth.login', _external=True)}">لوحة التحكم</a> لمتابعة المزيد من التفاصيل والصور.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #888; font-size: 12px;">مؤسسة الحاج رمضان محمد جبر للديكور والتشطيبات</p>
                </div>
                """
            )
    except Exception as e:
        print(f"Failed to send email: {e}")
    
    flash(f"تم تحديث نسبة الإنجاز للعميل {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))


@user_bp.route('/admin/delete_user/<username>', methods=['POST'])
def delete(username):
    """Delete user"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('عذراً، هذه العملية مخصصة للإدارة فقط.', 'warning')
        return redirect(url_for('index'))

    user_model.delete(username)
    flash(f"تم حذف المستخدم {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))

@user_bp.route('/user/submit_complaint', methods=['POST'])
@login_required
def submit_complaint():
    """Submit a new complaint"""
    subject = request.form.get('subject')
    message = request.form.get('message')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    if not subject or not message:
        flash('يرجى ملء موضوع وتفاصيل الشكوى.')
        return redirect(url_for('user.profile', username=current_user.username))
        
    complaint_model.create(
        username=current_user.username,
        subject=subject,
        message=message,
        phone=phone,
        email=email
    )
    
    flash('تم تسجيل شكواك بنجاح. سيتم مراجعتها من قبل الإدارة والرد عليك هنا.', 'success')
    return redirect(url_for('user.profile', username=current_user.username))

@user_bp.route('/user/rate_project', methods=['POST'])
@login_required
def submit_project_rating():
    """Submit rating for finished project with optional image"""
    if current_user.role != 'user':
        return "Access Denied", 403
        
    # Verify completion
    if current_user.project_percentage != 100:
        flash("لا يمكن تقديم تقييم إلا بعد اكتمال المشروع بنسبة 100%.", 'error')
        return redirect(url_for('user.profile', username=current_user.username))
        
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    try:
        rating = int(rating)
        if not (1 <= rating <= 5): raise ValueError
    except:
        flash("التقييم يجب أن يكون بين 1 و 5 نجوم.", 'error')
        return redirect(url_for('user.profile', username=current_user.username))

    # Handle Image Upload
    image_path = None
    if 'review_image' in request.files:
        file = request.files['review_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"review_{current_user.username}_{timestamp}.{file_extension}"
            
            # Save in static/user_images (or create distinct folder)
            upload_folder = os.path.join('static', 'user_images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            image_path = f"user_images/{unique_filename}"
            
    try:
        # Use our new RatingModel
        rating_model.create(
            username=current_user.username,
            user_id=str(current_user.id),
            quality_rating=rating,
            behavior_rating=rating, # Simplified for now
            comment=comment,
            image_path=image_path
        )
        flash("شكراً لك! تم استلام تقييمك بنجاح.", 'success')
    except Exception as e:
        flash(f"حدث خطأ أثناء حفظ التقييم: {e}", 'error')
        
    return redirect(url_for('user.profile', username=current_user.username))

@user_bp.route('/user/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    """Clear user chat history (Soft Delete)"""
    try:
        chat_model.soft_delete_all(current_user.username)
        return jsonify({'success': True, 'message': 'تم مسح سجل المحادثة بنجاح.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/user/toggle_memory', methods=['POST'])
@login_required
def toggle_memory():
    """Toggle chat memory setting"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        # Update user setting
        # SQLite stores booleans as 1/0
        user_model.update(current_user.username, {'chat_memory_enabled': 1 if enabled else 0})
        
        # If disabled (closing memory), HARD DELETE existing chats so admin cannot see them either
        if not enabled:
            chat_model.hard_delete_all(current_user.username)
            
        msg = "تم تفعيل ذاكرة المحادثة." if enabled else "تم تعطيل الذاكرة وحذف جميع المحادثات نهائياً."
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/user/submit_ticket', methods=['POST'])
@login_required
def submit_ticket():
    subject = request.form.get('subject')
    category = request.form.get('category')
    priority = request.form.get('priority')
    message = request.form.get('message')
    
    if not subject or not message:
        flash("يرجى ملء جميع الحقول", "error")
        return redirect(url_for('user.user_tickets'))
        
    try:
        # Create Ticket
        ticket_id = ticket_model.create(current_user.username, subject, category, priority)
        
        # Add Initial Message
        ticket_message_model.insert({
            'ticket_id': ticket_id,
            'sender_id': current_user.username,
            'message': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_admin_reply': 0
        })
        
        # Email Notification (To Admin)
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        # Use helper
        send_email(admin_email, f"New Ticket #{ticket_id} from {current_user.username}", 
                   f"<p>User <b>{current_user.username}</b> created a new ticket:</p><h3>{subject}</h3><p>{message}</p>")
        
        flash("تم إنشاء التذكرة بنجاح", "success")
    except Exception as e:
        flash(f"حدث خطأ: {e}", "error")
        
    return redirect(url_for('user.user_tickets'))

@user_bp.route('/user/tickets')
@login_required
def user_tickets():
    my_tickets = ticket_model.get_by_user(current_user.username)
    return render_template('user_tickets.html', tickets=my_tickets)

import sys
import os

# Add the current directory to path
sys.path.append(os.getcwd())

from flask import Flask
from models import UserModel, ChatModel, ContactModel, SecurityLogModel, UnansweredQuestionsModel, Database
from collections import Counter
from datetime import datetime

# Initialize app just for context if needed
app = Flask(__name__)

# Initialize models
user_model = UserModel()
chat_model = ChatModel()
contact_model = ContactModel()
security_log_model = SecurityLogModel()
unanswered_model = UnansweredQuestionsModel()

def test_logic():
    try:
        print("Fetching data...")
        users = user_model.get_all()
        messages = contact_model.get_all()
        chats = chat_model.get_all()
        sec_logs = security_log_model.get_all()
        unanswered = unanswered_model.get_all()
        print(f"Data fetched: Users={len(users)}, Messages={len(messages)}, Chats={len(chats)}, Logs={len(sec_logs)}, Unanswered={len(unanswered)}")

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
        print("Frequent AI done")

        # 3. Top Visitors
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
        print("Top visitors done")

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
        print("Daily visitors done")

        # 5. Top Requested Services
        service_counts = Counter([str(m.get('service', 'general')) for m in messages])
        print("Services req done")
        
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
        print("Services viewed done")

        # 7. Peak Hours
        hour_counts = Counter()
        for l in sec_logs:
            ts = str(l.get('timestamp', ''))
            if ts and ' ' in ts:
                try:
                    hour = ts.split(' ')[1].split(':')[0]
                    hour_counts[hour] += 1
                except: pass
        print("Peak hours done")

        # 8. AI Efficiency
        total_ai_msgs = len(chats)
        unanswered_msgs = len(unanswered)
        answered_msgs = max(0, total_ai_msgs - unanswered_msgs)
        print("AI Efficiency done")

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
        print("Page popularity done")
        
        print("All logic passed successfully!")
        
    except Exception as e:
        print(f"FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logic()

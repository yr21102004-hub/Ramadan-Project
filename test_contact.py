from app import app
from flask import url_for

with app.app_context():
    with app.test_request_context():
        try:
            # Manually trigger render
            from flask import render_template
            rendered = render_template('contact.html')
            print("Contact rendered successfully")
        except Exception as e:
            print(f"Error rendering contact: {e}")
            import traceback
            traceback.print_exc()


try:
    from controllers.web_controller import web_bp
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")


import os
from PIL import Image

def convert_to_webp(directory):
    for filename in os.listdir(directory):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            input_path = os.path.join(directory, filename)
            output_path = os.path.join(directory, os.path.splitext(filename)[0] + ".webp")
            
            # Skip if webp already exists and is newer
            if os.path.exists(output_path) and os.path.getmtime(output_path) > os.path.getmtime(input_path):
                continue
                
            try:
                with Image.open(input_path) as img:
                    img.save(output_path, "WEBP", quality=85)
            except Exception as e:
                pass

if __name__ == "__main__":
    directories = [
        "static",
        "static/assets",
        "static/user_images"
    ]
    for d in directories:
        if os.path.exists(d):
            print(f"Processing directory: {d}")
            convert_to_webp(d)
    print("Done!")

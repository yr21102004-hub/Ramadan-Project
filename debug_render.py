
import requests
import re

try:
    response = requests.get('http://127.0.0.1:5000/project/villas')
    content = response.text
    
    # Look for the project-hero section style
    match = re.search(r'class="project-hero"[^>]*style="([^"]*)"', content)
    if match:
        print("Hero Style Found:")
        print(match.group(1))
    else:
        print("Hero Style NOT Found")
        
    print("-" * 20)
    
    # Look for the section-padding class
    match_section = re.search(r'class="section-padding ([^"]*)"', content)
    if match_section:
        print("Section Classes Found:")
        print(match_section.group(1))

except Exception as e:
    print(f"Error: {e}")

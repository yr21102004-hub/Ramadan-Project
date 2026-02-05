
import svgwrite

def create_hotels_special_bg():
    # Art Deco Diamond Pattern matching the user's request
    # Dark Navy Blue background, Gold lines
    dwg = svgwrite.Drawing('static/assets/luxury_bg_hotels_v2.svg', profile='full', size=('100%', '100%'))
    
    navy_blue = '#081026' # Deep Navy
    gold = '#D4AF37'
    gold_light = '#F3D778'
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill=navy_blue))
    
    # Define Pattern
    pattern_width = 100
    pattern_height = 100
    pattern = dwg.defs.add(dwg.pattern(id='artdeco_diamonds', size=(pattern_width, pattern_height), patternUnits="userSpaceOnUse"))
    
    # Pattern Background (to ensure seamless)
    pattern.add(dwg.rect(insert=(0,0), size=(pattern_width, pattern_height), fill=navy_blue))
    
    # Diamond Cluster Group
    g = pattern.add(dwg.g(stroke=gold, stroke_width=1.5, fill='none'))
    
    # Main Diamond (Centered)
    # M 50 0 L 100 50 L 50 100 L 0 50 Z
    g.add(dwg.path(d="M50 10 L90 50 L50 90 L10 50 Z", stroke_width=2))
    
    # Inner Diamond
    g.add(dwg.path(d="M50 20 L80 50 L50 80 L20 50 Z", stroke_width=1))
    
    # Vertical Lines inside (Organ pipe effect)
    # Center line
    g.add(dwg.line(start=(50, 20), end=(50, 80), stroke_width=0.5))
    # Side lines
    g.add(dwg.line(start=(40, 30), end=(40, 70), stroke_width=0.5))
    g.add(dwg.line(start=(60, 30), end=(60, 70), stroke_width=0.5))
    g.add(dwg.line(start=(30, 40), end=(30, 60), stroke_width=0.5))
    g.add(dwg.line(start=(70, 40), end=(70, 60), stroke_width=0.5))

    # Corner Diamonds (to tile correctly)
    # Top Left
    g.add(dwg.path(d="M0 0 L40 0 L0 40 Z", stroke_width=1)) # Half diamond
    
    # Connecting Lines (The X shape between diamonds)
    g.add(dwg.line(start=(0, 0), end=(100, 100), stroke=gold_light, stroke_width=0.5, opacity=0.3))
    g.add(dwg.line(start=(100, 0), end=(0, 100), stroke=gold_light, stroke_width=0.5, opacity=0.3))

    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill='url(#artdeco_diamonds)'))
    dwg.save()

if __name__ == '__main__':
    create_hotels_special_bg()

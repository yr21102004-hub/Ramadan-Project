
import svgwrite

def create_villas_bg():
    dwg = svgwrite.Drawing('static/assets/luxury_bg_villas.svg', profile='full', size=('100%', '100%'))
    # Dark Background
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#050505'))
    
    # Gold Polygons / Triangles (Abstract)
    # INCREASED VISIBILITY: Thicker stroke, higher opacity
    gold = '#D4AF37'
    
    # Random-ish geometric lines
    lines = dwg.add(dwg.g(stroke=gold, stroke_width=5, opacity=0.8))
    
    # Diagonal lines - More Density
    lines.add(dwg.line(start=('0%', '0%'), end=('100%', '100%')))
    lines.add(dwg.line(start=('100%', '0%'), end=('0%', '100%')))
    lines.add(dwg.line(start=('20%', '0%'), end=('0%', '50%')))
    lines.add(dwg.line(start=('80%', '0%'), end=('100%', '50%')))
    
    dwg.save()

def create_apartments_bg():
    dwg = svgwrite.Drawing('static/assets/luxury_bg_apartments.svg', profile='full', size=('100%', '100%'))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#0A0A0A'))
    
    gold = '#D4AF37'
    # Nested Diamonds/Squares
    # INCREASED VISIBILITY
    shapes = dwg.add(dwg.g(stroke=gold, stroke_width=4, opacity=0.8, fill='none'))
    
    # Pattern definition
    pattern = dwg.defs.add(dwg.pattern(id='diamond', size=(200, 200), patternUnits="userSpaceOnUse"))
    pattern.add(dwg.rect(insert=(0,0), size=(200,200), fill='#0A0A0A'))
    # Thicker lines
    pattern.add(dwg.path(d="M100 0 L200 100 L100 200 L0 100 Z", stroke=gold, stroke_width=3, fill='none'))
    
    # Apply pattern
    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill='url(#diamond)'))
    
    dwg.save()

def create_factories_bg():
    dwg = svgwrite.Drawing('static/assets/luxury_bg_factories.svg', profile='full', size=('100%', '100%'))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#111111'))
    
    gold = '#D4AF37'
    
    # Industrial Lines / Stripes Pattern
    pattern = dwg.defs.add(dwg.pattern(id='stripes', size=(100, 100), patternUnits="userSpaceOnUse"))
    pattern.add(dwg.rect(insert=(0,0), size=(100,100), fill='#111111'))
    
    # Diagonal Stripes
    # Creating a group of diagonal lines
    g = pattern.add(dwg.g(stroke=gold, stroke_width=2, opacity=0.3))
    g.add(dwg.line(start=(0, 100), end=(100, 0)))
    g.add(dwg.line(start=(-20, 80), end=(80, -20))) # Extended for tiling
    
    # Tiny dots/sparks effect
    dots = pattern.add(dwg.g(fill=gold, opacity=0.5))
    dots.add(dwg.circle(center=(20, 20), r=1))
    dots.add(dwg.circle(center=(70, 60), r=1))
    dots.add(dwg.circle(center=(40, 80), r=1))

    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill='url(#stripes)'))
    
    dwg.save()

def create_companies_bg():
    dwg = svgwrite.Drawing('static/assets/luxury_bg_companies.svg', profile='full', size=('100%', '100%'))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#080C15'))
    
    gold = '#D4AF37'
    blue = '#1A2F4B'
    
    # Modern Corporate Pinstripes
    pattern = dwg.defs.add(dwg.pattern(id='pinstripe', size=(50, 50), patternUnits="userSpaceOnUse"))
    pattern.add(dwg.rect(insert=(0,0), size=(50,50), fill='#080C15'))
    
    # Vertical thin gold lines
    pattern.add(dwg.line(start=(25, 0), end=(25, 50), stroke=gold, stroke_width=0.5, opacity=0.3))
    
    # Subtle blue diagonal accents
    pattern.add(dwg.line(start=(0, 0), end=(50, 50), stroke=blue, stroke_width=2, opacity=0.2))

    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill='url(#pinstripe)'))
    
    # Large abstract arcs for "Network/Connection" feel
    arcs = dwg.add(dwg.g(stroke=gold, stroke_width=1, fill='none', opacity=0.1))
    arcs.add(dwg.circle(center=('50%', '50%'), r='30%'))
    arcs.add(dwg.circle(center=('50%', '50%'), r='45%'))

    dwg.save()

def create_hotels_bg():
    dwg = svgwrite.Drawing('static/assets/luxury_bg_hotels.svg', profile='full', size=('100%', '100%'))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#0A1020'))
    
    gold = '#D4AF37'
    
    # Art Deco Pattern (Simulated)
    pattern = dwg.defs.add(dwg.pattern(id='artdeco', size=(100, 100), patternUnits="userSpaceOnUse"))
    pattern.add(dwg.rect(insert=(0,0), size=(100,100), fill='#0A1020'))
    
    # Geometric Arches/Fans
    g = pattern.add(dwg.g(stroke=gold, stroke_width=2, fill='none', opacity=0.4))
    
    # Fan shape bottom left
    g.add(dwg.path(d="M0 100 Q 50 50 100 100"))
    g.add(dwg.path(d="M10 100 Q 50 60 90 100"))
    g.add(dwg.path(d="M20 100 Q 50 70 80 100"))
    
    # Fan shape top inverted
    g.add(dwg.path(d="M0 0 Q 50 50 100 0"))
    
    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill='url(#artdeco)'))
    
    dwg.save()

if __name__ == '__main__':
    create_villas_bg()
    create_apartments_bg()
    create_factories_bg()
    create_companies_bg()
    create_hotels_bg()

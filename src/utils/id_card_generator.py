import io
import os
import qrcode
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import current_app

# Design Constants
GOLD = colors.HexColor("#D4AF37")
BLACK = colors.HexColor("#000000")
DARK_GREY = colors.HexColor("#1a1a1a")
WHITE = colors.HexColor("#FFFFFF")

def generate_member_card_pdf(member, plan):
    """
    Generates a Mobile-First Vertical ID Card (54mm x 96mm).
    Features: Avatar placeholder, No expiry, ID under QR.
    """
    width, height = 54*mm, 96*mm
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # 1. Background
    c.setFillColor(BLACK)
    c.rect(0, 0, width, height, fill=1)
    
    # 2. Header Bar
    c.setFillColor(GOLD)
    c.rect(0, height - 8*mm, width, 8*mm, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width/2, height - 5.5*mm, "IRONLIFTER GYM")
    
    # 3. Avatar / Photo Logic
    photo_y = height - 40*mm
    photo_size = 24*mm  # Slightly smaller for cleaner look
    photo_x = (width - photo_size) / 2
    
    # Gold Ring
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.circle(width/2, photo_y + photo_size/2, photo_size/2 + 1*mm, stroke=1, fill=0)
    
    has_photo = False
    if member.photo_path:
        try:
            full_path = os.path.join(current_app.static_folder, member.photo_path.replace('static/', ''))
            if os.path.exists(full_path):
                # Draw User Photo
                c.drawImage(full_path, photo_x, photo_y, width=photo_size, height=photo_size, mask='auto')
                has_photo = True
        except:
            pass # Fallback to avatar
            
    if not has_photo:
        # Draw Vector "Human Avatar" (Head + Shoulders)
        c.setFillColor(DARK_GREY)
        c.circle(width/2, photo_y + photo_size/2, photo_size/2, stroke=0, fill=1) # Background
        
        c.setFillColor(colors.HexColor("#444444"))
        
        # Head
        head_radius = photo_size * 0.22
        c.circle(width/2, photo_y + photo_size * 0.6, head_radius, stroke=0, fill=1)
        
        # Shoulders (FIXED: Use c.ellipse instead of path.oval)
        shoulder_w = photo_size * 0.6
        shoulder_h = photo_size * 0.35
        
        # Calculate bounding box for ellipse (x1, y1, x2, y2)
        x_left = (width - shoulder_w) / 2
        y_bottom = photo_y + photo_size * 0.05
        x_right = x_left + shoulder_w
        y_top = y_bottom + shoulder_h
        
        # Draw the shoulders
        c.ellipse(x_left, y_bottom, x_right, y_top, stroke=0, fill=1)

    # 4. Member Name (Smaller, cleaner font)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10) # Reduced from 12/14 for elegance
    c.drawCentredString(width/2, height - 48*mm, member.name.upper())
    
    # 5. Plan Badge
    badge_w = 26*mm
    c.setFillColor(DARK_GREY)
    c.roundRect((width - badge_w)/2, height - 54*mm, badge_w, 4*mm, 2, fill=1, stroke=0)
    
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(width/2, height - 53*mm, f"{plan.name.upper()}")
    
    # 6. QR Code (Positioned lower)
    qr = qrcode.QRCode(box_size=10, border=0)
    code = member.member_code or str(member.id)
    qr.add_data(code)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    qr_size = 20*mm
    qr_y = 15*mm 
    # White box for QR to sit on
    c.setFillColor(WHITE)
    c.rect((width-qr_size)/2 - 1*mm, qr_y - 1*mm, qr_size + 2*mm, qr_size + 2*mm, fill=1, stroke=0)
    
    c.drawImage(ImageReader(qr_buffer), (width-qr_size)/2, qr_y, width=qr_size, height=qr_size)
    
    # 7. Member ID (Under the QR Code)
    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 7)
    display_id = member.member_code or str(member.id)
    c.drawCentredString(width/2, qr_y - 5*mm, f"ID: #{display_id}")

    c.save()
    buffer.seek(0)
    return buffer
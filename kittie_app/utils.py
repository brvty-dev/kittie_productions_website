import os
import io
import math
import time
from . import db, DB_NAME, mail
from flask_mail import Message
from flask import current_app, render_template, session, abort
import secrets
import subprocess
from werkzeug.utils import secure_filename
from datetime import datetime, timezone

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']


def create_database(app):
    if not os.path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')


def generate_secure_token():
    return secrets.token_urlsafe(32)


def utc_now():
    return datetime.now(timezone.utc)


ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'pdf'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_obj, upload_folder, base_name, suffix):
    if not file_obj or not file_obj.filename:
        return None

    if not allowed_file(file_obj.filename):
        raise ValueError(f"Invalid file type for {suffix.replace('_', ' ')}.")

    _, file_extension = os.path.splitext(file_obj.filename)
    filename = f"{secure_filename(base_name)}_{suffix}{file_extension.lower()}"
    filename = filename.lower().replace(' ', '_')

    file_obj.save(os.path.join(upload_folder, filename))
    return filename


def get_temp_watermarks_dir():
    temp_dir = os.path.join(current_app.instance_path, "temp_watermarks")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def cleanup_temp_watermarks_if_due(
    cleanup_interval_seconds=86400,
    file_max_age_seconds=172800
):
    temp_dir = get_temp_watermarks_dir()
    marker_path = os.path.join(current_app.instance_path, ".last_temp_watermark_cleanup")

    now = time.time()

    last_cleanup = 0
    if os.path.exists(marker_path):
        try:
            with open(marker_path, "r") as f:
                last_cleanup = float(f.read().strip() or 0)
        except (ValueError, OSError):
            last_cleanup = 0

    if now - last_cleanup < cleanup_interval_seconds:
        return

    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)

        if not os.path.isfile(file_path):
            continue

        try:
            file_age = now - os.path.getmtime(file_path)
            if file_age > file_max_age_seconds:
                os.remove(file_path)
        except OSError as e:
            current_app.logger.warning(
                f"Could not remove temp watermark file {file_path}: {e}"
            )

    try:
        with open(marker_path, "w") as f:
            f.write(str(now))
    except OSError as e:
        current_app.logger.warning(
            f"Could not update temp watermark cleanup marker: {e}"
        )


def current_compact_line(watermark_lines):
    return " | ".join(watermark_lines)


def draw_primary_watermark(
    c,
    lines,
    page_width,
    page_height,
    position,
    font_name,
    font_size,
    line_spacing,
    margin_x,
    margin_y,
    color,
    alpha,
    rotation=45
):
    c.saveState()
    c.setFillColor(Color(color[0], color[1], color[2], alpha=alpha))

    def set_line_font(index):
        if index == 0:
            c.setFont("Helvetica-Bold", font_size)
        else:
            c.setFont(font_name, font_size)

    if position == "top_left":
        for i, line in enumerate(lines):
            set_line_font(i)
            c.drawString(
                margin_x,
                page_height - margin_y - (i * line_spacing),
                line
            )

    elif position == "bottom_left":
        total_height = (len(lines) - 1) * line_spacing
        start_y = margin_y + total_height

        for i, line in enumerate(lines):
            set_line_font(i)
            c.drawString(
                margin_x,
                start_y - (i * line_spacing),
                line
            )

    elif position == "top_right":
        total_height = (len(lines) - 1) * line_spacing
        start_y = margin_y + total_height

        for i, line in enumerate(lines):
            set_line_font(i)
            current_font = "Helvetica-Bold" if i == 0 else font_name
            text_width = c.stringWidth(line, current_font, font_size)
            c.drawString(
                page_width - margin_x - text_width,
                page_height - margin_y - (i * line_spacing),
                line
            )

    elif position == "bottom_right":
        total_height = (len(lines) - 1) * line_spacing
        start_y = margin_y + total_height

        for i, line in enumerate(lines):
            set_line_font(i)
            current_font = "Helvetica-Bold" if i == 0 else font_name
            text_width = c.stringWidth(line, current_font, font_size)
            c.drawString(
                page_width - margin_x - text_width,
                start_y - (i * line_spacing),
                line
            )

    elif position == "center_diagonal":
        c.translate(page_width / 2, page_height / 2)
        c.rotate(rotation)

        total_height = (len(lines) - 1) * line_spacing
        start_y = total_height / 2

        for i, line in enumerate(lines):
            set_line_font(i)
            c.drawCentredString(0, start_y - (i * line_spacing), line)

    c.restoreState()


def draw_repeated_diagonal_watermark(
    c,
    page_width,
    page_height,
    text,
    font_name="Helvetica",
    font_size=11,
    color=(1, 1, 1),
    alpha=0.05,
    rotation=35,
    x_step=None,
    y_step=None
):

    c.saveState()

    c.setFont(font_name, font_size)
    c.setFillColor(Color(color[0], color[1], color[2], alpha=alpha))

    text_width = c.stringWidth(text, font_name, font_size)

    if x_step is None:
        x_step = text_width + 120

    if y_step is None:
        y_step = max(140, font_size * 10)

    c.translate(page_width / 2, page_height / 2)
    c.rotate(rotation)

    span = int(math.hypot(page_width, page_height))

    x_start = -span
    x_end = span
    y_start = -span
    y_end = span

    y = y_start
    row = 0

    while y <= y_end:
        x = x_start + ((row % 2) * (x_step / 2))

        while x <= x_end:
            c.drawString(x, y, text)
            x += x_step

        y += y_step
        row += 1

    c.restoreState()


def create_watermarked_pdf(input_pdf_path, output_pdf_path, watermark_lines, config=None):
    config = config or {}

    position = config.get("position", "top_left")
    font_name = config.get("font_name", "Helvetica")
    font_size = config.get("font_size", 11)
    line_spacing = config.get("line_spacing", 16)
    margin_x = config.get("margin_x", 36)
    margin_y = config.get("margin_y", 36)
    primary_color = config.get("color", (0.8, 0.8, 0.8))
    primary_alpha = config.get("alpha", 1)
    diagonal_color = config.get("diagonal_color", primary_color)
    diagonal_alpha = config.get("diagonal_alpha", min(primary_alpha, 0.1))
    rotation = config.get("rotation", 45)
    repeat_diagonal = config.get("repeat_diagonal", False)

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        overlay_stream = io.BytesIO()
        c = canvas.Canvas(overlay_stream, pagesize=(page_width, page_height))

        draw_primary_watermark(
            c=c,
            lines=watermark_lines,
            page_width=page_width,
            page_height=page_height,
            position=position,
            font_name=font_name,
            font_size=font_size,
            line_spacing=line_spacing,
            margin_x=margin_x,
            margin_y=margin_y,
            color=primary_color,
            alpha=primary_alpha,
            rotation=rotation
        )

        if repeat_diagonal:
            draw_repeated_diagonal_watermark(
                c=c,
                page_width=page_width,
                page_height=page_height,
                text=current_compact_line(watermark_lines),
                font_name="Helvetica",
                font_size=max(11, font_size + 4),
                color=diagonal_color,
                alpha=diagonal_alpha,
                rotation=35
            )

        c.save()
        overlay_stream.seek(0)

        overlay_pdf = PdfReader(overlay_stream)
        overlay_page = overlay_pdf.pages[0]

        page.merge_page(overlay_page)
        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)


def build_watermark_data(file_type, version, user_email, timestamp):
    if file_type == "script":
        watermark_lines = [
            "CONFIDENTIAL",
            f"Script (Draft {version})",
            f"Issued to: {user_email}",
            timestamp,
            "© Kittie Productions Limited"
        ]
        watermark_config = {
            "position": "bottom_right",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 20,
            "margin_y": 15,
            "color": (0.15, 0.15, 0.15),
            "alpha": 0.45,
            "repeat_diagonal": True
        }

    elif file_type == "treatment":
        watermark_lines = [
            "CONFIDENTIAL",
            f"Treatment (Draft {version})",
            f"Issued to: {user_email}",
            timestamp
        ]
        watermark_config = {
            "position": "top_left",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 20,
            "margin_y": 20,
            "color": (0.15, 0.15, 0.15),
            "alpha": 0.45,
            "repeat_diagonal": True
        }

    elif file_type == "budget":
        watermark_lines = [
            "INTERNAL USE ONLY",
            f"Accessed by: {user_email}",
            timestamp,
            "© Kittie Productions Limited"
        ]
        watermark_config = {
            "position": "bottom_right",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 36,
            "margin_y": 15,
            "color": (0, 0, 0),
            "alpha": 1.0,
            "repeat_diagonal": True
        }

    elif file_type == "one_sheet":
        watermark_lines = [
            "CONFIDENTIAL DEVELOPMENT MATERIAL",
            f"Issued to: {user_email}",
            timestamp
        ]
        watermark_config = {
            "position": "bottom_left",
            "font_name": "Helvetica",
            "font_size": 9,
            "line_spacing": 12,
            "margin_x": 49,
            "margin_y": 6,
            "color": (0, 0, 0),
            "alpha": 1.0,
            "repeat_diagonal": True
        }

    elif file_type == "two_sheet":
        watermark_lines = [
            "CONFIDENTIAL DEVELOPMENT MATERIAL",
            f"Issued to: {user_email}",
            timestamp
        ]
        watermark_config = {
            "align": "left",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 670,
            "margin_y": 797,
            "color": (0, 0, 0),
            "alpha": 1.0,
            "repeat_diagonal": True
        }

    elif file_type == "pitch_deck":
        watermark_lines = [
            "CONFIDENTIAL DEVELOPMENT MATERIAL",
            f"Issued to: {user_email}",
            timestamp
        ]
        watermark_config = {
            "position": "top_right",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 15,
            "margin_y": 20,
            "color": (0.15, 0.15, 0.15),
            "alpha": 0.45,
            "repeat_diagonal": True
        }

    else:
        watermark_lines = [
            f"Issued to: {user_email}",
            timestamp,
            "© Kittie Productions Limited"
        ]
        watermark_config = {
            "position": "bottom_right",
            "font_name": "Helvetica",
            "font_size": 11,
            "line_spacing": 16,
            "margin_x": 36,
            "margin_y": 36,
            "color": (0.15, 0.15, 0.15),
            "alpha": 0.45,
            "repeat_diagonal": False
        }

    return watermark_lines, watermark_config

'''
def send_welcome_email(email, token, first_name):
    reset_url = f"https://www.kittieproductions.co.uk/update_password/{token}"
    msg = Message(
        subject="Welcome to Kittie Productions",
        recipients=[email],
        body=f"""
        
        Hi {first_name},
        
        Thank you for your interest in Kittie Productions.
        
        Please click the following link to set a password and view our upcoming productions:
        
        {reset_url}
        
        Once logged in, you will be directed to Kittie's latest projects.

        Kind regards,

        Kittie Productions
        www.kittieproductions.co.uk
        Content creation for Film and TV
                
        """
    )
    mail.send(msg)
'''

def send_welcome_email(email, token, first_name):
    reset_url = f"https://www.kittieproductions.co.uk/update_password/{token}"
    msg = Message(
        subject="Kittie Productions' systems upgrade",
        recipients=[email],
        body=f"""
        
        Dear {first_name},
        
        Thank you for your continuing interest in Kittie Productions.

        We have recently upgraded our servers to provide more secure data management. This is in-line with 
        industry practices, and will support our aim of moving to a paperless workflow during production.
        
        During the upgrade, your data stored with us (full name and email) remained secure. However, to bring your 
        account inline with the changes, you are required to reset your password using the link below:
        
        {reset_url}
        
        Once logged in, you will be able to view the development files of Kittie's latest projects, 
        which are now watermarked for additional peace of mind.


        Kind regards,



        Richard (He/him)

        Kittie Productions
        www.kittieproductions.co.uk
        Content creation for Film and TV
                
        """
    )
    mail.send(msg)

def send_reset_email(email, token):
    reset_url = f"https://www.kittieproductions.co.uk/update_password/{token}"
    msg = Message(
        subject="Kittie Productions Password Reset",
        recipients=[email],
        body=f"""
        
        Hi there,

        Click the following link to reset your Kittie Productions password:

        {reset_url}

        You are receiving this message because a request was made using this email address.
        If you did not make the request, please ignore this message. No personal data has been compromised.

        Kind regards,

        Kittie Productions
        www.kittieproductions.co.uk
        Content creation for Film and TV
                
        """
    )
    mail.send(msg)
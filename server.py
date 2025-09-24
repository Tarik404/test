#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import urllib.parse
import requests
import re
import time
from datetime import datetime
from collections import defaultdict

# Change to the directory containing the HTML files
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 5000
HOST = "0.0.0.0"

# Rate limiting - track requests per IP
rate_limit_tracker = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 minutes
RATE_LIMIT_MAX_REQUESTS = 3  # Max 3 requests per 5 minutes per IP

# Email notification functionality using Replit Mail integration
def get_auth_token():
    """Get authentication token for Replit services"""
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        return f"repl {repl_identity}"
    elif web_repl_renewal:
        return f"depl {web_repl_renewal}"
    else:
        raise Exception("No authentication token found. Ensure you're running in Replit environment.")

def send_loan_notification(book_title, book_author, borrower_name, borrower_email):
    """Send loan notification email using Replit Mail service"""
    # Get admin email from environment variable - never trust client input for recipient
    admin_email = os.environ.get('ADMIN_EMAIL')
    if not admin_email:
        print("⚠️  No ADMIN_EMAIL configured in environment")
        return {"success": False, "error": "Admin email not configured"}
    
    try:
        auth_token = get_auth_token()
        
        # Compose email content
        subject = f"📚 Nuevo Préstamo - {book_title}"
        text_content = f"""
¡Hola!

Se ha registrado un nuevo préstamo en la biblioteca digital gehitubib:

📖 Libro: {book_title}
✍️ Autor: {book_author}
👤 Usuario: {borrower_name}
📧 Email: {borrower_email}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Puedes gestionar este préstamo desde el panel de administración.

Saludos,
Sistema de Biblioteca gehitubib
        """.strip()
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #9b59b6;">📚 Nuevo Préstamo - gehitubib</h2>
            
            <div style="background: #f8f9fa; border-left: 4px solid #9b59b6; padding: 20px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #333;">Detalles del Préstamo</h3>
                <p><strong>📖 Libro:</strong> {book_title}</p>
                <p><strong>✍️ Autor:</strong> {book_author}</p>
                <p><strong>👤 Usuario:</strong> {borrower_name}</p>
                <p><strong>📧 Email:</strong> {borrower_email}</p>
                <p><strong>📅 Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <p>Puedes gestionar este préstamo desde el panel de administración de la biblioteca.</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #666; font-size: 14px;">
                Sistema de Biblioteca Digital gehitubib
            </p>
        </div>
        """
        
        payload = {
            "to": admin_email,
            "subject": subject,
            "text": text_content,
            "html": html_content
        }
        
        response = requests.post(
            "https://connectors.replit.com/api/v2/mailer/send",
            headers={
                "Content-Type": "application/json",
                "X-Replit-Token": auth_token,
            },
            json=payload
        )
        
        if response.status_code == 200:
            print(f"✅ Email notification sent successfully to {admin_email}")
            return {"success": True, "message": "Notification sent successfully"}
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', f'Email service error: {response.status_code}')
            except:
                error_msg = f'Email service error: {response.status_code} - {response.text}'
            print(f"❌ Failed to send email notification: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        print(f"❌ Exception in send_loan_notification: {str(e)}")
        return {"success": False, "error": str(e)}

def validate_loan_request(data):
    """Validate and sanitize loan notification request"""
    required_fields = ['book_title', 'book_author', 'borrower_name', 'borrower_email']
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Length limits
    if len(data['book_title']) > 255:
        return False, "Book title too long (max 255 characters)"
    if len(data['book_author']) > 100:
        return False, "Book author too long (max 100 characters)"
    if len(data['borrower_name']) > 100:
        return False, "Borrower name too long (max 100 characters)"
    
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['borrower_email']):
        return False, "Invalid borrower email format"
    
    # Sanitize text fields (basic HTML/special character removal)
    for field in ['book_title', 'book_author', 'borrower_name']:
        data[field] = re.sub(r'[<>"\']', '', data[field]).strip()
    
    return True, "Valid"

def check_rate_limit(client_ip):
    """Check if client IP is within rate limits"""
    current_time = time.time()
    
    # Clean old entries
    rate_limit_tracker[client_ip] = [
        timestamp for timestamp in rate_limit_tracker[client_ip]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check if within limits
    if len(rate_limit_tracker[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    rate_limit_tracker[client_ip].append(current_time)
    return True

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add cache control headers to prevent caching issues in iframe
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Allow CORS for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for API endpoints"""
        if self.path == '/api/loan-notification':
            # Handle loan notification with security measures
            try:
                # Rate limiting check
                client_ip = self.client_address[0]
                if not check_rate_limit(client_ip):
                    self.send_response(429)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {"success": False, "error": "Rate limit exceeded. Please try again later."}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Content length check
                content_length = int(self.headers['Content-Length'])
                if content_length > 10000:  # 10KB limit
                    self.send_response(413)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {"success": False, "error": "Request too large"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Parse and validate JSON
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate and sanitize input
                is_valid, error_msg = validate_loan_request(data)
                if not is_valid:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {"success": False, "error": error_msg}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Log the notification request (sanitized)
                print(f"📧 Processing loan notification for book: {data['book_title'][:50]}... from IP: {client_ip}")
                
                # Send notification
                result = send_loan_notification(
                    data['book_title'], 
                    data['book_author'],
                    data['borrower_name'],
                    data['borrower_email']
                )
                
                self.send_response(200 if result['success'] else 500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"success": False, "error": "Invalid JSON"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            # For non-API POST requests, return 404
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer((HOST, PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving at http://{HOST}:{PORT}")
    print("API endpoint available at /api/loan-notification")
    httpd.serve_forever()
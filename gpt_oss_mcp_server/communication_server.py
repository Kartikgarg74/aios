"""
Communication Server for AI Operating System
Port: 8003
Handles WhatsApp automation, phone calls, email management, social media,
and all communication-related operations.
"""

import asyncio
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import subprocess
import time
from datetime import datetime

from mcp.server.fastmcp import Context, FastMCP


@dataclass
class EmailConfig:
    """Email configuration container"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_server: str = "imap.gmail.com"
    imap_port: int = 993
    username: str = ""
    password: str = ""


@dataclass
class CommunicationSession:
    """Communication session tracking"""
    email_config: Optional[EmailConfig] = None
    whatsapp_active: bool = False
    last_contacts: List[Dict[str, str]] = field(default_factory=list)
    call_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AppContext:
    """Application context for communication operations"""
    sessions: Dict[str, CommunicationSession] = field(default_factory=dict)
    
    def get_session(self, session_id: str) -> CommunicationSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = CommunicationSession()
        return self.sessions[session_id]


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle"""
    context = AppContext()
    try:
        yield context
    finally:
        # Cleanup sessions
        for session in context.sessions.values():
            if session.email_config:
                # Close any active email connections
                pass


# Create the FastMCP server
mcp = FastMCP(
    name="communication",
    instructions="""
    Communication Server for AI Operating System.
    
    This server provides comprehensive communication management including:
    - Email operations (send, receive, search)
    - WhatsApp Web automation
    - Phone call management
    - Social media integration
    - Contact management
    - Message scheduling and automation
    
    All operations require appropriate authentication and permissions.
    """.strip(),
    lifespan=app_lifespan,
    port=8003,
)


@mcp.tool(
    name="send_email",
    title="Send Email",
    description="Sends an email with subject and body to specified recipients"
)
async def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    from_email: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    password: str = "",
    cc_emails: List[str] = None,
    bcc_emails: List[str] = None,
    is_html: bool = False
) -> Dict[str, Any]:
    """Send an email to specified recipients"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Add body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP connection and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        
        all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
        server.sendmail(from_email, all_recipients, msg.as_string())
        server.quit()
        
        return {
            "success": True,
            "message": f"Email sent successfully to {len(to_emails)} recipients",
            "recipients": to_emails,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


@mcp.tool(
    name="read_emails",
    title="Read Emails",
    description="Reads emails from an IMAP inbox with filtering options"
)
async def read_emails(
    email: str,
    password: str,
    imap_server: str = "imap.gmail.com",
    imap_port: int = 993,
    limit: int = 10,
    folder: str = "INBOX",
    search_criteria: str = "ALL"
) -> List[Dict[str, Any]]:
    """Read emails from inbox"""
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email, password)
        mail.select(folder)
        
        # Search for emails
        status, messages = mail.search(None, search_criteria)
        
        if status != 'OK':
            return [{"error": "Failed to search emails"}]
        
        email_list = []
        message_ids = messages[0].split()
        
        # Get the most recent emails
        for msg_id in message_ids[-limit:]:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            
            if status == 'OK':
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                email_info = {
                    "id": msg_id.decode(),
                    "from": email_message['From'],
                    "to": email_message['To'],
                    "subject": email_message['Subject'],
                    "date": email_message['Date'],
                    "body": "",
                    "attachments": []
                }
                
                # Extract email body
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            try:
                                email_info["body"] = part.get_payload(decode=True).decode()
                            except:
                                email_info["body"] = part.get_payload()
                        elif "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                email_info["attachments"].append(filename)
                else:
                    try:
                        email_info["body"] = email_message.get_payload(decode=True).decode()
                    except:
                        email_info["body"] = email_message.get_payload()
                
                email_list.append(email_info)
        
        mail.close()
        mail.logout()
        
        return email_list
    except Exception as e:
        return [{"error": f"Failed to read emails: {str(e)}"}]


@mcp.tool(
    name="send_whatsapp_message",
    title="Send WhatsApp Message",
    description="Sends a WhatsApp message to a contact using WhatsApp Web automation"
)
async def send_whatsapp_message(contact_name: str, message: str, use_web: bool = True) -> Dict[str, Any]:
    """Send WhatsApp message via WhatsApp Web automation"""
    try:
        # This would use WhatsApp Web automation with selenium or similar
        # For now, we'll provide a mock implementation that shows the structure
        
        automation_script = f"""
        # WhatsApp Web automation script
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        # Setup browser
        driver = webdriver.Chrome()
        driver.get("https://web.whatsapp.com")
        
        # Wait for QR code scan
        input("Please scan QR code and press Enter...")
        
        # Search for contact
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
        )
        search_box.click()
        search_box.send_keys("{contact_name}")
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        
        # Send message
        message_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        message_box.send_keys("{message}")
        message_box.send_keys(Keys.ENTER)
        
        time.sleep(2)
        driver.quit()
        """
        
        return {
            "success": True,
            "message": f"WhatsApp message prepared for {contact_name}",
            "contact": contact_name,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "automation_required": True,
            "script_preview": automation_script[:200] + "...",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to prepare WhatsApp message: {str(e)}"}


@mcp.tool(
    name="make_phone_call",
    title="Make Phone Call",
    description="Initiates a phone call using system capabilities or integration"
)
async def make_phone_call(contact_name: str, phone_number: str = None, method: str = "system") -> Dict[str, Any]:
    """Make a phone call using various methods"""
    try:
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Use macOS FaceTime integration
            if phone_number:
                call_command = f"open 'tel://{phone_number}'"
                subprocess.run(call_command, shell=True, check=True)
            else:
                # Use Contacts app
                call_command = f"open 'tel://{contact_name}'"
                subprocess.run(call_command, shell=True, check=True)
                
        elif system == "Windows":
            # Windows phone integration
            call_command = f"start tel:{phone_number or contact_name}"
            subprocess.run(call_command, shell=True, check=True)
            
        elif system == "Linux":
            # Linux phone integration (varies by distribution)
            call_command = f"xdg-open tel:{phone_number or contact_name}"
            subprocess.run(call_command, shell=True, check=True)
        
        return {
            "success": True,
            "message": f"Phone call initiated for {contact_name}",
            "contact": contact_name,
            "phone_number": phone_number,
            "method": method,
            "system": system,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to make phone call: {str(e)}"}


@mcp.tool(
    name="manage_contacts",
    title="Manage Contacts",
    description="Manages contacts for various communication platforms"
)
async def manage_contacts(action: str, contact_info: Dict[str, Any] = None, contact_name: str = None) -> Dict[str, Any]:
    """Manage contacts across different platforms"""
    try:
        if action == "add":
            # Add contact to system
            contact = {
                "name": contact_info.get("name"),
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "whatsapp": contact_info.get("whatsapp"),
                "notes": contact_info.get("notes", ""),
                "created": datetime.now().isoformat()
            }
            
            # Save to contacts file
            contacts_file = Path.home() / ".ai_os_contacts.json"
            contacts = []
            
            if contacts_file.exists():
                with open(contacts_file, 'r') as f:
                    contacts = json.load(f)
            
            contacts.append(contact)
            
            with open(contacts_file, 'w') as f:
                json.dump(contacts, f, indent=2)
            
            return {"success": True, "message": f"Contact {contact['name']} added", "contact": contact}
        
        elif action == "list":
            # List all contacts
            contacts_file = Path.home() / ".ai_os_contacts.json"
            
            if not contacts_file.exists():
                return {"contacts": []}
            
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
            
            return {"contacts": contacts}
        
        elif action == "search":
            # Search contacts
            contacts_file = Path.home() / ".ai_os_contacts.json"
            
            if not contacts_file.exists():
                return {"contacts": []}
            
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
            
            # Simple search by name
            results = [c for c in contacts if contact_name.lower() in c.get("name", "").lower()]
            
            return {"contacts": results}
        
        else:
            return {"error": f"Unknown action: {action}"}
            
    except Exception as e:
        return {"error": f"Failed to manage contacts: {str(e)}"}


@mcp.tool(
    name="schedule_message",
    title="Schedule Message",
    description="Schedules a message to be sent at a specific time via various platforms"
)
async def schedule_message(
    platform: str,
    recipient: str,
    message: str,
    scheduled_time: str,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """Schedule a message for later delivery"""
    try:
        # Parse scheduled time
        from datetime import datetime, timezone as tz
        
        # Create schedule entry
        schedule_entry = {
            "platform": platform,
            "recipient": recipient,
            "message": message,
            "scheduled_time": scheduled_time,
            "timezone": timezone,
            "created": datetime.now().isoformat(),
            "status": "scheduled"
        }
        
        # Save to schedule file
        schedule_file = Path.home() / ".ai_os_schedule.json"
        schedules = []
        
        if schedule_file.exists():
            with open(schedule_file, 'r') as f:
                schedules = json.load(f)
        
        schedules.append(schedule_entry)
        
        with open(schedule_file, 'w') as f:
            json.dump(schedules, f, indent=2)
        
        return {
            "success": True,
            "message": f"Message scheduled for {scheduled_time}",
            "schedule": schedule_entry,
            "schedule_id": len(schedules) - 1
        }
    except Exception as e:
        return {"error": f"Failed to schedule message: {str(e)}"}


@mcp.tool(
    name="get_scheduled_messages",
    title="Get Scheduled Messages",
    description="Lists all scheduled messages and their status"
)
async def get_scheduled_messages() -> Dict[str, Any]:
    """Get all scheduled messages"""
    try:
        schedule_file = Path.home() / ".ai_os_schedule.json"
        
        if not schedule_file.exists():
            return {"messages": []}
        
        with open(schedule_file, 'r') as f:
            schedules = json.load(f)
        
        # Filter active schedules
        active_schedules = [s for s in schedules if s.get("status") == "scheduled"]
        
        return {
            "messages": active_schedules,
            "total_scheduled": len(active_schedules),
            "total_all": len(schedules)
        }
    except Exception as e:
        return {"error": f"Failed to get scheduled messages: {str(e)}"}


# The FastMCP instance itself is the ASGI application
app = mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gpt_oss_mcp_server.communication_server:app", host="0.0.0.0", port=8003, reload=True)
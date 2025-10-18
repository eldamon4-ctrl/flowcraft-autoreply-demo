import imaplib
import smtplib
import email
from email.mime.text import MIMEText
import openai
from flask import Flask, request, render_template

app = Flask(__name__)

# ---------- CONFIG ----------
IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
EMAIL_ACCOUNT = 'damonflowcraftco@gmail.com'
EMAIL_PASSWORD = 'DamonMoreau4!'
OPENAI_API_KEY = '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'

openai.api_key = OPENAI_API_KEY
review_queue = []

# ---------- FUNCTIONS ----------
def fetch_unread_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select('inbox')
    status, response = mail.search(None, '(UNSEEN)')
    unread_msg_nums = response[0].split()
    emails = []
    for e_id in unread_msg_nums:
        _, data = mail.fetch(e_id, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        emails.append({
            'from': msg['From'],
            'subject': msg['Subject'],
            'body': msg.get_payload(decode=True).decode()
        })
    return emails

def generate_reply(email_body):
    prompt = f"""
You are FlowCraftCo's AI Email Assistant. Write a professional, polite, and concise email reply.
Email to reply to:
{email_body}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = f"Re: {subject}"
    msg['From'] = EMAIL_ACCOUNT
    msg['To'] = to_email

    server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
    server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ACCOUNT, to_email, msg.as_string())
    server.quit()

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html', queue=review_queue)

@app.route('/fetch_emails')
def fetch_emails():
    emails = fetch_unread_emails()
    for e in emails:
        draft = generate_reply(e['body'])
        review_queue.append({
            'from': e['from'],
            'subject': e['subject'],
            'draft': draft
        })
    return "Fetched emails and generated drafts!"

@app.route('/send/<int:index>')
def send_email_route(index):
    draft = review_queue.pop(index)
    send_email(draft['from'], draft['subject'], draft['draft'])
    return f"Email sent to {draft['from']}!"

"""Send emails or create drafts of emails.

Functions
---------
create_email_message
    Creates an email message object.
draft
    Creates a draft email using an email message object.
send
    Sends an email using an email message object.
load_html
    Loads an html file and returns its contents.
localhost_send
    Sends an email using an email object to localhost for testing.
"""
# TODO: embedding images does not work for drafts. Maybe use the Gmail 
# API to handle Gmail drafts.


import os
import re
import time
import ssl
import smtplib
import imaplib
import imghdr
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Optional
from dotenv import load_dotenv
from textwrap import dedent


def __sample_use() -> None:
    load_dotenv()
    email_address = os.environ.get('EMAIL_ADDRESS')
    email_password = os.environ.get('EMAIL_PASSWORD')

    subject = 'This is a sample email'
    attachment_paths = []

    to_addresses = [os.environ.get('RECIPIENT_ADDRESS')]
    cc_addresses = []
    bcc_addresses = []

    plaintext_content = dedent(f'''\
        Hello,
        
        This is the plaintext content of the email.
        ''')
    html_content = dedent(f'''\
        <h1>Greetings!</h1>

        <p>This is an email written with HTML.</p>
        ''')

    msg = create_email_message(from_address=email_address,
                               subject=subject,
                               plaintext_content=plaintext_content,
                               html_content=html_content,
                               attachment_paths=attachment_paths,
                               to_addresses=to_addresses,
                               cc_addresses=cc_addresses,
                               bcc_addresses=bcc_addresses)

    # send(msg=msg,
    draft(msg=msg,
          from_address=email_address,
          email_app_password=email_password)


def __create_image_ids(num: int) -> list[str]:
    """Makes a list of image IDs.

    Parameters
    ----------
    num : int
        The number of image IDs to make.
    """
    return [make_msgid() for _ in range(num)]


def create_email_message(from_address: str,
                         subject: str,
                         plaintext_content: str,
                         html_content: Optional[str] = None,
                         attachment_paths: Optional[list[str]] = None,
                         to_addresses: Optional[list[str]] = None,
                         cc_addresses: Optional[list[str]] = None,
                         bcc_addresses: Optional[list[str]] = None
                         ) -> EmailMessage:
    """Initializes an email message object.
    
    Parameters
    ----------
    from_address : str
        Your email address.
    subject : str
        The subject of the email.
    plaintext_content : str
        The body of the email. Required even if an html_content is given 
        because some email clients do not display html emails.
    html_content : Optional[str]
        The HTML body of the email. Replaces plaintext_content if given 
        and if the recipient's email client supports HTML emails.
    attachment_paths : Optional[list[str]]
        The paths to the files to be attached to the email.
    to_addresses : Optional[list[str]]
        The email addresses of the recipients.
    cc_addresses : Optional[list[str]]
        The email addresses of the CC recipients.
    bcc_addresses : Optional[list[str]]
        The email addresses of the BCC recipients.
    """
    msg = EmailMessage()
    if not subject:
        raise ValueError('subject must be given')
    msg['Subject'] = subject
    msg['From'] = from_address
    if not to_addresses and not cc_addresses and not bcc_addresses:
        raise ValueError('At least one recipient must be given.')
    if to_addresses is not None:
        msg['To'] = ', '.join(to_addresses)
    if cc_addresses is not None:
        msg['Cc'] = ', '.join(cc_addresses)
    if bcc_addresses is not None:
        msg['Bcc'] = ', '.join(bcc_addresses)

    if not plaintext_content:
        raise ValueError('plaintext_content must be given')
    msg.set_content(plaintext_content)
    if html_content is not None:
        html_content, embedded_image_paths, image_ids = \
            __convert_image_links(html_content)
        msg.add_alternative(html_content, subtype='html', charset='utf8')

        for i, path in enumerate(embedded_image_paths):
            with open(path, 'rb') as f:
                msg.add_attachment(f.read(),
                                   maintype='image',
                                   subtype=path.split('.')[-1],
                                   filename=path.split('/')[-1],
                                   cid=image_ids[i])

    if isinstance(attachment_paths, str):
        attachment_paths = [attachment_paths]
    if not attachment_paths and 'attach' in plaintext_content.lower():
        raise ValueError('Attachment required because "attach" in email.')
    image_types = ['jpg', 'jpeg', 'png', 'gif']
    tested_file_types = ['jpg', 'jpeg', 'docx', 'pdf']
    for path in attachment_paths:
        with open(path, 'rb') as f:
            file_data = f.read()
            file_name = f.name
            file_ext = file_name.split('.')[-1]
            if file_ext not in tested_file_types:
                raise ValueError(f'File type {file_ext} not tested.')
            if file_ext in image_types:
                maintype = 'image'
                subtype = imghdr.what(f.name)
            elif file_ext == 'xlsx':
                maintype = 'application/xlsx'
                subtype = 'xlsx'
            elif file_ext == 'csv':
                maintype = 'csv'
                subtype = 'None'
            else:
                # This should work for pdfs and maybe other file types.
                maintype = 'application'
                subtype = 'octet-stream'
        msg.add_attachment(file_data,
                           maintype=maintype,
                           subtype=subtype,
                           filename=file_name)
    return msg


def __convert_image_links(html_content: str) \
        -> tuple[str, list[str], list[str]]:
    """Converts image links to cid links.
    
    Parameters
    ----------
    html_content : str
        The HTML content of the email.

    Returns
    -------
    html_content : str
        The HTML content of the email with image links converted to cid 
        links.
    embedded_image_paths : list[str]
        The paths to the embedded images.
    image_ids : list[str]
        The image IDs.
    """
    image_link_pattern = \
        re.compile(r'(?<=<img src=[\'\"])(?!cid:)(.+?)(?=[\'\"] ?/?>)')
    embedded_image_paths = image_link_pattern.findall(html_content)
    image_ids: list[str] = __create_image_ids(len(embedded_image_paths))
    for image_id in image_ids:
        html_content = image_link_pattern.sub(f'cid:{image_id[1:-1]}',
                                              html_content,
                                              count=1)
    return html_content, embedded_image_paths, image_ids


def draft(msg: EmailMessage,
          from_address: str,
          email_app_password: str,
          email_server: str = 'imap.gmail.com',
          email_port: int = 993,
          mailbox_name: str = '[Gmail]/Drafts') -> None:
    """Creates a draft email.

    Parameters
    ----------
    msg : EmailMessage
        The email message to create a draft of.
    from_address : str
        Your email address.
    email_app_password : str
        The app password to access your email account. For gmail, this 
        is different from your google password. To create a gmail app 
        password, go to https://myaccount.google.com/apppasswords. 
        Multi-factor authentication must be enabled to visit this site.
    email_server : str
        The email server to connect to. Gmail: 'imap.gmail.com', 
        Outlook.com/Hotmail.com: 'imap-mail.outlook.com', Yahoo Mail: 
	    'imap.mail.yahoo.com', AT&T: 'imap.mail.att.net', Comcast: 
	    'imap.comcast.net', Verizon: 'incoming.verizon.net'.
    email_port : int
        The port to connect to. This function attempts to make an SSL 
        connection.
    mailbox_name : str
        The name of the mailbox to create the draft in.
    """
    ctx = ssl.create_default_context()
    with imaplib.IMAP4_SSL(email_server, email_port, ssl_context=ctx) as imap:
        imap.login(from_address, email_app_password)
        status, mailboxes = imap.list()
        if status != 'OK':
            raise RuntimeError(f'Could not list mailboxes: {mailboxes}')
        folder_list = [str(folder).split('"')[-2] for folder in mailboxes]
        if mailbox_name not in folder_list:
            raise ValueError(f'The mailbox {mailbox_name} does not exist. '
                             f'Select one of the following: {folder_list}')
        status, _ = imap.select(mailbox=mailbox_name, readonly=False)
        if status != 'OK':
            raise RuntimeError(f'Could not select mailbox {mailbox_name}')
        imap.append(mailbox=mailbox_name,
                    flags='',
                    date_time=imaplib.Time2Internaldate(time.time()),
                    message=str(msg).encode('utf8'))
    print('Draft created.')


def send(msg: EmailMessage,
         from_address: str,
         email_app_password: str,
         email_server: str = 'smtp.gmail.com',
         email_port: int = 465) -> None:
    """Immediately sends an email to the given recipient addresses.
    
    Parameters
    ----------
    msg : EmailMessage
        The email message to send.
    from_address : str
        Your email address.
    email_app_password : str
        The app password to access your email account. For gmail, this 
        is different from your google password. To create a gmail app 
        password, go to https://myaccount.google.com/apppasswords. 
        Multi-factor authentication must be enabled to visit this site.
    email_server : str
        The email server to connect to. Gmail: 'smtp.gmail.com', 
        Outlook.com/Hotmail.com: 'smtp-mail.outlook.com', Yahoo Mail: 
        'smtp.mail.yahoo.com', AT&T: 'smtp.mail.att.net', Comcast: 
        'smtp.comcast.net', Verizon: 'smtp.verizon.net'.
    email_port : int
        The port to connect to. This function attempts to make an SSL 
        connection.
    """
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(email_server, email_port, context=ctx) as smtp:
        smtp.login(from_address, email_app_password)
        smtp.send_message(msg)
    __print_recipient_addresses(msg)


def __print_recipient_addresses(msg: EmailMessage) -> None:
    """Prints all recipient addresses."""
    print('Email sent')
    if msg['To']:
        print(f'\tto: {msg["To"]}')
    if msg['Cc']:
        print(f'\tCC: {msg["Cc"]}')
    if msg['Bcc']:
        print(f'\tBCC: {msg["Bcc"]}')


def load_html(file_path: str) -> str:
    """Loads an html file and returns its contents.

    Parameters
    ----------
    file_path : str
        The path to the html file.

    Returns
    -------
    str
        The contents of the html file.
    """
    with open(file_path, 'r', encoding='utf8') as f:
        return f.read()


def localhost_send(msg: EmailMessage) -> None:
    """Immediately sends an email to a mail server on localhost.
    
    The mail server can be started with the following command:
    $ python3 -m smtpd -c DebuggingServer -n localhost:1025
    
    Parameters
    ----------
    msg : EmailMessage
        The email message to send.
    """
    with smtplib.SMTP('localhost', 1025) as smtp:
        smtp.send_message(msg)
    print('Email sent to localhost.')

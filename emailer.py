"""Send and create drafts of emails.

Functions
---------
create_email_message
    Creates an email message object.
draft
    Creates a draft email.
send
    Sends an email.
load_html
    Loads an html file and returns its contents.
localhost_send
    Sends a sample email to localhost.
"""


import os
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


def sample_use() -> None:
    load_dotenv()
    email_address = os.environ.get('EMAIL_ADDRESS')
    email_password = os.environ.get('EMAIL_PASSWORD')
    to_addresses = [os.environ.get('RECIPIENT_ADDRESS')]
    cc_addresses = []
    bcc_addresses = []
    subject = 'This is a sample email'
    plaintext_content = 'This is the plaintext content of the email.'
    embedded_image_paths = ['sun 1024.jpg']
    image_ids: list[str] = create_image_ids(len(embedded_image_paths))
    html_content = dedent(f'''\
        <h1>This is an email written with HTML</h1>
        <p>There should be one image embedded below and one image attached.</p>
        <img src='cid:{image_ids[0][1:-1]}' />
        ''')
    attachment_paths = ['nebula 2 under 1 MB.jpg']

    msg = create_email_message(from_address=email_address,
                               subject=subject,
                               plaintext_content=plaintext_content,
                               html_content=html_content,
                               attachment_paths=attachment_paths,
                               embedded_image_paths=embedded_image_paths,
                               image_ids=image_ids,
                               to_addresses=to_addresses,
                               cc_addresses=cc_addresses,
                               bcc_addresses=bcc_addresses)

    draft(msg=msg,
          from_address=email_address,
          email_app_password=email_password)
    # send(msg=msg,
    #      from_address=email_address,
    #      email_app_password=email_password)


def create_image_ids(num: int) -> list[str]:
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
                         embedded_image_paths: Optional[list[str]] = None,
                         image_ids: Optional[list[str]] = None,
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
        and if the recipient(s) email client supports html emails.
    attachment_paths : Optional[list[str]]
        The paths to the files to be attached to the email.
    embedded_image_paths : Optional[list[str]]
        The paths to the images to be embedded in the email.
    image_ids : Optional[list[str]]
        The IDs of the images to be embedded in the email. Each embedded
        image must have a corresponding ID already specified in the 
        HTML, e.g. ``<img src='cid:{image_ids[0][1:-1]}' />``. Create 
        image IDs using the ``create_image_ids`` function.
    to_addresses : Optional[list[str]]
        The email addresses of the recipients.
    cc_addresses : Optional[list[str]]
        The email addresses of the CC recipients.
    bcc_addresses : Optional[list[str]]
        The email addresses of the BCC recipients.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_address
    if to_addresses is not None:
        msg['To'] = ', '.join(to_addresses)
    if cc_addresses is not None:
        msg['Cc'] = ', '.join(cc_addresses)
    if bcc_addresses is not None:
        msg['Bcc'] = ', '.join(bcc_addresses)
    msg.set_content(plaintext_content)
    msg.add_alternative(html_content, subtype='html', charset='utf8')

    if isinstance(embedded_image_paths, str):
        embedded_image_paths = [embedded_image_paths]
    if isinstance(image_ids, str):
        image_ids = [image_ids]
    if embedded_image_paths is not None and image_ids is not None:
        # TODO: embedding images still does not work for drafts.
        assert len(embedded_image_paths) == len(image_ids)
        for i, path in enumerate(embedded_image_paths):
            with open(path, 'rb') as f:
                msg.add_attachment(f.read(),
                                   maintype='image',
                                   subtype=path.split('.')[-1],
                                   filename=path.split('/')[-1],
                                   cid=image_ids[i])

    if isinstance(attachment_paths, str):
        attachment_paths = [attachment_paths]
    image_types = ['jpg', 'jpeg', 'png', 'gif']
    for path in attachment_paths:
        with open(path, 'rb') as f:
            file_data = f.read()
            file_name = f.name
            file_ext = file_name.split('.')[-1]
            if file_ext in image_types:
                maintype = 'image'
                subtype = imghdr.what(f.name)
            elif file_ext == 'xlsx':
                maintype = 'application/xlsx'
                subtype = 'xlsx'
            elif file_ext == 'csv':
                maintype = 'csv'
                subtype = 'None'
            else:  # This should work for pdfs and possibly other file types.
                maintype = 'application'
                subtype = 'octet-stream'
        msg.add_attachment(file_data,
                           maintype=maintype,
                           subtype=subtype,
                           filename=file_name)
    return msg


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


def localhost_send(from_address: str,
                   subject: str,
                   plaintext_content: str,
                   to_addresses: Optional[list[str]] = None,
                   cc_addresses: Optional[list[str]] = None,
                   bcc_addresses: Optional[list[str]] = None) -> None:
    """Immediately sends an email to a mail server on localhost.
    
    The mail server can be started with the following command:
    $ python3 -m smtpd -c DebuggingServer -n localhost:1025
    
    Parameters
    ----------
    from_address : str
        Your email address.
    subject : str
        The subject of the email.
    plaintext_content : str
        The body of the email.
    to_addresses : Optional[list[str]]
        The email addresses of the recipients, as if there could be any.
    cc_addresses : Optional[list[str]]
        The email addresses of the CC recipients, as if there could be 
        any.
    bcc_addresses : Optional[list[str]]
        The email addresses of the BCC recipients, as if there could be 
        any.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = ', '.join(to_addresses)
    msg['Cc'] = ', '.join(cc_addresses)
    msg['Bcc'] = ', '.join(bcc_addresses)
    msg.set_content(plaintext_content)

    with smtplib.SMTP('localhost', 1025) as smtp:
        smtp.send_message(msg)


if __name__ == '__main__':
    sample_use()

from __future__ import annotations
from .utils import log
from email.message import EmailMessage
import smtplib
import ssl


class Sender:
    def __init__(
        self,
        from_address: str,
        email_app_password: str,
        log_file_path: str = "sent.log",
        email_server: str = "smtp.gmail.com",
        email_port: int = 465,
    ) -> None:
        """Creates a context manager for sending emails.

        Parameters
        ----------
        from_address : str
            Your email address.
        email_app_password : str
            The app password to access your email account. For gmail, this is
            different from your google password. To create a gmail app
            password, go to https://myaccount.google.com/apppasswords.
            Multi-factor authentication must be enabled to visit this site.
        log_file_path : str
            The path to the log file for logging emails' subject, recipient(s),
            and send time. Set this to an empty string, None, or False to
            disable logging.
        email_server : str
            The email server to connect to.
            Gmail: "smtp.gmail.com"
            Outlook.com/Hotmail.com: "smtp-mail.outlook.com"
            Yahoo Mail: "smtp.mail.yahoo.com"
            AT&T: "smtp.mail.att.net"
            Comcast: "smtp.comcast.net"
            Verizon: "smtp.verizon.net"
        email_port : int
            The port to connect to. This function attempts to make an SSL
            connection.
        """
        self.from_address = from_address
        self.email_app_password = email_app_password
        self.log_file_path = log_file_path
        self.email_server = email_server
        self.email_port = email_port

    def __enter__(self) -> Sender:
        ctx = ssl.create_default_context()
        self.smtp = smtplib.SMTP_SSL(self.email_server, self.email_port, context=ctx)
        self.smtp.login(self.from_address, self.email_app_password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.smtp:
            self.smtp.close()
        if exc_type is not None:
            raise exc_type(exc_val)

    def send(self, msg: EmailMessage) -> None:
        """Sends an email.

        Parameters
        ----------
        msg : EmailMessage
            The email message to send.
        """
        self.smtp.send_message(msg)
        if self.log_file_path:
            log(msg, self.log_file_path)
        self.__print_recipient_addresses(msg)

    def __print_recipient_addresses(self, msg: EmailMessage) -> None:
        """Prints all recipient addresses.

        Parameters
        ----------
        msg : EmailMessage
            The email message to print the recipient addresses of.
        """
        print("Email sent")
        if msg["To"]:
            print(f'\tto: {msg["To"]}')
        if msg["Cc"]:
            print(f'\tCC: {msg["Cc"]}')
        if msg["Bcc"]:
            print(f'\tBCC: {msg["Bcc"]}')

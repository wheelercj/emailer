from __future__ import annotations
from .utils import log
from email.message import EmailMessage
import smtplib
import ssl
from typing import Optional


# TODO: make this async
# https://realpython.com/python-with-statement/#creating-an-asynchronous-context-manager
# https://docs.python.org/3/library/asyncio.html
# https://docs.python.org/3/library/asyncio-api-index.html
# https://docs.python.org/3/library/asyncio-task.html#asyncio-example-gather


class Sender:
    def __init__(
        self,
        from_address: str,
        email_app_password: str,
        log_file_path: str = "sent.log",
        email_server: Optional[str] = None,
        email_port: Optional[int] = None,
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
        email_server : Optional[str]
            The email server to connect to. This will usually be automatically
            determined from your email address.
        email_port : Optional[int]
            The port to connect to. This will usually be automatically
            determined from your email address. An SSL connection will be
            attempted.
        """
        self.from_address = from_address
        self.email_app_password = email_app_password
        self.log_file_path = log_file_path
        self.email_server = email_server
        if not self.email_server:
            self.email_server = self.__get_email_server(self.from_address)
        self.email_port = email_port
        if not self.email_port:
            self.email_port = self.__get_email_port(self.email_server)

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

    def __get_email_server(self, email_address: str) -> str:
        """Attempts to get the correct email server from an email address."""
        domain = email_address.split("@")[1]
        if domain == "1and1.com":
            return "smtp.1and1.com"
        elif domain == "1und1.de":
            return "smtp.1und1.de"
        elif domain == "aol.com":
            return "smtp.aol.com"
        elif domain == "att.yahoo.com":
            return "smtp.att.yahoo.com"
        elif domain == "au.yahoo.com":
            return "smtp.mail.yahoo.com.au"
        elif domain == "btinternet.com":
            return "mail.btinternet.com"
        elif domain == "btopenworld.com":
            return "mail.btopenworld.com"
        elif domain == "comcast.net":
            return "smtp.comcast.net"
        elif domain == "csun.edu":
            return "smtp.live.com"
        elif domain == "gmail.com":
            return "smtp.gmail.com"
        elif domain == "gmx.com":
            return "smtp.gmx.com"
        elif domain == "icloud.com":
            return "smtp.mail.me.com"
        elif domain == "laccd.edu":
            return "smtp.live.com"
        elif domain == "lavc.edu":
            return "smtp.live.com"
        elif domain == "live.com":
            return "smtp.live.com"
        elif domain == "mail.com":
            return "smtp.mail.com"
        elif domain == "my.csun.edu":
            return "smtp.gmail.com"
        elif domain == "ntlworld.com":
            return "smtp.ntlworld.com"
        elif domain == "o2.co.uk":
            return "o2.co.uk"
        elif domain == "o2.ie":
            return "smtp.o2.ie"
        elif domain == "o2online.de":
            return "mail.o2online.de"
        elif domain == "office365.com":
            return "smtp.office365.com"
        elif domain == "orange.net":
            return "smtp.orange.net"
        elif domain == "outlook.com":
            return "smtp.live.com"
        elif domain == "postoffice.net":
            return "smtp.postoffice.net"
        elif domain == "privateemail.com":
            return "mail.privateemail.com"
        elif domain == "secureserver.net":
            return "smtpout.secureserver.net"
        elif domain == "student.laccd.edu":
            return "smtp.live.com"
        elif domain == "t-online.de":
            return "t-online.de"
        elif domain == "verizon.net":
            return "outgoing.verizon.net"
        elif domain == "yahoo.co.uk":
            return "smtp.mail.yahoo.co.uk"
        elif domain == "yahoo.com":
            return "smtp.mail.yahoo.com"
        elif domain == "zoho.com":
            return "smtp.zoho.com"
        else:
            raise ValueError(f"Could not determine email server from {email_address}.")

    def __get_email_port(self, email_server: str) -> int:
        """Attempts to get the correct email port from an email server."""
        if email_server in (
            "mail.btinternet.com",
            "mail.btopenworld.com",
            "mail.o2online.de",
            "smtp.o2.co.uk",
            "smtp.o2.ie",
            "smtp.orange.co.uk",
            "smtp.orange.net",
            "smtp.wanadoo.co.uk",
        ):
            return 25
        if email_server in (
            "mail.privateemail.com",
            "outgoing.yahoo.verizon.net",
            "securesmtp.t-online.de",
            "smtp.1and1.com",
            "smtp.1und1.de",
            "smtp.aol.com",
            "smtp.comcast.net",
            "smtp.mail.com",
            "smtp.mail.me.com",
            "smtp.office365.com",
            "smtpout.secureserver.net",
        ):
            return 587
        return 465

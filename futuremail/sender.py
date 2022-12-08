from __future__ import annotations

import json
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from .utils import log


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
        self.email_server = email_server or self.__get_email_server(self.from_address)
        self.email_port = email_port or self.__get_email_port(self.email_server)

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
        with open("resources/smtp-domains.json", "r", encoding="utf8") as file:
            domains = json.load(file)
        return domains[email_address.split("@")[1]]

    def __get_email_port(self, email_server: str) -> int:
        """Attempts to get the correct email port from an email server."""
        with open("resources/smtp-ports.json", "r", encoding="utf8") as file:
            server_ports = json.load(file)
        if email_server in server_ports:
            return server_ports[email_server]
        return 465

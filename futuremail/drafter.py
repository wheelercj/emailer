from __future__ import annotations

import imaplib
import json
import ssl
import time
from email.message import EmailMessage
from typing import Optional


# TODO: embedding images does not work for drafts for some reason. Maybe use
# the Gmail API to handle Gmail drafts?


class Drafter:
    def __init__(
        self,
        from_address: str,
        email_app_password: str,
        email_server: Optional[str] = None,
        mailbox_name: Optional[str] = None,
        email_port: int = 993,
    ):
        """Creates a context manager for creating email drafts.

        Parameters
        ----------
        from_address : str
            Your email address.
        email_app_password : str
            The app password to access your email account. For gmail, this is
            different from your google password. To create a gmail app
            password, go to https://myaccount.google.com/apppasswords.
            Multi-factor authentication must be enabled to visit this site.
        email_server : Optional[str]
            The email server to connect to. This will usually be automatically
            determined from your email address.
        mailbox_name : Optional[str]
            The name of the mailbox to create the draft in. This will usually
            be automatically determined from your email address. If you're not
            sure what the mailbox name should be, try the default and a helpful
            error message will be shown if needed.
        email_port : int
            The port to connect to. An SSL connection will be attempted.
            Apparently all email servers use the same port for SSL IMAP?
        """
        self.from_address = from_address
        self.email_app_password = email_app_password
        self.email_port = email_port
        self.email_server = email_server or self.__get_email_server(self.from_address)
        self.imap = imaplib.IMAP4_SSL(
            self.email_server, self.email_port, ssl_context=ssl.create_default_context()
        )
        self.imap.login(self.from_address, self.email_app_password)
        self.__mailbox_folder_list = self.__get_mailbox_folder_list(self.imap)
        self.mailbox_name = mailbox_name or self.__get_mailbox_name(
            self.email_server, self.__mailbox_folder_list
        )

    def __enter__(self) -> "Drafter":
        self.__validate_mailbox_name(self.mailbox_name, self.__mailbox_folder_list)
        status, _ = self.imap.select(mailbox=self.mailbox_name, readonly=False)
        if status != "OK":
            if self.imap:
                self.imap.close()
            raise RuntimeError(f"Could not select mailbox {self.mailbox_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.imap:
            self.imap.close()
        if exc_type is not None:
            raise exc_type(exc_val)

    def draft(self, msg: EmailMessage) -> None:
        """Creates a draft email.

        Parameters
        ----------
        msg : EmailMessage
            The email message to create a draft of.
        """
        self.imap.append(
            mailbox=self.mailbox_name,
            flags="",
            date_time=imaplib.Time2Internaldate(time.time()),
            message=str(msg).encode("utf8"),  # type: ignore
        )
        print("Draft created.")

    def __get_email_server(self, email_address: str) -> str:
        """Attempts to get the correct email server from an email address."""
        with open("resources/imap-domains.json", "r", encoding="utf8") as file:
            domains = json.load(file)
        return domains[email_address.split("@")[-1]]

    def __get_mailbox_name(
        self, email_server: str, mailbox_folder_list: list[str]
    ) -> str:
        """Attempts to get the correct mailbox name."""
        if email_server == "imap.gmail.com":
            return "[Gmail]/Drafts"
        for folder in mailbox_folder_list:
            if "draft" in folder.lower():
                return folder
        raise ValueError(
            "Could not determine the mailbox name from the email server and/or the"
            " mailbox folder list."
        )

    def __validate_mailbox_name(
        self, mailbox_name: str, mailbox_folder_list: list[str]
    ) -> None:
        if mailbox_name not in mailbox_folder_list:
            raise ValueError(
                f"The mailbox {self.mailbox_name} does not exist. "
                f"Select one of the following: {mailbox_folder_list}"
            )

    def __get_mailbox_folder_list(self, imap) -> list[str]:
        status, mailboxes = imap.list()
        if status != "OK":
            raise RuntimeError(
                "Could not connect to the email server to list the mailboxes."
            )
        return [str(folder).split('"')[-2] for folder in mailboxes]

from email.message import EmailMessage
import imaplib
import ssl
import time


# TODO: embedding images does not work for drafts for some reason. Maybe use
# the Gmail API to handle Gmail drafts?


class Drafter:
    def __init__(
        self,
        from_address: str,
        email_app_password: str,
        email_server: str = "imap.gmail.com",
        mailbox_name: str = "[Gmail]/Drafts",
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
        email_server : str
            The email server to connect to.
            Gmail: "imap.gmail.com"
            Outlook.com/Hotmail.com: "imap-mail.outlook.com"
            Yahoo Mail: "imap.mail.yahoo.com"
            AT&T: "imap.mail.att.net"
            Comcast: "imap.comcast.net"
            Verizon: "incoming.verizon.net"
        mailbox_name : str
            The name of the mailbox to create the draft in. If you're not sure
            what the mailbox name should be, try the default and a helpful
            error message will be shown if needed.
        email_port : int
            The port to connect to. This function attempts to make an SSL
            connection.
        """
        self.from_address = from_address
        self.email_app_password = email_app_password
        self.email_server = email_server
        self.mailbox_name = mailbox_name
        self.email_port = email_port

    def __enter__(self) -> "Drafter":
        self.imap = imaplib.IMAP4_SSL(
            self.email_server, self.email_port, ssl_context=ssl.create_default_context()
        )
        self.imap.login(self.from_address, self.email_app_password)
        status, mailboxes = self.imap.list()
        if status != "OK":
            if self.imap:
                self.imap.close()
            raise RuntimeError(f"Could not list mailboxes: {mailboxes}")
        folder_list = [str(folder).split('"')[-2] for folder in mailboxes]
        if self.mailbox_name not in folder_list:
            if self.imap:
                self.imap.close()
            raise ValueError(
                f"The mailbox {self.mailbox_name} does not exist. "
                f"Select one of the following: {folder_list}"
            )
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
            message=str(msg).encode("utf8"),
        )
        print("Draft created.")

from datetime import datetime
from email.message import EmailMessage
from textwrap import dedent
import smtplib
import sqlite3


def assert_unique(
    text: str, key: str, database_path: str = "unique_strings.db"
) -> None:
    """Asserts that the given text has not been used before with the given key.

    Parameters
    ----------
    text : str
        The text to check and save.
    key : str
        The category of the text.
    database_path : str
        The path to the local database file. A table named "unique_strings"
        will be created if it does not exist.

    Raises
    ------
    RuntimeError
        If the text has already been used with the given key.
    """
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS unique_strings (
            id INTEGER PRIMARY KEY,
            key TEXT,
            text TEXT
            )"""
        )
        cur.execute(
            """SELECT *
            FROM unique_strings
            WHERE key = ?
            AND text = ?""",
            (key, text),
        )
        if cur.fetchall():
            raise RuntimeError(f'"{text}" has already been used as a {key}')
        cur.execute(
            """INSERT INTO unique_strings
            (key, text)
            VALUES (?, ?)""",
            (key, text),
        )


def log(msg: EmailMessage, log_file_path: str) -> None:
    """Logs an email's recipient(s), subject, and send time to a file.

    Parameters
    ----------
    msg : EmailMessage
        The email message to log.
    log_file : str
        The path to the log file.
    """
    now = datetime.now()
    with open(log_file_path, "a") as file:
        file.write(
            dedent(
                f"""\
                {now.strftime('%Y-%m-%d %H:%M:%S')} - {msg['Subject']}
                \tTo: {msg['To']}
                \tCC: {msg['Cc']}
                \tBCC: {msg['Bcc']}
                """
            )
        )


def localhost_send(msg: EmailMessage) -> None:
    """Immediately sends an email to a mail server on localhost.

    The mail server can be started with the following command:
    $ python3 -m smtpd -c DebuggingServer -n localhost:1025

    Parameters
    ----------
    msg : EmailMessage
        The email message to send.
    """
    with smtplib.SMTP("localhost", 1025) as smtp:
        smtp.send_message(msg)
    print("Email sent to localhost.")

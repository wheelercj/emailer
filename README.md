# emailer

An email client with a "Python user interface" (no user interface) for maximum customizability in how you send and draft emails. Those who already know Python will find this much easier to use than both Mail Merge and Python's built-in emailing tools.

## features

* Write emails in a string with either markdown, plain text, or HTML.
* Files are easy to attach and images are easy to embed.
* Quickly load contact info from one of many file formats or string formats into Python objects.
* Be confident and write emails fast. You can use `emailer.assert_unique` to raise an exception if you accidentally reuse a subject, attachment name, or any other string, even between runs.
* The code is easy to read and change. Type hints and docstrings are used almost everywhere possible, and the code has been auto-formatted with Black.

Here is a small example, and a more comprehensive one is at the end of this page.

```python
from emailer import Sender, create_email_message, contacts
import os
from textwrap import dedent
from dotenv import load_dotenv  # https://pypi.org/project/python-dotenv/
load_dotenv()

contacts_str = dedent(
    # first_name, last_name, email_address, group_name
    """\
    Maximillian, Marsh, remedy@inbox.com, member
    Kolby, Bradshaw, publisher@mail.com, member
    Virginia, Andersen, suburb@gmail.com, member
    Braiden, Villanueva, resolution@yahoo.com, member
    """  # This contact info is fake.
)

my_email_address = os.environ.get("EMAIL_ADDRESS")
my_email_password = os.environ.get("EMAIL_PASSWORD")
subject = "This is the email's subject"
recipients = contacts.load_from_str(contacts_str)

with Sender(my_email_address, my_email_password) as sender:
    for recipient in recipients:
        email_content = dedent(
            f"""\
            Greetings {recipient.first_name},

            This email was created and sent with Python!
            """
        )

        msg = create_email_message(
            from_address=my_email_address,
            subject=subject,
            plaintext_content=email_content,
            md_content=email_content,
            to_addresses=[recipient.email_address],
        )

        sender.send(msg)
```

## usage

Download the source code, and then install it as a local package with the terminal command `python3 -m pip install -e .` while in the same folder as the source code. This will also install the third party dependencies listed in `requirements.txt`. Now you can import emailer in other Python files saved anywhere on your computer. Be sure to avoid naming a Python file the same as one built into the Python language, such as `email.py`. I happen to use this with gmail; if you use a different email service provider, you will need to specify the email server and possibly the email port as explained in the docstrings.

## public functions and classes

For each of the functions for loading contacts, a filter predicate can be provided to filter out some contacts. If a contacts file is used, the first row of the file is ignored by default. The order of the columns in the file must be the same as the order of the variables in the Contact class (you can just rearrange the Contact class if needed).

**emailer.assert_unique** - Asserts that the given text has not been used before with the given key. Given strings are saved to a local sqlite3 database file named `unique_strings.db`. If the same two strings are given again, an exception is raised.

**emailer.contacts.Contact** - A dataclass for holding one person's contact info.

**emailer.contacts.Contacts** - A class for holding multiple Contact objects.

**emailer.contacts.load_from_csv** - Loads contacts from a CSV file.

**emailer.contacts.load_from_str** - Loads contacts from a string. By default, each contact must be on its own line and must contain the comma-separated data specified in the Contact class (in contacts.py). The delimiter is easy to change from a comma to anything else.

**emailer.contacts.load_from_tsv** - Loads contacts from a TSV file.

**emailer.contacts.load_from_xlsx** - Loads contacts from an XLSX file.

**emailer.create_email_message** - Creates an email message object.

**emailer.Drafter** - A context manager that creates an object for drafting emails using an email message object.

**emailer.localhost_send** - Sends an email using an email object to localhost for testing.

**emailer.log** - Logs the current time and the recipient(s) and subject of an email message object.

**emailer.Sender** - A context manager that creates an object for sending emails using an email message object. By default, each email's send time, subject, and recipient(s) are logged to a file named `sent.log`.

## large example

```python
from emailer import Sender, create_email_message, contacts, assert_unique
import os
from textwrap import dedent
from dotenv import load_dotenv  # https://pypi.org/project/python-dotenv/
load_dotenv()

# The format of the contact info below is based on the Contact dataclass in
# contacts.py, which you can change at any time.
contacts_str = dedent(
    # first_name, last_name, email_address, group_name
    """\
    For, Testing, different.email@duck.com, me
    Maximillian, Marsh, remedy@inbox.com, member
    Kolby, Bradshaw, shout@outlook.com, member
    Virginia, Andersen, suburb@gmail.com, member
    Braiden, Villanueva, resolution@yahoo.com, member
    Alissa, Douglas, achievement@gmail.com, member
    Miracle, Buckley, someone@icloud.com, member
    Taylor, Nelson, seminar@mail.com, member
    Tamara, Snyder, reappoint@gmail.com, member
    Haleigh, Rios, publisher@icloud.com, member
    Charity, Parrish, language@yahoo.com, member
    """
    # If you prefer, you could instead keep the contact info in an XLSX, CSV,
    # or TSV file and load it with the appropriate function listed below in
    # place of `contacts.load_from_str`.
)

my_email_address = os.environ.get("EMAIL_ADDRESS")
my_email_password = os.environ.get("EMAIL_PASSWORD")
subject = "This is the email's subject"
assert_unique(subject, "subject")
recipients = contacts.load_from_str(contacts_str, lambda x: x.group_name == "me")
attachment_paths = ["C:/Users/chris/Documents/book voucher.pdf"]
# I happen to use an absolute file path here and for an embedded image below,
# but you can just use the file's name if it's in the same folder as emailer's
# source code.
for path in attachment_paths:
    assert_unique(path, "attachment paths")

with Sender(my_email_address, my_email_password) as sender:
    for recipient in recipients:
        email_content = dedent(
            f"""\
            Greetings {recipient.first_name},

            This is a sample email. These can be written in markdown (like this
            one), HTML, or in plain text.
            
            The first line of this email will show the correct first name for
            each recipient, and it's easy to add more info that's different for
            each person. Just add a variable to the Contact dataclass in
            contacts.py and add to your list of contact info.

            ## markdown syntax samples

            All of these markdown elements will be converted to HTML and will
            look great in the final result, including:
            
            * bullet points
            * [links to websites](https://zombo.com/)
            * embedded images (see below)
            * **bold** and _italic_
            * headers
            * numbered list items
            * tables
            * and more
            
            Everything in markdown works, which includes basically everything
            commonly used in emails.

            1. The numbers for these numbered
            1. list items will be automatically
            1. changed to the correct numbers.

            Here's an embedded image:

            ![alt text](C:/Users/chris/Pictures/an image.jpg)

            I have also attached a file by adding its file path to the
            attachment_paths list, as you can see above this email.

            Let me know if you have any questions or concerns!

            Kind regards,  
            Chris Wheeler  
            christopher.wheeler.320@my.csun.edu  
            """
            # If you use markdown and want multiple lines (that are not bullet
            # points, ordered list items, etc.) next to each other like in the
            # email signature, make sure you end each line with two (or more)
            # spaces. Markdown removes the line breaks otherwise.
        )

        msg = create_email_message(
            from_address=my_email_address,
            subject=subject,
            plaintext_content=email_content,
            md_content=email_content,
            attachment_paths=attachment_paths,
            to_addresses=[recipient.email_address],
        )

        sender.send(msg)
```

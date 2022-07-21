import imghdr
import re
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Optional

from mistune import markdown as HTMLConverter  # https://github.com/lepture/mistune


def create_email_message(
    from_address: str,
    subject: str,
    plaintext_content: str,
    md_content: Optional[str] = None,
    html_content: Optional[str] = None,
    attachment_paths: Optional[list[str]] = None,
    to_addresses: Optional[list[str]] = None,
    cc_addresses: Optional[list[str]] = None,
    bcc_addresses: Optional[list[str]] = None,
) -> EmailMessage:
    """Initializes an email message object.

    Parameters
    ----------
    from_address : str
        Your email address.
    subject : str
        The subject of the email.
    plaintext_content : str
        The body of the email. Required even if md or html content is given
        because some email clients do not display html emails.
    md_content : Optional[str]
        The markdown content of the email. Replaces plaintext_content if given
        and if the recipient's email client supports HTML emails. The markdown
        content is converted to HTML. Do not give both md_content and
        html_content.
    html_content : Optional[str]
        The HTML body of the email. Replaces plaintext_content if given and if
        the recipient's email client supports HTML emails. Any markdown links
        will be converted to HTML links for both URLs and images. Do not give
        both md_content and html_content.
    attachment_paths : Optional[list[str]]
        The paths to the files to be attached to the email.
    to_addresses : Optional[list[str]]
        The email addresses of the recipients.
    cc_addresses : Optional[list[str]]
        The email addresses of the CC recipients.
    bcc_addresses : Optional[list[str]]
        The email addresses of the BCC recipients.
    """
    if md_content and html_content:
        raise ValueError("Do not give both md_content and html_content.")
    msg = EmailMessage()
    if not subject:
        raise ValueError("subject must be given")
    msg["Subject"] = subject
    msg["From"] = from_address
    __add_recipients(msg, to_addresses, cc_addresses, bcc_addresses)
    if not plaintext_content:
        raise ValueError("plaintext_content must be given")
    msg.set_content(plaintext_content)
    if html_content is None and md_content is not None:
        html_content_s = HTMLConverter(md_content)
        html_content_s = __convert_md_links_to_html_links(html_content_s)
        __add_html(msg, html_content_s)
    elif html_content is not None:
        html_content_s = __convert_md_links_to_html_links(html_content)
        __add_html(msg, html_content_s)
    if attachment_paths:
        __add_attachments(msg, attachment_paths, plaintext_content)
    return msg


def __add_attachments(
    msg: EmailMessage, attachment_paths: list[str], plaintext_content: str
) -> None:
    """Adds attachments to an email message object.

    Parameters
    ----------
    msg : EmailMessage
        The email message object to which the attachments will be added.
    attachment_paths : list[str]
        The paths to the files to be attached to the email.
    plaintext_content : str
        The plaintext content of the email.
    """
    if isinstance(attachment_paths, str):
        attachment_paths = [attachment_paths]
    __check_for_attachment_hints(plaintext_content, attachment_paths)
    image_types = ["jpg", "jpeg", "png", "gif"]
    tested_file_types = ["jpg", "jpeg", "docx", "pdf", "md"]
    for path in attachment_paths:
        with open(path, "rb") as f:
            file_data = f.read()
            file_name = f.name.split("/")[-1]
            file_ext = file_name.split(".")[-1]
            if file_ext not in tested_file_types:
                raise ValueError(f"File type {file_ext} not tested.")
            if file_ext in image_types:
                maintype = "image"
                subtype = imghdr.what(f.name)
            elif file_ext == "xlsx":
                maintype = "application/xlsx"
                subtype = "xlsx"
            elif file_ext == "csv":
                maintype = "csv"
                subtype = "None"
            else:
                maintype = "application"
                subtype = "octet-stream"
        msg.add_attachment(
            file_data, maintype=maintype, subtype=subtype, filename=file_name
        )


def __check_for_attachment_hints(
    plaintext_content: str, attachment_paths: list[str]
) -> None:
    """Checks for the presence of attachment hints in the email body.

    Raises ValueError if the email body contains an attachment hint.

    Parameters
    ----------
    plaintext_content : str
        The plaintext content of the email.
    attachment_paths : list[str]
        The paths to the files to be attached to the email.
    """
    if not attachment_paths:
        attachment_hints = [
            # These must all be lowercase.
            "attach",
            "enclosed",
            " cv ",
            "resume",
            "cover letter",
            ".doc",
            ".pdf",
            ".xls",
            ".ptt",
            ".pps",
        ]
        plaintext_content = plaintext_content.lower()
        for hint in attachment_hints:
            if hint in plaintext_content:
                raise ValueError(
                    f'Attachment required because "{hint}" is in the email.'
                )


def __add_recipients(
    msg: EmailMessage,
    to_addresses: Optional[list[str]],
    cc_addresses: Optional[list[str]],
    bcc_addresses: Optional[list[str]],
) -> None:
    """Adds recipients to the email message object.

    Parameters
    ----------
    msg : EmailMessage
        The email message object.
    to_addresses : Optional[list[str]]
        The email addresses of the recipients.
    cc_addresses : Optional[list[str]]
        The email addresses of the CC recipients.
    bcc_addresses : Optional[list[str]]
        The email addresses of the BCC recipients.
    """
    if not to_addresses and not cc_addresses and not bcc_addresses:
        raise ValueError("At least one recipient must be given.")
    if to_addresses:
        msg["To"] = ", ".join(to_addresses)
    if cc_addresses:
        msg["Cc"] = ", ".join(cc_addresses)
    if bcc_addresses:
        msg["Bcc"] = ", ".join(bcc_addresses)


def __convert_md_links_to_html_links(
    html_content: str, image_width: str = "70%"
) -> str:
    """Converts markdown url links and image links to html.

    Parameters
    ----------
    html_content : str
        The html content to be converted.
    image_width : str
        The width of the image, if the link is for an embedded image.
    """
    md_image_link_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
    html_content = md_image_link_pattern.sub(
        rf'<img src="\2" alt="\1" style="width:{image_width}" />', html_content
    )
    md_link_pattern = re.compile(r"\[(.*?)\]\((.*?)\)")
    html_content = md_link_pattern.sub(r'<a href="\2">\1</a>', html_content)
    return html_content


def __add_html(msg: EmailMessage, html_content: str) -> None:
    """Adds a html content to the email message object.

    Parameters
    ----------
    msg : EmailMessage
        The email message object.
    html_content : str
        The html content to be added.
    """
    html_content, embedded_image_paths, image_ids = __convert_image_links(html_content)
    msg.add_alternative(html_content, subtype="html", charset="utf8")
    __embed_images(msg, embedded_image_paths, image_ids)


def __embed_images(
    msg: EmailMessage, embedded_image_paths: list[str], image_ids: list[str]
) -> None:
    """Embeds images in the email.

    Parameters
    ----------
    msg : EmailMessage
        The email message object.
    embedded_image_paths : list[str]
        The paths to the images to be embedded.
    image_ids : list[str]
        The image IDs to be embedded.
    """
    for i, path in enumerate(embedded_image_paths):
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype=path.split(".")[-1],
                filename=path.split("/")[-1],
                cid=image_ids[i],
            )


def __convert_image_links(html_content: str) -> tuple[str, list[str], list[str]]:
    """Converts image links to cid links.

    Parameters
    ----------
    html_content : str
        The HTML content of the email.

    Returns
    -------
    html_content : str
        The HTML content of the email with image links converted to cid links.
    embedded_image_paths : list[str]
        The paths to the embedded images.
    image_ids : list[str]
        The image IDs.
    """
    image_link_pattern = re.compile(
        r"(?<=<img src=[\'\"])(?!cid:)(.+?)(?=[\'\"] ?(?:alt=.+?)? ?/?>)"
    )
    embedded_image_paths = image_link_pattern.findall(html_content)
    image_ids: list[str] = __create_image_ids(len(embedded_image_paths))
    for image_id in image_ids:
        html_content = image_link_pattern.sub(
            f"cid:{image_id[1:-1]}", html_content, count=1
        )
    return html_content, embedded_image_paths, image_ids


def __create_image_ids(num: int) -> list[str]:
    """Makes a list of image IDs.

    Parameters
    ----------
    num : int
        The number of image IDs to make.
    """
    return [make_msgid() for _ in range(num)]

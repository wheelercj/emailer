from dataclasses import dataclass
from typing import Iterator, Callable
import openpyxl  # https://pypi.org/project/openpyxl/


@dataclass
class Contact:
    first_name: str
    last_name: str
    email_address: str
    group_name: str


def load_from_xlsx(
    file_path: str, filter_predicate: Callable = None, first_data_row: int = 2
) -> Iterator:
    """Loads contacts from an XLSX file.

    The order of the columns in the file must be the same as the order of the
    variables in the Contact class (you can just rearrange the Contact class
    if needed).

    Parameters
    ----------
    file_path : str
        The path to the XLSX file.
    filter_predicate : Callable, None
        A function that takes a Contact object as its only argument that can be
        used to load only some of the contacts present in the string.
    first_data_row : int
        The (1-based) row number of the first row of data in the XLSX file.
    """
    contacts_obj = Contacts()
    wb = openpyxl.load_workbook(file_path)
    ws1 = wb.active
    for row in ws1.iter_rows(min_row=first_data_row, values_only=True):
        contacts_obj.append(Contact(*row))
    return filter(filter_predicate, contacts_obj)


def load_from_str(
    contacts_: str, filter_predicate: Callable = None, delimiter: str = ","
) -> Iterator:
    """Loads contacts from a string.

    Parameters
    ----------
    contacts_ : str
        The string containing the contacts. Each contact must be on its own
        line and must have the data specified in the Contact class.
    filter_predicate : Callable, None
        A function that takes a Contact object as its only argument that can be
        used to load only some of the contacts present in the string.
    delimiter : str
        The delimiter used to separate the data in the string. After splitting,
        whitespace characters will be removed from the beginning and end of
        each string.
    """
    contacts_obj = Contacts()
    for line in contacts_.splitlines():
        if not line:
            continue
        fields = line.split(delimiter)
        for i, field in enumerate(fields):
            fields[i] = field.strip()
        contacts_obj.append(Contact(*fields))
    return filter(filter_predicate, contacts_obj)


def load_from_csv(file_path: str, filter_predicate: Callable = None) -> Iterator:
    """Loads contacts from a CSV string.

    Parameters
    ----------
    file_path : str
        The path to the CSV file.
    filter_predicate : Callable, None
        A function that takes a Contact object as its only argument that can be
        used to load only some of the contacts present in the string.
    """
    with open(file_path) as file:
        contacts_ = file.read()
    return load_from_str(contacts_, filter_predicate, ",")


def load_from_tsv(file_path: str, filter_predicate: Callable = None) -> Iterator:
    """Loads contacts from a TSV string.

    Parameters
    ----------
    file_path : str
        The path to the TSV file.
    filter_predicate : Callable, None
        A function that takes a Contact object as its only argument that can be
        used to load only some of the contacts present in the string.
    """
    with open(file_path) as file:
        contacts_ = file.read()
    return load_from_str(contacts_, filter_predicate, "\t")


class Contacts:
    def __init__(self):
        self.data: list[Contact] = []

    def __getitem__(self, first_and_last_name: str) -> Contact:
        for contact in self.data:
            if contact.first_name + " " + contact.last_name == first_and_last_name:
                return contact
        raise KeyError(f"No contact with name {first_and_last_name}")

    def __setitem__(self, first_and_last_name: str, new_contact: Contact) -> None:
        for contact in self.data:
            if contact.first_name + " " + contact.last_name == first_and_last_name:
                raise KeyError(
                    f"There is already a contact with name {first_and_last_name}"
                )
        self.data.append(new_contact)

    def append(self, new_contact: Contact) -> None:
        self.data.append(new_contact)

    def __iter__(self) -> iter:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, first_and_last_name: str) -> bool:
        for contact in self.data:
            if contact.first_name + " " + contact.last_name == first_and_last_name:
                return True
        return False

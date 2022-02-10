from dataclasses import dataclass
from typing import Iterator, Callable


def load(contacts: str, filter_predicate: Callable = None) -> Iterator:
    """Loads contacts from a string.

    Parameters
    ----------
    contacts : str
        The string containing the contacts. Each contact must be on its own
        line and must contain the comma-separated data specified in the Contact
        class.
    filter_predicate : Callable, optional
        A function that takes a Contact object as its only argument that can be
        used to load only some of the contacts present in the string.
    """
    contacts_obj = Contacts()
    for line in contacts.splitlines():
        fields = *line.split(",")
        for i, field in enumerate(fields):
            fields[i] = field.strip()
        contacts_obj.append(Contact(fields))
    return filter(filter_predicate, contacts_obj)


@dataclass
class Contact:
    first_name: str
    last_name: str
    email_address: str
    group_name: str


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

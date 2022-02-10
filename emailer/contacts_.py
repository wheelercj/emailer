from dataclasses import dataclass


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

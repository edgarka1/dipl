from typing import TypedDict, NotRequired


class MenuButtonCallbackData(TypedDict):
    section: str


class MenuButton(TypedDict):
    text: str
    callback_data: MenuButtonCallbackData


class MenuButtonGroup(TypedDict):
    buttons: list[MenuButton]


class MenuKeyboard(TypedDict):
    groups_buttons: list[MenuButtonGroup]


class MenuSection(TypedDict):
    name: str
    text: str
    keyboard: MenuKeyboard
    file: NotRequired[str]

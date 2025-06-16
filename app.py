import os
import json
from typing import OrderedDict
from collections.abc import Callable
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QTreeWidgetItem, QTableWidgetItem
from PyQt6.QtGui import QIcon

from ui import UiMainWindow, UiAddSectionDialog
from type import MenuSection, MenuKeyboard, MenuButtonGroup, MenuButton, MenuButtonCallbackData
from server_client import ServerClient


main_window: QMainWindow | None = None
add_section_dialog: QDialog | None = None    


class MainWindow(QMainWindow, UiMainWindow):
    MENU_REMOTE_FILE_PATH = '/var/www/TelegramBotKPA/menu_structure.json'
    MENU_LOCAL_FILE_PATH = './tmp/menu_structure.json'


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon('./logo_book.png'))
        self.setupUi(self)

        self.menu_sections: list[MenuSection] = []

        self.load_menu_button.released.connect(self.load_menu)
        self.sections_tree_widget.itemClicked.connect(self.select_section_callback)
        self.save_menu_button.released.connect(self.save_menu)
        self.add_section_button.released.connect(lambda: add_section_dialog.show(self.add_section) if add_section_dialog is not None else None)
        self.del_section_button.released.connect(self.remove_section)
        self.save_section_button.released.connect(self.save_section)
        self.section_add_btn_button.released.connect(self.add_section_keyboard_button)
        self.section_del_btn_button.released.connect(self.remove_section_keyboard_button)

        self.server_client = ServerClient(
            user='www',
            password='Kameta2013!'
        )

        if not os.path.exists('./tmp'):
            os.mkdir('./tmp')

    def get_menu_section_by_name(self, name: str) -> tuple[int, MenuSection] | tuple[None, None]:
        for s_idx, section in enumerate(self.menu_sections):
            if section['name'] == name:
                return s_idx, section
        
        return None, None

    def get_menu_button_by_text(self, section_name: str, button_text: str) -> MenuButton | None:
        _, section = self.get_menu_section_by_name(section_name)

        if section is None:
            return

        for section_group_button in section['keyboard']['groups_buttons']:
            for section_button in section_group_button['buttons']:
                if section_button['text'] == button_text:
                    return section_button

    def get_section_linked_sections(self, section_name: str) -> list[str] | None:
        linked_sections_names = []

        for section in self.menu_sections:
            for section_group_button in section['keyboard']['groups_buttons']:
                for section_button in section_group_button['buttons']:
                    if section_button.get('callback_data', None) is not None:
                        section_button_linked_section_name = section_button['callback_data']['section']
                        
                        if section_button_linked_section_name == section_name:
                            if section['name'] not in linked_sections_names:
                                linked_sections_names.append(section['name'])
        
        return linked_sections_names

    def load_menu(self) -> None:
        menu_sections: list[MenuSection] = []

        menu_structure: list[dict] = []

        self.server_client.download_file(
            file_path=self.MENU_REMOTE_FILE_PATH,
            path_to_save=self.MENU_LOCAL_FILE_PATH
        )

        with open(self.MENU_LOCAL_FILE_PATH, 'r', encoding='utf-8') as menu_structure_file:
            menu_structure = json.load(menu_structure_file, object_pairs_hook=OrderedDict)
        
        for section in menu_structure:
            menu_section = MenuSection(
                name=section.get('name', ''),
                text=section.get('text', ''),
                keyboard=MenuKeyboard(
                    groups_buttons=[]
                )
            )

            for button_group in section.get('keyboard', []):
                menu_section_button_group = MenuButtonGroup(
                    buttons=[]
                )
                
                for button in button_group:
                    menu_section_button_group['buttons'].append(
                        MenuButton(
                            text=button.get('text', ''),
                            callback_data=MenuButtonCallbackData(
                                **button.get('callback_data', {})
                            )
                        )
                    )
                
                menu_section['keyboard']['groups_buttons'].append(menu_section_button_group)
            
            menu_sections.append(menu_section)
        
        self.menu_sections = menu_sections

        self.fill_menu_sections_tree()
    
    def fill_menu_sections_tree(self):
        self.sections_tree_widget.clear()
        self.sections_tree_widget.setColumnCount(1)

        for section in self.menu_sections:
            section_tree_item = QTreeWidgetItem(self.sections_tree_widget, [section['name']])
            section_tree_item.setIcon(0, QIcon('./ui/assets/folder.png'))

            for section_group_button in section['keyboard']['groups_buttons']:
                for section_button in section_group_button['buttons']:
                    section_button_tree_item = QTreeWidgetItem([section_button['text']])
                    section_button_tree_item.setIcon(0, QIcon('./ui/assets/interface-button.png'))
                    
                    section_tree_item.addChild(section_button_tree_item)

            self.sections_tree_widget.addTopLevelItem(section_tree_item)
        
    def select_section_callback(self, section_item: QTreeWidgetItem):
        section_name = section_item.text(0)
        section_item_parent = section_item.parent()
        
        if section_item_parent is not None:
            section_name = section_item_parent.text(0)

        _, section = self.get_menu_section_by_name(section_name)

        if section is None:
            return

        section_linked_sections_names = self.get_section_linked_sections(section['name'])

        # Установка значений раздела в поля 
        self.section_name_input.setText(section['name'])

        if section_linked_sections_names:
            self.section_linked_sections_label.setText(', '.join(section_linked_sections_names))
        else:
            self.section_linked_sections_label.setText('Нет ссылочных разделов')
        
        self.section_text_input.clear()
        self.section_text_input.setPlainText(section['text'])

        self.section_file_name_input.setText(section.get('file', None))

        self.section_buttons_table.setRowCount(0)

        for group_btn_idx, section_editable_group_button in enumerate(section['keyboard']['groups_buttons']):
            for btn_idx, section_editable_button in enumerate(section_editable_group_button['buttons']):
                if self.section_buttons_table.rowCount() - 1 <= btn_idx + group_btn_idx:
                    self.section_buttons_table.insertRow(btn_idx + group_btn_idx)
                
                self.section_buttons_table.setItem(
                    btn_idx + group_btn_idx, 0,
                    QTableWidgetItem(section_editable_button['text'])
                )
                self.section_buttons_table.setItem(
                    btn_idx + group_btn_idx, 1,
                    QTableWidgetItem(section_editable_button['callback_data']['section'])
                )
        
    def save_menu(self) -> None:
        self.save_section()
        
        menu_sections = []

        for section in self.menu_sections:
            section_data = {}

            section_data['name'] = section['name']
            section_data['text'] = section['text']
            section_data['keyboard'] = []

            for section_group_button in section['keyboard']['groups_buttons']:
                section_data['keyboard'].append([])
                
                for section_button in section_group_button['buttons']:
                    section_data['keyboard'][-1].append({})
                    section_data['keyboard'][-1][-1]['text'] = section_button['text']

                    if section_button.get('callback_data', None) is not None:
                        section_data['keyboard'][-1][-1]['callback_data'] = section_button['callback_data']
        
            menu_sections.append(section_data)
        
        with open(self.MENU_LOCAL_FILE_PATH, 'w', encoding='utf-8') as menu_structure_file:
            json.dump(menu_sections, menu_structure_file, ensure_ascii=False, indent=4)
        
        # self.server_client.upload_file(file_path=self.MENU_LOCAL_FILE_PATH, path_to_save=self.MENU_REMOTE_FILE_PATH)

    def add_section(self, section_name: str) -> None:
        self.section_linked_sections_label.clear()
        self.section_name_input.setText(section_name)
        self.section_text_input.clear()
        self.section_file_name_input.clear()
        self.section_buttons_table.setRowCount(0)

    def remove_section(self) -> None:
        section_item = self.sections_tree_widget.currentItem()

        if section_item is None:
            return

        section_name = section_item.text(0)
        section_item_parent = section_item.parent()
        
        if section_item_parent is not None:
            section_name = section_item_parent.text(0)

        s_idx, section = self.get_menu_section_by_name(section_name)

        if s_idx is not None and section is not None:
            self.menu_sections.pop(s_idx)
            
            self.section_linked_sections_label.clear()
            self.section_name_input.clear()
            self.section_text_input.clear()
            self.section_file_name_input.clear()
            self.section_buttons_table.setRowCount(0)

            self.fill_menu_sections_tree()

    def add_section_keyboard_button(self) -> None:
        self.section_buttons_table.setRowCount(
            self.section_buttons_table.rowCount() + 1
        )
    
    def remove_section_keyboard_button(self) -> None:
        self.section_buttons_table.removeRow(self.section_buttons_table.currentRow())

    def save_section(self) -> None:
        required_data_exists = all([
            len(self.section_name_input.text()),
            len(self.section_text_input.toPlainText()),
            self.section_buttons_table.rowCount()
        ])

        if not required_data_exists:
            return

        section = MenuSection(
            name=self.section_name_input.text().strip(),
            text=self.section_text_input.toPlainText().strip(),
            keyboard=MenuKeyboard(
                groups_buttons=[]
            )
        )

        for buttons_table_row_idx in range(self.section_buttons_table.rowCount()):
            section['keyboard']['groups_buttons'].append(MenuButtonGroup(buttons=[]))
            
            button_text = self.section_buttons_table.item(buttons_table_row_idx, 0)

            if button_text is not None:
                button_text = button_text.text().strip()

                if not button_text:
                    continue
            
            button_linked_section_name = self.section_buttons_table.item(buttons_table_row_idx, 1)

            if button_linked_section_name is not None:
                button_linked_section_name = button_linked_section_name.text().strip()
            
                if not button_linked_section_name:
                    continue

            if button_text is not None and button_linked_section_name is not None:
                section['keyboard']['groups_buttons'][-1]['buttons'].append(MenuButton(
                    text=button_text,
                    callback_data=MenuButtonCallbackData(
                        section=button_linked_section_name
                    )
                ))
        
        s_idx, exist_section = self.get_menu_section_by_name(section['name'])

        if s_idx is not None and exist_section is not None:
            self.menu_sections[s_idx] = section
        else:
            self.menu_sections.append(section)
        
        self.fill_menu_sections_tree()
            

class AddSectionDialog(QDialog, UiAddSectionDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon('./logo_book.png'))
        self.setupUi(self)

        self.confirm_button.released.connect(self.accept)
        self.cancel_button.released.connect(self.close)

        self.add_section_callback: Callable[[str], None] | None = None
    
    def show(self, add_section_callback: Callable[[str], None] | None = None) -> None:
        if isinstance(add_section_callback, Callable):
            self.add_section_callback = add_section_callback
        
        return super().show()

    def accept(self) -> None:
        section_name = self.section_name_input.text()

        if self.add_section_callback is not None:
            self.add_section_callback(section_name)
        
        return super().accept()


if __name__ == '__main__':
    app = QApplication([])

    main_window = MainWindow()
    add_section_dialog = AddSectionDialog()

    main_window.show()

    app.exec()

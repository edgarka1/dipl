#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Редактор структуры меню Telegram-бота.
Позволяет редактировать JSON с разделами, текстом, кнопками и файлами.
"""

import os
import re
import json
import shutil
from datetime import datetime
from collections import OrderedDict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem,
    QFileDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, QDialog,
    QDialogButtonBox, QHeaderView, QScrollArea, QGroupBox, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction, QFont, QIcon, QPixmap, QColor, QPalette


class AddSectionDialog(QDialog):
    def __init__(self, existing_names=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить раздел")
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                font-family: Arial;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit, QPlainTextEdit {
                border: 1px solid #A2B6C1;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #EF7D05;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        self.existing_names = existing_names or []

        # Основной вертикальный лэйаут
        layout = QVBoxLayout(self)

        # Поле ввода названия раздела
        name_layout = QFormLayout()
        self.name_edit = QLineEdit(self)
        name_layout.addRow("Название раздела:", self.name_edit)

        # Поле ввода текста раздела
        text_layout = QFormLayout()
        self.text_edit = QPlainTextEdit(self)
        text_layout.addRow("Текст раздела:", self.text_edit)

        # Поле выбора файла
        file_layout = QHBoxLayout()
        self.file_line = QLineEdit(self)
        self.file_line.setReadOnly(True)
        file_layout.addWidget(QLabel("Файл:"))
        file_layout.addWidget(self.file_line)
        self.attach_button = QPushButton("Прикрепить файл", self)
        self.remove_file_button = QPushButton("Удалить файл", self)
        self.remove_file_button.setEnabled(False)
        file_layout.addWidget(self.attach_button)
        file_layout.addWidget(self.remove_file_button)

        # Таблица кнопок раздела
        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Название кнопки", "Переход в раздел"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        # Кнопки добавления/удаления строки таблицы
        button_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Добавить кнопку", self)
        self.delete_row_button = QPushButton("Удалить кнопку", self)
        button_layout.addWidget(self.add_row_button)
        button_layout.addWidget(self.delete_row_button)

        # Кнопки OK/Cancel
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )

        # Сборка макета
        layout.addLayout(name_layout)
        layout.addLayout(text_layout)
        layout.addLayout(file_layout)
        layout.addWidget(QLabel("Кнопки раздела:"))
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addWidget(self.button_box)

        # Подключение сигналов
        self.attach_button.clicked.connect(self.attach_file)
        self.remove_file_button.clicked.connect(self.remove_file)
        self.add_row_button.clicked.connect(self.add_button_row)
        self.delete_row_button.clicked.connect(self.delete_button_row)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", "All Files (*)")
        if file_path:
            self.file_line.setText(file_path)
            self.remove_file_button.setEnabled(True)

    def remove_file(self):
        self.file_line.clear()
        self.remove_file_button.setEnabled(False)

    def add_button_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item_text = QTableWidgetItem("")
        item_text.setFlags(item_text.flags() | Qt.ItemFlag.ItemIsEditable)
        item_section = QTableWidgetItem("")
        item_section.setFlags(item_section.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item_text)
        self.table.setItem(row, 1, item_section)

    def delete_button_row(self):
        current = self.table.currentRow()
        if current >= 0:
            self.table.removeRow(current)

    def validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название раздела не может быть пустым.")
            return
        if name in self.existing_names:
            QMessageBox.warning(self, "Ошибка", f"Раздел с именем '{name}' уже существует.")
            return
        self.accept()

    def get_section_data(self):
        name = self.name_edit.text().strip()
        text = self.text_edit.toPlainText()
        file_path = self.file_line.text().strip()
        if not file_path:
            file_path = None
        buttons = []
        for row in range(self.table.rowCount()):
            item_text = self.table.item(row, 0)
            item_section = self.table.item(row, 1)
            if item_text and item_section:
                text_btn = item_text.text().strip()
                section_name = item_section.text().strip()
                if text_btn and section_name:
                    buttons.append((text_btn, section_name))
        return name, text, file_path, buttons


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор структуры меню Telegram-бота")
        self.setMinimumSize(1300, 800)
        #self.setFixedSize(1280, 800)
        #self.setFont(QFont("Segoe UI", 11))
        self.is_loading = False

        self.menu_data: list[OrderedDict] = []
        self.current_section_index = None
        self.current_file_path = None
        self.dirty = False

        self.init_ui()

        self.open_file()

    def init_ui(self):
        # Установка фирменной цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#F5F5F5'))
        palette.setColor(QPalette.ColorRole.WindowText, QColor('#333333'))
        palette.setColor(QPalette.ColorRole.Button, QColor('#EF7D05'))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor('#FFFFFF'))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QGroupBox {
                border: 2px solid #A2B6C1;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 25px;
                font-family: "Helios";
                font-size: 16px;
                color: #333333;
            }
            QPushButton {
                background-color: #EF7D05;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-family: "Arial";
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #E30617;
            }
            QPushButton:disabled {
                background-color: #A2B6C1;
            }
            QListWidget, QPlainTextEdit, QLineEdit, QTableWidget {
                border: 1px solid #A2B6C1;  /* Внешняя граница таблицы */
                border-radius: 4px;
                background: white;
                gridline-color: transparent;  /* Убираем линии сетки */
            }
            QTableWidget {
                border: none;
                background: transparent;
                outline: none; 
                gridline-color: transparent;
            }
            QTableWidget::item {
                border: 0px solid transparent !important;
                background: white;
                padding: 4 px;
            }
            QTableWidget::item:focus, 
            QTableWidget::item:selected {
                border: 0px !important;
                outline: none !important;
                background: #F5F5F5;
            }
            QHeaderView::section {
                background-color: #E30617;
                color: #FFFFFF;
                padding: 12px;
                border: none;
            }
            QLabel {
                color: #333333;
            }
            #previewPane {
                background-image: url(patterns/primary_pattern.png);
                background-repeat: repeat-xy;
                border: 1px solid #A2B6C1;
                border-radius: 6px;
            }
        """)

        # В конструкторе MainWindow добавить логотип
        self.setWindowIcon(QIcon('logo_book.png'))

        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(15)

        # Левая панель
        left_panel = QWidget()
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Логотип
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap('./logo.png')  # Правильное имя файла
            
            if logo_pixmap.isNull():
                raise FileNotFoundError("Файл не найден")

            logo_label.setPixmap(logo_pixmap)
            left_layout.addWidget(logo_label)
            left_layout.addSpacing(15)  # Отступ после логотипа
        except Exception as e:
            print(f"[Ошибка] Логотип не загружен: {str(e)}")
            logo_label.setText("РАНХиГС\nМОСКВА")
            logo_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333333;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(logo_label)


        # Поиск
        search_group = QGroupBox("Поиск разделов")
        search_layout = QVBoxLayout(search_group)
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Введите название...")
        self.search_line.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_line)
        left_layout.addWidget(search_group)

        # Список разделов с прокруткой
        list_group = QGroupBox("Разделы меню")
        list_layout = QVBoxLayout(list_group)

        # Добавляем QScrollArea для списка
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget(scroll)
        scroll_layout = QVBoxLayout(scroll_content)
        self.section_list_widget = QListWidget()
        scroll_layout.addWidget(self.section_list_widget)
        scroll.setWidget(scroll_content)

        list_layout.addWidget(scroll)
        left_layout.addWidget(list_group)

        # Кнопки управления
        btn_group = QWidget()
        btn_layout = QHBoxLayout(btn_group)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.add_section_button = QPushButton("Добавить")
        self.delete_section_button = QPushButton("Удалить")
        self.delete_section_button.setEnabled(False)
        btn_layout.addWidget(self.add_section_button)
        btn_layout.addWidget(self.delete_section_button)
        left_layout.addWidget(btn_group)

        main_layout.addWidget(left_panel, stretch=1)  # Растягиваем левую панель

        # Правая панель
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Редактирование раздела
        edit_group = QGroupBox("Редактирование раздела")
        edit_layout = QFormLayout(edit_group)
        edit_layout.setVerticalSpacing(12)

        self.name_line = QLineEdit()
        self.name_line.setReadOnly(True)
        edit_layout.addRow("Название:", self.name_line)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setMinimumHeight(120)
        edit_layout.addRow("Текст:", self.text_edit)

        # Управление файлами
        file_group = QWidget()
        file_layout = QHBoxLayout(file_group)
        self.file_line = QLineEdit()
        self.file_line.setReadOnly(True)
        self.attach_file_button = QPushButton("Выбрать файл")
        self.remove_file_button = QPushButton("Очистить")
        self.remove_file_button.setEnabled(False)
        file_layout.addWidget(QLabel("Файл:"))
        file_layout.addWidget(self.file_line)
        file_layout.addWidget(self.attach_file_button)
        file_layout.addWidget(self.remove_file_button)
        edit_layout.addRow(file_group)

        right_layout.addWidget(edit_group)

        # Кнопки раздела
        buttons_group = QGroupBox("Управление кнопками")
        buttons_main_layout = QVBoxLayout(buttons_group)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Текст кнопки", "Целевой раздел"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)  # Отключаем линии сетки
        self.table.setMinimumHeight(150)
        self.table.setAlternatingRowColors(True)
        buttons_main_layout.addWidget(self.table)

        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Отключаем фокусную рамку
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)  # Редактирование по двойному клику
        self.table.setShowGrid(False)

        table_btn_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Добавить кнопку")
        self.delete_row_button = QPushButton("Удалить кнопку")
        table_btn_layout.addWidget(self.add_row_button)
        table_btn_layout.addWidget(self.delete_row_button)
        buttons_main_layout.addLayout(table_btn_layout)

        right_layout.addWidget(buttons_group)

        # Предпросмотр
        # Предпросмотр с прокруткой
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        # Создаем область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(QVBoxLayout())

        self.preview_title = QLabel()
        self.preview_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.preview_text = QLabel()
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("color: #444; margin: 8px 0;")
        self.preview_file = QLabel()
        self.preview_file.setStyleSheet("color: #666; font-style: italic;")

        self.preview_buttons = QWidget()
        self.preview_buttons_layout = QVBoxLayout(self.preview_buttons)
        self.preview_buttons_layout.setSpacing(6)

        scroll_content.layout().addWidget(self.preview_title)
        scroll_content.layout().addWidget(self.preview_text)
        scroll_content.layout().addWidget(self.preview_file)
        scroll_content.layout().addWidget(self.preview_buttons)
        scroll_content.layout().addStretch()

        scroll_area.setWidget(scroll_content)
        preview_layout.addWidget(scroll_area)

        right_layout.addWidget(preview_group)

        main_layout.addWidget(right_panel, stretch=2)

        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        open_action = QAction("Открыть...", self)
        save_action = QAction("Сохранить", self)
        exit_action = QAction("Выход", self)
        file_menu.addActions([open_action, save_action, exit_action])

        # Подключение сигналов
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        exit_action.triggered.connect(self.close)
        self.add_section_button.clicked.connect(self.on_add_section)
        self.delete_section_button.clicked.connect(self.on_delete_section)
        self.section_list_widget.currentItemChanged.connect(self.on_section_changed)
        self.attach_file_button.clicked.connect(self.on_attach_file)
        self.remove_file_button.clicked.connect(self.on_remove_file)
        self.add_row_button.clicked.connect(self.on_add_button_row)
        self.delete_row_button.clicked.connect(self.on_delete_button_row)
        self.text_edit.textChanged.connect(self.on_content_changed)
        self.table.itemChanged.connect(self.on_content_changed)

        self.section_list_widget.currentRowChanged.connect(self.update_delete_button_state)

    def get_section_by_name(self, name: str) -> OrderedDict | None:
        for section in self.menu_data:
            if section.get('name', '') == name:
                return section

    def on_search_text_changed(self, text):
        text = text.lower()
        self.section_list_widget.clear()
        for sec in self.menu_data:
            name = sec.get("name", "").lower()
            if text in name:
                self.section_list_widget.addItem(sec.get("name", ""))

    def on_delete_section(self):
        try:
            current_row = self.section_list_widget.currentRow()
            if current_row == -1 or current_row >= len(self.menu_data):
                QMessageBox.warning(self, "Ошибка", "Выберите раздел для удаления")
                return

            section = self.menu_data[current_row]
            confirm = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Удалить раздел '{section.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm == QMessageBox.StandardButton.Yes:
                del self.menu_data[current_row]
                self.section_list_widget.takeItem(current_row)

                # Сброс интерфейса
                self.current_section_index = None  # Исправлено
                self.name_line.clear()
                self.text_edit.clear()
                self.file_line.clear()
                self.table.setRowCount(0)
                self.preview_title.clear()
                self.preview_text.clear()
                self.preview_file.clear()

                self.dirty = True
                self.delete_section_button.setEnabled(self.section_list_widget.count() > 0)

                if self.section_list_widget.count() > 0:
                    new_index = max(0, min(current_row, self.section_list_widget.count() - 1))
                    self.section_list_widget.setCurrentRow(new_index)
                    self.load_section(new_index)
                else:
                    self.current_section_index = None  # Явный сброс

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

    def update_delete_button_state(self, index):
        enabled = index >= 0 and self.section_list_widget.count() > 0
        self.delete_section_button.setEnabled(enabled)

    def on_add_section(self):
        existing_names = [sec.get("name", "") for sec in self.menu_data]
        dialog = AddSectionDialog(existing_names, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, text, file_path, buttons = dialog.get_section_data()

            # Копируем файл в папку проекта, если он указан
            relative_file_path = None
            if file_path:
                try:
                    base_name = os.path.basename(file_path)
                    target_dir = os.path.join(os.path.dirname(__file__), "files")
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, base_name)
                    shutil.copy(file_path, target_path)
                    relative_file_path = os.path.relpath(target_path, os.path.dirname(__file__))
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось скопировать файл: {e}")
                    return

            # Создаем новый раздел
            new_sec = OrderedDict()
            new_sec["name"] = name
            new_sec["text"] = text
            if relative_file_path:
                new_sec["file"] = relative_file_path
            if buttons:
                new_sec["buttons"] = [{"text": t, "section": s} for t, s in buttons]

            self.menu_data.append(new_sec)
            self.section_list_widget.addItem(name)
            self.dirty = True

    def on_section_changed(self, menu_section: QListWidgetItem):
        if not menu_section.text():
            return

        # Название нажатой секции и название кнопки в нажатой секции
        section_name, section_button_text = re.findall(r'\[(.+)\]\s(.+)$', menu_section.text())[0]

        # Секция для редактирования
        section_to_edit = None

        # Ищем секцию, на которую видет section_button_text
        for section in self.menu_data:
            if section.get('name', '') != section_name:
                continue

            for group_button in section.get('keyboard', []):
                for button in group_button:
                    if button.get('text', '') != section_button_text:
                        continue

                    section_to_edit = self.get_section_by_name(button.get('callback_data', {}).get('section', ''))

        if section_to_edit is None:
            return

        # # Сохраняем предыдущий раздел
        # if self.current_section_index is not None and self.current_section_index != index:
        #     self.commit_current_section()
            
        # Загружаем новый раздел
        self.load_section(section_to_edit)
        # self.current_section_index = index

    def on_attach_file(self):
        if self.current_section_index is None:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", "All Files (*)")
        if file_path:
            self.file_line.setText(file_path)
            self.remove_file_button.setEnabled(True)
            self.dirty = True

    def on_remove_file(self):
        if self.current_section_index is None:
            return
        self.file_line.clear()
        self.remove_file_button.setEnabled(False)
        self.dirty = True

    def on_add_button_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item_text = QTableWidgetItem("")
        item_text.setFlags(item_text.flags() | Qt.ItemFlag.ItemIsEditable)
        item_section = QTableWidgetItem("")
        item_section.setFlags(item_section.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item_text)
        self.table.setItem(row, 1, item_section)
        self.dirty = True

    def on_delete_button_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.dirty = True

    def on_content_changed(self):
        if not self.is_loading:
            self.dirty = True

    def commit_current_section(self):
        if self.current_section_index is None:
            return
        sec = self.menu_data[self.current_section_index]
        # Сохраняем текст раздела
        new_text = self.text_edit.toPlainText()
        if sec.get("text", "") != new_text:
            sec["text"] = new_text
        # Сохраняем файл раздела
        current_file = self.file_line.text().strip()
        if current_file:
            sec["file"] = current_file
        else:
            if "file" in sec:
                del sec["file"]
        # Сохраняем клавиатуру раздела
        new_keyboard = []
        for row in range(self.table.rowCount()):
            item_text = self.table.item(row, 0)
            item_section = self.table.item(row, 1)
            if item_text and item_section:
                text_btn = item_text.text().strip()
                section_name = item_section.text().strip()
                if text_btn and section_name:
                    new_keyboard.append([{"text": text_btn, "callback_data": {"section": section_name}}])
        old_keyboard = sec.get("keyboard", [])
        if new_keyboard != old_keyboard:
            sec["keyboard"] = new_keyboard

    def load_section(self, section: OrderedDict):
        self.is_loading = True

        # Название раздела
        name = section.get("name", "")
        self.name_line.setText(name)

        # Текст раздела
        text = section.get("text", "")
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(text)
        self.text_edit.blockSignals(False)
        
        # # Файл раздела
        file_path = section.get("file", "")
        self.file_line.setText(file_path)
        self.remove_file_button.setEnabled(bool(file_path))

        # Клавиатура раздела
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for row_buttons in section.get("keyboard", []):
            for button in row_buttons:
                self.table.insertRow(self.table.rowCount())
                
                item_text = QTableWidgetItem(button.get("text", ""))
                item_text.setFlags(item_text.flags() | Qt.ItemFlag.ItemIsEditable)
                
                self.table.setItem(self.table.rowCount() - 1, 0, item_text)
                
                section_name = button.get("callback_data", {}).get('section', '')
                
                item_section = QTableWidgetItem(section_name)
                item_section.setFlags(item_section.flags() | Qt.ItemFlag.ItemIsEditable)

                self.table.setItem(self.table.rowCount() - 1, 1, item_section)

        self.table.blockSignals(False)
        
        self.is_loading = False

        # self.update_preview(name, text, file_path, keyboard)

    def update_preview(self, name, text, file_path, keyboard):
        self.preview_title.setText(f"<b>{name}</b>")
        self.preview_text.setText(text)

        if file_path:
            filename = os.path.basename(file_path)
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                self.preview_file.setText(f"[🖼️] Изображение: {filename}")
            elif filename.lower().endswith((".pdf", ".docx")):
                self.preview_file.setText(f"[📄] Документ: {filename}")
            else:
                self.preview_file.setText(f"[📎] Файл: {filename}")
        else:
            self.preview_file.setText("")

        # Кнопки
        for i in reversed(range(self.preview_buttons_layout.count())):
            self.preview_buttons_layout.itemAt(i).widget().setParent(None)

        for row in keyboard:
            for btn in row:
                b = QPushButton(btn["text"])
                b.setStyleSheet("""
                    QPushButton {
                        background-color: #EF7D05;
                        color: #FFFFFF;
                        border: 1px solid #E30617;
                        border-radius: 5px;
                        padding: 8px 16px;
                        margin: 3px;
                        font-family: "Arial";
                    }
                    QPushButton:hover {
                        background-color: #E30617;
                    }
                """)
                b.setEnabled(False)
                self.preview_buttons_layout.addWidget(b)

    def open_file(self):
        if self.dirty:
            ans = QMessageBox.question(self, "Внимание",
                                       "Имеются несохраненные изменения. Сохранить перед открытием другого файла?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if ans == QMessageBox.StandardButton.Cancel:
                return
            if ans == QMessageBox.StandardButton.Yes:
                if not self.save_file():
                    return
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть JSON-файл", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_pairs_hook=OrderedDict)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")
                return
            
            if not isinstance(data, list):
                QMessageBox.critical(self, "Ошибка", "Неверный формат файла (ожидается массив разделов).")
                return
            
            self.menu_data = data
            self.current_file_path = file_path
            self.section_list_widget.clear()
            
            for section in self.menu_data:
                for group_button in section.get('keyboard', []):
                    for button in group_button:
                        if 'text' in button:
                            if button["text"] not in ['Назад', 'В начало']:
                                self.section_list_widget.addItem(f'[{section["name"]}] {button["text"]}')
            
            if self.menu_data:
                self.section_list_widget.setCurrentRow(0)
            
            self.dirty = False

    def save_file(self):
        if not self.current_file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON-файл", "",
                                                       "JSON Files (*.json);;All Files (*)")
            if not file_path:
                return False
            self.current_file_path = file_path
        # Фиксируем данные текущего раздела
        if self.current_section_index is not None:
            self.commit_current_section()
        # Резервное копирование
        try:
            base, ext = os.path.splitext(self.current_file_path)
            backup_name = base + "_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ext
            shutil.copy2(self.current_file_path, backup_name)
        except Exception:
            pass
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.menu_data, f, ensure_ascii=False, indent=4)
            self.dirty = False
            QMessageBox.information(self, "Сохранено", "Файл успешно сохранен.")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
            return False

    def closeEvent(self, event: QCloseEvent):
        if self.dirty:
            ans = QMessageBox.question(self, "Внимание",
                                       "Имеются несохраненные изменения. Сохранить перед выходом?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if ans == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if ans == QMessageBox.StandardButton.Yes:
                if not self.save_file():
                    event.ignore()
                    return
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    
    window = MainWindow()
    window.show()

    app.exec()

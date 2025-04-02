import sys
import os
import io
import csv
import contextlib
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, QTextEdit
)
from PySide6.QtGui import QFont
from csv_processor import CSVProcessor


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Processor")

        self.input_path = None
        self.output_path = None
        self.pattern_path = os.path.join(os.path.dirname(__file__), "patterns.json")

        self.upload_btn = QPushButton("Загрузить CSV")
        self.save_btn = QPushButton("Выбрать путь сохранения")
        self.process_btn = QPushButton("Обработать")

        self.status_label = QLabel("Ожидание...")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 10))

        layout = QVBoxLayout()
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.process_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_output)
        self.setLayout(layout)

        self.upload_btn.clicked.connect(self.load_csv)
        self.save_btn.clicked.connect(self.choose_output_path)
        self.process_btn.clicked.connect(self.process_csv)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV", "", "CSV Files (*.csv)")
        if path:
            self.input_path = path
            self.status_label.setText(f"Загружено: {os.path.basename(path)}")

    def choose_output_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "", "CSV Files (*.csv)")
        if path:
            self.output_path = path
            self.status_label.setText(f"Сохраняем в: {path}")

    def process_csv(self):
        if not self.input_path or not self.output_path:
            self.status_label.setText("Выберите входной и выходной файл.")
            return

        try:
            processor = CSVProcessor(self.input_path, self.output_path, self.pattern_path)
            processor.process_data()
            self.status_label.setText("Успешно обработано!")
            
            
            self.log_output.setPlainText(processor.display_basic_statistics())


        except Exception as e:
            self.status_label.setText("Ошибка")
            self.log_output.setPlainText(str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())

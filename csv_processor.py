import pandas as pd
import re
import json
from bs4 import BeautifulSoup


class CSVProcessor:
    """
    A class for processing and analyzing technical requirement data from a CSV file.
    """

    def __init__(self, input_csv_path, output_csv_path, pattern_json_path):
        self.input_csv_path = input_csv_path
        self.output_csv_path = output_csv_path
        self.pattern_json_path = pattern_json_path
        
        self.base_cols = [
            "ID",
            "Содержание",
            "Дата ввода требования в действие",
            "Реестр НТД",
            "Требование безопасности",
            "ЮИН"
        ]

        self.extra_cols = [
            "Обрабатывается в ЦИМ",
            "Подлежит переводу в МПФ",
            "Передано подрядчику",
            "Комментарии",
            "Наличие ссылок на другие НД, в которых содержатся требования",
            "Наличие ссылок на Задание на проектирование",
            "Наличие ссылок на другие пункы этого СП",
            "Наличие формул",
            "Упоминание расчетов",
            "Наличие таблиц",
            "Наличие рисунков/диаграмм",
            "Требование носит рекомендательный характер"
        ]
        
        self.final_columns = self.base_cols + self.extra_cols
        
        self.df = self.load_csv()
        self.initialize_extra_columns()
        self.patterns = self.load_patterns()

    def load_csv(self):
        """Фиксит и загружает CSV, выбирает нужные столбцы."""
        df = pd.read_csv(
            self.input_csv_path,
            sep=";",
            encoding="utf-8",
        )
        available_cols = [col for col in self.base_cols if col in df.columns]
        missing = [col for col in self.base_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Отсутствуют столбцы: {missing}")
        return df[available_cols]

    def load_patterns(self):
        """Загружает регулярные выражения из JSON-файла."""
        with open(self.pattern_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def initialize_extra_columns(self):
        """Добавляет дополнительные столбцы в DataFrame."""
        for col in self.extra_cols:
            self.df[col] = 0
        self.df["Комментарии"] = ""

    def clean_html_and_quotes(self, text):
        """Удаляет HTML-теги и лишние кавычки из текста."""
        if not isinstance(text, str):
            return text
        text = BeautifulSoup(text, "html.parser").get_text()
        text = re.sub(r'"{2,}', '"', text)
        text = text.replace('\n', ' ').replace('\r', ' ')
        return text.strip()

    def has_pattern(self, text: str, pattern: str) -> bool:
        if not isinstance(text, str):
            return False
        return bool(re.search(pattern, text, flags=re.IGNORECASE))
    
    def get_pattern_text(self, text: str, pattern: str) -> list[str]:
        if not isinstance(text, str):
            return None
        match = re.findall(pattern, text, flags=re.IGNORECASE)
        return match if len(match) > 0 else None

    def check_conditions(self):
        for i, row in self.df.iterrows():
            content = self.clean_html_and_quotes(row["Содержание"])
            for category, pattern_list in self.patterns.items():
                for pattern in pattern_list:
                    match = self.get_pattern_text(content, pattern)
                    if match:
                        if category in self.df.columns:
                            self.df.at[i, category] = 1
                        if category == "Наличие таблиц":
                            self.df.at[i, "Комментарии"] += f"{category}\n"
                        elif category == "Упоминание расчетов":
                            self.df.at[i, "Комментарии"] += f"{category} {match} \n"
                            break
                        elif category == "Требование носит рекомендательный характер":
                            if "Неоднозначная формулировка" not in self.df.at[i, "Комментарии"]:
                                self.df.at[i, "Комментарии"] += f"Неоднозначная формулировка {match}\n"
                            else:
                                self.df.at[i, "Комментарии"] += f"{match}"
                        else:
                            self.df.at[i, "Комментарии"] += f"{category} {match}\n"

    def save_csv(self):
        """Сохраняет обновленный DataFrame в CSV."""
        self.df[self.final_columns].to_csv(self.output_csv_path, index=False, encoding="utf-8", sep=";")

    def process_data(self):
        """Основной метод обработки данных."""
        self.check_conditions()
        self.save_csv()


    def display_basic_statistics(self):
        result_output = "--- Basic Column Statistics ---\n"
        result_output += f"doc_path - { self.input_csv_path}\n"
        result_output += f"Total rows: {len(self.df)}\n\n"

        ignoring_cols = [
            "ID", "Содержание", "Дата ввода требования в действие",
            "Реестр НТД", "Требование безопасности", "ЮИН"
        ]
        total_flagged = 0
        flag_lines = []

        COL_WIDTH = 60
        VALUE_WIDTH = 10  

        for col in self.df.columns:
            if self.df[col].dtype in [int, float] and col not in ignoring_cols:
                flagged_count = self.df[col].sum()
                total_flagged += flagged_count
                flag_lines.append((col, flagged_count))

        for col, count in flag_lines:
            right_text = f"{count} flagged"
            result_output += f"{col.ljust(COL_WIDTH)} : {right_text.rjust(VALUE_WIDTH)}\n"

        result_output += "\n"
        result_output += f"{'Total flagged'.ljust(COL_WIDTH)} : {str(total_flagged).rjust(VALUE_WIDTH)}\n"
        empty_comments = self.df['Комментарии'].astype(str).str.strip().replace('', pd.NA).isna().sum()
        result_output += f"{'Rows with comments'.ljust(COL_WIDTH)} : {str(len(self.df)-empty_comments).rjust(VALUE_WIDTH)}\n"
        result_output += f"{'Rows with no comments'.ljust(COL_WIDTH)} : {str(empty_comments).rjust(VALUE_WIDTH)}"

        return result_output




import sys
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, \
    QTableWidgetItem, QDialog, QVBoxLayout, QLineEdit


class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                           (id INTEGER PRIMARY KEY, item TEXT, macroregion TEXT, region TEXT,
                           assignment_date TEXT, performer TEXT, status TEXT)''')
        self.conn.commit()


class DetailsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Details")
        self.setGeometry(parent.geometry())

        layout = QVBoxLayout()

        self.line_edits = []

        self.apply_button = QPushButton("Применить")
        self.apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def update(self, parent, row_id, details):
        self.row_id = row_id
        self.parent = parent

        layout = self.layout()
        for line_edit in self.line_edits:
            line_edit.deleteLater()

        self.line_edits = []

        for detail in details:
            line_edit = QLineEdit(detail)
            layout.addWidget(line_edit)
            self.line_edits.append(line_edit)

    def apply_changes(self):
        new_details = [line_edit.text() for line_edit in self.line_edits]
        self.parent.update_table_row(self.row_id, new_details)
        self.close()


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Task Table')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.button_layout = QHBoxLayout()

        self.in_progress_button = QPushButton("В работе")
        self.in_progress_button.clicked.connect(self.filter_in_progress)
        self.button_layout.addWidget(self.in_progress_button)

        self.waiting_button = QPushButton("Ожидание")
        self.waiting_button.clicked.connect(self.filter_waiting)
        self.button_layout.addWidget(self.waiting_button)

        self.completed_button = QPushButton("Выполнено")
        self.completed_button.clicked.connect(self.filter_completed)
        self.button_layout.addWidget(self.completed_button)

        layout.addLayout(self.button_layout)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(
            ['Item', 'Macroregion', 'Region', 'Assignment Date', 'Performer', 'Status'])
        layout.addWidget(self.table_widget)

        self.central_widget.setLayout(layout)

        self.db_manager = DatabaseManager('tasks_database.db')
        self.db_manager.create_table()

        self.details_dialog = None
        self.table_widget.doubleClicked.connect(self.show_details)

        self.populate_table(self.db_manager.cursor.execute("SELECT * FROM tasks").fetchall())

        self.table_widget.setColumnHidden(5, True)

    def populate_table(self, data):
        self.table_widget.setRowCount(0)  # Clear existing rows

        for row_number, row_data in enumerate(data):
            self.table_widget.insertRow(row_number)
            for column_number, column_data in enumerate(row_data[1:]):  # Skipping the 'id' column
                item = QTableWidgetItem(str(column_data))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the cell read-only
                self.table_widget.setItem(row_number, column_number, item)

    def update_table_row(self, row_id, new_details):
        for row_index in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row_index, 0)  # Assuming the first column is 'id'
            if item is not None and item.data(Qt.DisplayRole) == row_id:
                for col, detail in enumerate(new_details):
                    item = QTableWidgetItem(detail)
                    self.table_widget.setItem(row_index, col, item)  # +1 to skip the 'id' column
                break  # Stop after finding the row

    def filter_in_progress(self):
        self.db_manager.cursor.execute("SELECT * FROM tasks WHERE status = ?", ("В работе",))
        data = self.db_manager.cursor.fetchall()
        self.populate_table(data)

    def filter_waiting(self):
        self.db_manager.cursor.execute("SELECT * FROM tasks WHERE status = ?", ("Ожидание",))
        data = self.db_manager.cursor.fetchall()
        self.populate_table(data)

    def filter_completed(self):
        self.db_manager.cursor.execute("SELECT * FROM tasks WHERE status = ?", ("Выполнено",))
        data = self.db_manager.cursor.fetchall()
        self.populate_table(data)

    def show_details(self, index):
        row = index.row()
        row_id = self.table_widget.item(row, 0).data(Qt.DisplayRole)  # Get data as it is
        details = [self.table_widget.item(row, col).text() for col in range(self.table_widget.columnCount())]

        if self.details_dialog:
            self.details_dialog.close()

        self.details_dialog = DetailsDialog(self)
        self.details_dialog.update(self, row_id, details)
        self.details_dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())


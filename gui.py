import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog,
                             QTextEdit, QSpinBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Import your existing script functions
from contextforge import compile_project

class CompileThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, project_path, output_file, output_format, max_file_size):
        QThread.__init__(self)
        self.project_path = project_path
        self.output_file = output_file
        self.output_format = output_format
        self.max_file_size = max_file_size

    def run(self):
        try:
            # Redirect print statements to update_signal
            def custom_print(*args, **kwargs):
                self.update_signal.emit(' '.join(map(str, args)))

            # Replace the built-in print function with our custom one
            import builtins
            original_print = builtins.print
            builtins.print = custom_print

            self.update_signal.emit("Starting compile_project function...")
            compile_project(self.project_path, self.output_file, self.output_format, self.max_file_size)
            self.update_signal.emit("compile_project function completed.")
            self.finished_signal.emit(True, "Compilation completed successfully.")
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.update_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)
        finally:
            # Restore the original print function
            builtins.print = original_print

class ContextForgeGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ContextForge GUI')
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Project Path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('Project Path:'))
        self.path_input = QLineEdit()
        path_layout.addWidget(self.path_input)
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.browse_project)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)

        # Output File
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel('Output File:'))
        self.output_input = QLineEdit()
        output_layout.addWidget(self.output_input)
        output_browse_button = QPushButton('Browse')
        output_browse_button.clicked.connect(self.browse_output)
        output_layout.addWidget(output_browse_button)
        layout.addLayout(output_layout)

        # Full Path Display
        self.full_path_label = QLabel()
        layout.addWidget(self.full_path_label)

        # Output Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('Output Format:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['markdown', 'html', 'json', 'xml'])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # Max File Size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel('Max File Size (bytes):'))
        self.size_input = QSpinBox()
        self.size_input.setRange(1, 1000000000)
        self.size_input.setValue(1000000)
        size_layout.addWidget(self.size_input)
        layout.addLayout(size_layout)

        # Buttons
        button_layout = QHBoxLayout()
        compile_button = QPushButton('Compile Project')
        compile_button.clicked.connect(self.compile_project)
        button_layout.addWidget(compile_button)
        
        clear_button = QPushButton('Clear Output')
        clear_button.clicked.connect(self.clear_output)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)

        # Output Text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Connect signals
        self.path_input.textChanged.connect(self.update_full_path)
        self.output_input.textChanged.connect(self.update_full_path)

    def browse_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.path_input.setText(folder)

    def browse_output(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Output File")
        if file:
            self.output_input.setText(file)

    def update_full_path(self):
        project_path = self.path_input.text()
        output_file = self.output_input.text()
        if project_path and output_file:
            if not os.path.isabs(output_file):
                full_path = os.path.join(project_path, output_file)
            else:
                full_path = output_file
            self.full_path_label.setText(f'Full path: {full_path}')
        else:
            self.full_path_label.setText('')

    def compile_project(self):
        project_path = self.path_input.text()
        output_file = self.output_input.text()
        output_format = self.format_combo.currentText()
        max_file_size = self.size_input.value()

        if not project_path:
            QMessageBox.warning(self, "Error", "Please specify a project path.")
            return

        self.output_text.clear()
        self.output_text.append(f"Starting compilation...\n")
        self.output_text.append(f"Project Path: {project_path}\n")
        self.output_text.append(f"Output File: {output_file}\n")
        self.output_text.append(f"Output Format: {output_format}\n")
        self.output_text.append(f"Max File Size: {max_file_size} bytes\n")

        try:
            self.compile_thread = CompileThread(project_path, output_file, output_format, max_file_size)
            self.compile_thread.update_signal.connect(self.update_output)
            self.compile_thread.finished_signal.connect(self.compilation_finished)
            self.compile_thread.start()
            self.output_text.append("Compilation thread started.\n")
        except Exception as e:
            self.output_text.append(f"Error starting compilation thread: {str(e)}\n")
            QMessageBox.critical(self, "Error", f"Failed to start compilation: {str(e)}")

    def update_output(self, message):
        self.output_text.append(message)

    def compilation_finished(self, success, message):
        if success:
            self.output_text.append(message)
        else:
            self.output_text.append(f"Compilation failed: {message}")

    def clear_output(self):
        self.output_text.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ContextForgeGUI()
    ex.show()
    sys.exit(app.exec_())
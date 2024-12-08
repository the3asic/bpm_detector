import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QMessageBox, QFileDialog, QGridLayout,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QPushButton, QMenu
)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QCursor
import soundfile as sf
from .detector import BPMDetector, BPMAlgorithm
import re

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread"""
    progress = pyqtSignal(str, dict)  # Emits filename and results
    error = pyqtSignal(str, str)  # Emits filename and error message
    finished = pyqtSignal()

class BPMWorker(QRunnable):
    """Worker runnable for processing a single audio file"""
    def __init__(self, file_path, detector):
        super().__init__()
        self.file_path = file_path
        self.detector = detector
        self.signals = WorkerSignals()

    def run(self):
        try:
            audio_data, sample_rate = sf.read(self.file_path)
            results = self.detector.detect_all(audio_data, sample_rate)
            self.signals.progress.emit(
                os.path.basename(self.file_path),
                results  # Now passing the complete results dictionary
            )
        except Exception as e:
            self.signals.error.emit(os.path.basename(self.file_path), str(e))
        finally:
            self.signals.finished.emit()

class DropArea(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("\n\n Drop audio files here \n or click to select \n\n")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f8f8f8;
                padding: 10px;
                font-size: 16px;
            }
            QLabel:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            main_window = self.window()
            if isinstance(main_window, BPMDetectorGUI):
                main_window.process_files(files)

    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac);;All Files (*.*)"
        )
        if files:
            main_window = self.window()
            if isinstance(main_window, BPMDetectorGUI):
                main_window.process_files(files)

class BPMDetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.detector = BPMDetector(min_bpm=92, max_bpm=184)
        self.thread_pool = QThreadPool()
        self.active_workers = 0
        self.file_paths = {}  # Store original file paths
        self.selected_bpms = {}  # Store selected BPM for each file
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('BPM Detector')
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create drop area
        self.drop_area = DropArea(central_widget)
        layout.addWidget(self.drop_area)

        # BPM Range controls
        range_layout = QHBoxLayout()
        
        # Min BPM
        min_bpm_layout = QHBoxLayout()
        min_bpm_label = QLabel("Min BPM:")
        min_bpm_label.setStyleSheet("font-size: 14px;")
        self.min_bpm_spin = QSpinBox()
        self.min_bpm_spin.setRange(30, 300)
        self.min_bpm_spin.setValue(92)
        self.min_bpm_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
                font-size: 14px;
                width: 70px;
            }
        """)
        min_bpm_layout.addWidget(min_bpm_label)
        min_bpm_layout.addWidget(self.min_bpm_spin)
        range_layout.addLayout(min_bpm_layout)
        
        range_layout.addSpacing(20)
        
        # Max BPM
        max_bpm_layout = QHBoxLayout()
        max_bpm_label = QLabel("Max BPM:")
        max_bpm_label.setStyleSheet("font-size: 14px;")
        self.max_bpm_spin = QSpinBox()
        self.max_bpm_spin.setRange(30, 300)
        self.max_bpm_spin.setValue(184)
        self.max_bpm_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
                font-size: 14px;
                width: 70px;
            }
        """)
        max_bpm_layout.addWidget(max_bpm_label)
        max_bpm_layout.addWidget(self.max_bpm_spin)
        range_layout.addLayout(max_bpm_layout)
        
        # Thread count display
        self.thread_count_label = QLabel(f"Processing threads: {self.thread_pool.maxThreadCount()}")
        self.thread_count_label.setStyleSheet("font-size: 14px;")
        range_layout.addSpacing(40)
        range_layout.addWidget(self.thread_count_label)
        
        # Add confidence legend
        legend_layout = QHBoxLayout()
        legend_label = QLabel("Confidence:")
        legend_label.setStyleSheet("font-size: 14px;")
        legend_layout.addWidget(legend_label)
        
        confidence_levels = [
            ("≥60%", "#4CAF50", "#E8F5E9"),
            ("≥40%", "#FF9800", "#FFF3E0"),
            ("≥20%", "#FFC107", "#FFF8E1"),
            ("<20%", "#F44336", "#FFEBEE")
        ]
        
        for text, color, bg_color in confidence_levels:
            label = QLabel(text)
            label.setStyleSheet(f"""
                QLabel {{
                    padding: 2px 8px;
                    border-radius: 3px;
                    background-color: {bg_color};
                    color: {color};
                    font-weight: bold;
                    margin: 0 5px;
                }}
            """)
            legend_layout.addWidget(label)
        
        legend_layout.addStretch()
        range_layout.addSpacing(40)
        range_layout.addLayout(legend_layout)
        
        range_layout.addStretch()
        layout.addLayout(range_layout)

        # Add options layout
        options_layout = QHBoxLayout()
        
        # Round BPM checkbox
        self.round_bpm_checkbox = QCheckBox("Round BPM to Integer")
        self.round_bpm_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
            }
        """)
        self.round_bpm_checkbox.stateChanged.connect(self.on_round_bpm_changed)
        options_layout.addWidget(self.round_bpm_checkbox)
        
        # Add some spacing
        options_layout.addSpacing(20)
        
        # Rename files button
        self.rename_button = QPushButton("Rename Files with BPM")
        self.rename_button.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.rename_button.clicked.connect(self.rename_files)
        self.rename_button.setEnabled(False)
        options_layout.addWidget(self.rename_button)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(len(BPMAlgorithm) + 2)  # +2 for filename and selected BPM
        headers = ["File"] + [algo.value for algo in BPMAlgorithm] + ["Selected BPM"]
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        # Increase row height for multi-line content
        self.results_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.results_table)

        # Connect spinbox value changes
        self.min_bpm_spin.valueChanged.connect(self.update_bpm_range)
        self.max_bpm_spin.valueChanged.connect(self.update_bpm_range)

    def update_bpm_range(self):
        min_bpm = self.min_bpm_spin.value()
        max_bpm = self.max_bpm_spin.value()
        
        if min_bpm >= max_bpm:
            if self.sender() == self.min_bpm_spin:
                self.min_bpm_spin.setValue(max_bpm - 1)
            else:
                self.max_bpm_spin.setValue(min_bpm + 1)
            return
        
        self.detector = BPMDetector(min_bpm=min_bpm, max_bpm=max_bpm)

    def process_files(self, files):
        # Clear selected BPMs
        self.selected_bpms.clear()
        
        # Store original file paths
        self.file_paths.clear()
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(len(files))
        
        # Reset progress bar
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self.progress.show()
        
        # Reset active workers count
        self.active_workers = len(files)
        
        # Add filenames to the first column and initialize status
        for i, file_path in enumerate(files):
            filename = os.path.basename(file_path)
            self.file_paths[filename] = file_path  # Store original path
            
            # Add filename
            filename_item = QTableWidgetItem(filename)
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(i, 0, filename_item)
            
            # Add "Processing..." to other columns
            for j in range(1, self.results_table.columnCount() - 1):
                processing_item = QTableWidgetItem("Processing...")
                processing_item.setFlags(processing_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.results_table.setItem(i, j, processing_item)
            
            # Create and start worker for this file
            worker = BPMWorker(file_path, self.detector)
            worker.signals.progress.connect(self.update_results)
            worker.signals.error.connect(self.handle_error)
            worker.signals.finished.connect(self.worker_finished)
            
            # Start the worker
            self.thread_pool.start(worker)

    def handle_error(self, filename, error_msg):
        # Find the row for this file
        for row in range(self.results_table.rowCount()):
            if self.results_table.item(row, 0).text() == filename:
                # Update all algorithm columns with error message
                for col in range(1, self.results_table.columnCount()):
                    item = QTableWidgetItem("Error")
                    item.setToolTip(error_msg)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.results_table.setItem(row, col, item)
                break

    def worker_finished(self):
        self.active_workers -= 1
        self.progress.setValue(self.progress.maximum() - self.active_workers)
        
        if self.active_workers == 0:
            self.progress.hide()
            self.rename_button.setEnabled(True)

    def update_results(self, filename, results):
        # Find the row for this file
        for row in range(self.results_table.rowCount()):
            if self.results_table.item(row, 0).text() == filename:
                # Find the highest confidence result first
                best_bpm = None
                best_confidence = -1
                best_algo = None
                
                for algo, result in results.items():
                    if result and result.bpm > 0 and result.confidence > best_confidence:
                        best_confidence = result.confidence
                        best_bpm = result.bpm
                        best_algo = algo
                
                # Update results for each algorithm
                for col, algo in enumerate(BPMAlgorithm, start=1):
                    result = results.get(algo)
                    
                    if result and result.bpm > 0:
                        # Handle BPM rounding
                        bpm_value = result.bpm
                        if self.round_bpm_checkbox.isChecked():
                            bpm_value = round(bpm_value)
                            bpm_text = f"{bpm_value:.0f}"
                        else:
                            bpm_text = f"{bpm_value:.1f}"
                        
                        # Create cell text with BPM and confidence percentage
                        cell_text = f"{bpm_text} BPM\n{result.confidence:.1%}"
                        item = QTableWidgetItem(cell_text)
                        
                        # Store the actual BPM value in item data for later use
                        item.setData(Qt.ItemDataRole.UserRole, bpm_value)
                        
                        # Color coding based on confidence
                        if result.confidence >= 0.6:  # Above 60%
                            color = "#4CAF50"  # Green
                            bg_color = "#E8F5E9"  # Light green background
                        elif result.confidence >= 0.4:  # Above 40%
                            color = "#FF9800"  # Orange
                            bg_color = "#FFF3E0"  # Light orange background
                        elif result.confidence >= 0.2:  # Above 20%
                            color = "#FFC107"  # Amber
                            bg_color = "#FFF8E1"  # Light amber background
                        else:
                            color = "#F44336"  # Red
                            bg_color = "#FFEBEE"  # Light red background
                        
                        # Set cell style
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setBackground(QColor(bg_color))
                        item.setForeground(QColor(color))
                    else:
                        item = QTableWidgetItem("No result")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setForeground(QColor("#666666"))
                    
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.results_table.setItem(row, col, item)
                
                # Add "Select BPM" button in the last column and auto-select best result
                select_button = QPushButton("Select BPM")
                select_button.clicked.connect(lambda checked, r=row: self.select_bpm(r))
                
                # If we found a best result, auto-select it
                if best_bpm is not None:
                    self.selected_bpms[filename] = best_bpm
                    if self.round_bpm_checkbox.isChecked():
                        best_bpm = round(best_bpm)
                        bpm_text = f"{best_bpm:.0f}"
                    else:
                        bpm_text = f"{best_bpm:.1f}"
                    select_button.setText(f"Selected: {bpm_text} BPM ({best_algo.value})")
                    select_button.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            padding: 5px;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                
                self.results_table.setCellWidget(row, self.results_table.columnCount() - 1, select_button)
                break

    def select_bpm(self, row):
        filename = self.results_table.item(row, 0).text()
        menu = QMenu(self)
        
        # Add options for each algorithm's result
        for col, algo in enumerate(BPMAlgorithm, start=1):
            item = self.results_table.item(row, col)
            if item and "BPM" in item.text():
                bpm_value = item.data(Qt.ItemDataRole.UserRole)
                action = menu.addAction(f"{algo.value}: {bpm_value:.1f} BPM")
                action.setData((filename, bpm_value))
        
        # Show menu and handle selection
        action = menu.exec(QCursor.pos())
        if action:
            filename, bpm = action.data()
            self.selected_bpms[filename] = bpm
            
            # Update the button text to show selected BPM
            button = self.results_table.cellWidget(row, self.results_table.columnCount() - 1)
            button.setText(f"Selected: {bpm:.1f} BPM")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

    def rename_files(self):
        try:
            for row in range(self.results_table.rowCount()):
                filename = self.results_table.item(row, 0).text()
                original_path = self.file_paths.get(filename)
                if not original_path:
                    continue

                # Use selected BPM if available, otherwise use highest confidence result
                selected_bpm = self.selected_bpms.get(filename)
                if selected_bpm is not None:
                    best_bpm = selected_bpm
                else:
                    # Existing logic to find highest confidence BPM
                    best_bpm = None
                    best_confidence = -1
                    
                    for col, algo in enumerate(BPMAlgorithm, start=1):
                        cell_item = self.results_table.item(row, col)
                        if cell_item and "BPM" in cell_item.text():
                            try:
                                bpm = cell_item.data(Qt.ItemDataRole.UserRole)
                                confidence = float(cell_item.text().split('\n')[1].rstrip('%')) / 100
                                
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_bpm = bpm
                            except (ValueError, IndexError):
                                continue

                if best_bpm is not None:
                    # Round BPM if checkbox is checked
                    if self.round_bpm_checkbox.isChecked():
                        best_bpm = round(best_bpm)
                        bpm_text = f"{best_bpm:.0f}"
                    else:
                        bpm_text = f"{best_bpm:.1f}"
                    
                    # Create new filename with BPM
                    dir_path = os.path.dirname(original_path)
                    file_ext = os.path.splitext(filename)[1]
                    base_name = os.path.splitext(filename)[0]
                    
                    # Remove existing BPM if present
                    base_name = re.sub(r'[\[\(]?\d+\s*BPM[\]\)]?\s*', '', base_name)
                    base_name = re.sub(r'\d+\s*BPM\s*', '', base_name)
                    base_name = base_name.strip()
                    
                    new_name = f"{base_name} [{bpm_text}BPM]{file_ext}"
                    new_path = os.path.join(dir_path, new_name)
                    
                    # Rename the file
                    os.rename(original_path, new_path)
                    
                    # Update the table and stored path
                    self.file_paths[new_name] = new_path
                    self.results_table.item(row, 0).setText(new_name)

            QMessageBox.information(self, "Success", "Files have been renamed successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error renaming files: {str(e)}")

    def on_round_bpm_changed(self):
        """Update all displayed BPM values when rounding option changes"""
        for row in range(self.results_table.rowCount()):
            for col, algo in enumerate(BPMAlgorithm, start=1):
                item = self.results_table.item(row, col)
                if item and "BPM" in item.text():
                    # Get the stored BPM value
                    bpm_value = item.data(Qt.ItemDataRole.UserRole)
                    if bpm_value is not None:
                        # Format BPM based on checkbox state
                        if self.round_bpm_checkbox.isChecked():
                            bpm_value = round(bpm_value)
                            bpm_text = f"{bpm_value:.0f}"
                        else:
                            bpm_text = f"{bpm_value:.1f}"
                        
                        # Get the confidence from existing text
                        confidence = float(item.text().split('\n')[1].rstrip('%')) / 100
                        
                        # Update the display
                        cell_text = f"{bpm_text} BPM\n{confidence:.1%}"
                        item.setText(cell_text)
            
            # Update selected BPM button if exists
            button = self.results_table.cellWidget(row, self.results_table.columnCount() - 1)
            if isinstance(button, QPushButton) and "Selected:" in button.text():
                # Extract just the BPM value from the button text
                # Button text format: "Selected: 140.1 BPM (algorithm)"
                try:
                    bpm_text = button.text().split(': ')[1]  # Get everything after "Selected: "
                    bpm_text = bpm_text.split(' BPM')[0]     # Get just the number before " BPM"
                    bpm_value = float(bpm_text)
                    algo_name = button.text().split('(')[1].rstrip(')')  # Get algorithm name
                    
                    if self.round_bpm_checkbox.isChecked():
                        bpm_value = round(bpm_value)
                        button.setText(f"Selected: {bpm_value:.0f} BPM ({algo_name})")
                    else:
                        button.setText(f"Selected: {bpm_value:.1f} BPM ({algo_name})")
                except (ValueError, IndexError):
                    continue

def main():
    app = QApplication(sys.argv)
    window = BPMDetectorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from krita import *
from .settings import SettingsManager
from .providers import ProviderManager
from .presets import PresetManager
from .generator import ImageGenerator
from .generator import ImageGenerator
import threading
import os
from datetime import datetime


class GenerationWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        generator,
        prompt,
        provider,
        resolution,
        aspect_ratio,
        debug_mode,
        input_image_path=None,
    ):
        super().__init__()
        self.generator = generator
        self.prompt = prompt
        self.provider = provider
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.debug_mode = debug_mode
        self.input_image_path = input_image_path

    def run(self):
        success, result = self.generator.generate_image(
            self.prompt,
            self.provider,
            self.resolution,
            self.aspect_ratio,
            debug_mode=self.debug_mode,
            input_image_path=self.input_image_path,
        )
        self.finished.emit(success, result)


class BananaDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍌Krita Banana")

        # Managers
        self.settings_manager = SettingsManager()
        self.provider_manager = ProviderManager()
        self.preset_manager = PresetManager()
        self.image_generator = ImageGenerator(self.provider_manager)

        # Main Widget
        mainWidget = QWidget(self)
        self.setWidget(mainWidget)

        # Main Layout
        mainLayout = QVBoxLayout()
        mainWidget.setLayout(mainLayout)

        # Tabs
        self.tabs = QTabWidget()
        mainLayout.addWidget(self.tabs)

        # Generate Tab
        self.generate_tab = QWidget()
        self.setup_generate_tab()
        self.tabs.addTab(self.generate_tab, "Generate")

        # Settings Tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")

        # Utilities Tab
        self.utilities_tab = QWidget()
        self.setup_utilities_tab()
        self.tabs.addTab(self.utilities_tab, "Utilities")

    def setup_generate_tab(self):
        layout = QVBoxLayout()
        self.generate_tab.setLayout(layout)

        # Prompt Presets Area
        presets_layout = QHBoxLayout()
        presets_label = QLabel("Presets:")
        self.presets_combo = QComboBox()
        self.refresh_presets_combo()
        self.presets_combo.currentIndexChanged.connect(self.load_preset_prompt)

        presets_layout.addWidget(presets_label)
        presets_layout.addWidget(self.presets_combo, 1)  # Stretch factor 1
        layout.addLayout(presets_layout)

        # Preset Actions
        preset_actions_layout = QHBoxLayout()
        self.btn_preset_add = QPushButton("+")
        self.btn_preset_save = QPushButton("Save")
        self.btn_preset_rename = QPushButton("Rename")
        self.btn_preset_del = QPushButton("Del")

        self.btn_preset_add.clicked.connect(self.add_preset)
        self.btn_preset_save.clicked.connect(self.save_preset)
        self.btn_preset_rename.clicked.connect(self.rename_preset)
        self.btn_preset_del.clicked.connect(self.delete_preset)

        preset_actions_layout.addWidget(self.btn_preset_add)
        preset_actions_layout.addWidget(self.btn_preset_save)
        preset_actions_layout.addWidget(self.btn_preset_rename)
        preset_actions_layout.addWidget(self.btn_preset_del)
        layout.addLayout(preset_actions_layout)

        preset_actions_layout.addWidget(self.btn_preset_del)
        layout.addLayout(preset_actions_layout)

        # Prompt Input
        prompt_label = QLabel("Prompt:")
        layout.addWidget(prompt_label)
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "Enter your image generation prompt here..."
        )
        layout.addWidget(self.prompt_input)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Text to Image", "Image Edit"])
        self.mode_combo.setCurrentText("Image Edit")
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_layout)

        # Resolution Selector
        res_layout = QHBoxLayout()
        res_label = QLabel("Resolution:")
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1K", "2K", "4K"])
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_combo)
        layout.addLayout(res_layout)

        # Generate Button
        self.btn_generate = QPushButton("Generate Image")
        self.btn_generate.clicked.connect(self.start_generation)
        layout.addWidget(self.btn_generate)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Test Import Button (Temporary)
        self.btn_test_import = QPushButton("Test Import")
        self.btn_test_import.clicked.connect(self.test_import_image)
        self.btn_test_import.setVisible(False)
        layout.addWidget(self.btn_test_import)

    def refresh_presets_combo(self):
        current = self.presets_combo.currentText()
        self.presets_combo.blockSignals(True)
        self.presets_combo.clear()
        names = self.preset_manager.get_all_names()
        self.presets_combo.addItems(names)

        if current in names:
            self.presets_combo.setCurrentText(current)

        self.presets_combo.blockSignals(False)

    def load_preset_prompt(self):
        name = self.presets_combo.currentText()
        if not name:
            return
        prompt = self.preset_manager.get_prompt(name)
        self.prompt_input.setText(prompt)

    def add_preset(self):
        name, ok = QInputDialog.getText(self, "New Preset", "Enter preset name:")
        if ok and name:
            prompt = self.prompt_input.toPlainText()
            success, msg = self.preset_manager.add_preset(name, prompt)
            if success:
                self.refresh_presets_combo()
                self.presets_combo.setCurrentText(name)
            else:
                QMessageBox.warning(self, "Error", msg)

    def save_preset(self):
        name = self.presets_combo.currentText()
        if not name:
            return
        prompt = self.prompt_input.toPlainText()
        success, msg = self.preset_manager.update_preset(name, prompt)
        QMessageBox.information(self, "Info", msg)

    def rename_preset(self):
        old_name = self.presets_combo.currentText()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename Preset", "Enter new name:", text=old_name
        )
        if ok and new_name:
            success, msg = self.preset_manager.rename_preset(old_name, new_name)
            if success:
                self.refresh_presets_combo()
                self.presets_combo.setCurrentText(new_name)
            else:
                QMessageBox.warning(self, "Error", msg)

    def delete_preset(self):
        name = self.presets_combo.currentText()
        if not name:
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete preset '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            success, msg = self.preset_manager.delete_preset(name)
            if success:
                self.refresh_presets_combo()
                self.prompt_input.clear()

    def get_aspect_ratio(self):
        doc = Krita.instance().activeDocument()
        if not doc:
            return "1:1"

        width = doc.width()
        height = doc.height()

        # Calculate ratio
        ratio = width / height

        # Standard ratios
        ratios = {
            "1:1": 1.0,
            "2:3": 2 / 3,
            "3:2": 3 / 2,
            "3:4": 3 / 4,
            "4:3": 4 / 3,
            "4:5": 4 / 5,
            "5:4": 5 / 4,
            "9:16": 9 / 16,
            "16:9": 16 / 9,
            "21:9": 21 / 9,
        }

        # Find closest
        closest_ratio = "1:1"
        min_diff = float("inf")

        for r_name, r_val in ratios.items():
            diff = abs(ratio - r_val)
            if diff < min_diff:
                min_diff = diff
                closest_ratio = r_name

        return closest_ratio

    def import_image_to_krita(self, file_path):
        doc = Krita.instance().activeDocument()
        if not doc:
            return

        # Find next available name
        root = doc.rootNode()
        childNodes = root.childNodes()
        existing_indices = []
        for node in childNodes:
            name = node.name()
            if name.startswith("BananaImage"):
                try:
                    idx = int(name.replace("BananaImage", ""))
                    existing_indices.append(idx)
                except ValueError:
                    pass

        next_idx = 0
        if existing_indices:
            next_idx = max(existing_indices) + 1

        layer_name = f"BananaImage{next_idx:02d}"

        try:
            # Load image using QImage
            img = QImage(file_path)
            if img.isNull():
                print(f"Failed to load image: {file_path}")
                return

            # Resize to canvas size
            doc_width = doc.width()
            doc_height = doc.height()
            img = img.scaled(
                doc_width, doc_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )

            # Convert to ARGB32 (Krita usually expects BGRA on Windows/Little Endian)
            img = img.convertToFormat(QImage.Format_ARGB32)

            # Get raw data
            ptr = img.bits()
            ptr.setsize(img.byteCount())
            data = ptr.asstring()

            # Create paint layer
            layer = doc.createNode(layer_name, "paintlayer")
            layer.setPixelData(data, 0, 0, doc_width, doc_height)

            root.addChildNode(layer, None)
            doc.refreshProjection()
            return

        except Exception as e:
            print(f"Failed to create layer: {e}")

    def capture_canvas_image(self, max_size, quality):
        doc = Krita.instance().activeDocument()
        if not doc:
            return None

        try:
            # Get flattened image using thumbnail method which returns QImage
            # This handles color space conversion automatically
            width = doc.width()
            height = doc.height()
            img = doc.thumbnail(width, height)

            # Resize if needed
            if width > max_size or height > max_size:
                img = img.scaled(
                    max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            # Save to temp file
            import tempfile

            temp_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Krita_Banana", "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"canvas_capture_{timestamp}.webp"
            file_path = os.path.join(temp_dir, filename)

            # Save
            img.save(file_path, "WEBP", quality)
            return file_path

        except Exception as e:
            print(f"Error capturing canvas: {e}")
            return None

    def start_generation(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt.")
            return

        provider_name = self.provider_combo.currentText()
        if not provider_name:
            QMessageBox.warning(self, "Error", "Please select a provider.")
            return

        resolution = self.res_combo.currentText()
        aspect_ratio = self.get_aspect_ratio()
        debug_mode = self.chk_debug.isChecked()
        mode = self.mode_combo.currentText()

        input_image_path = None
        if mode == "Image Edit":
            # Capture canvas
            max_size = self.settings_manager.get("input_max_size", 2048)
            quality = self.settings_manager.get("webp_quality", 80)

            self.status_label.setText("Capturing canvas...")
            QApplication.processEvents()

            input_image_path = self.capture_canvas_image(max_size, quality)
            if not input_image_path:
                QMessageBox.warning(self, "Error", "Failed to capture canvas image.")
                self.status_label.setText("Error")
                return

        self.btn_generate.setEnabled(False)
        self.status_label.setText(f"Generating ({resolution}, {aspect_ratio})...")

        self.worker = GenerationWorker(
            self.image_generator,
            prompt,
            provider_name,
            resolution,
            aspect_ratio,
            debug_mode,
            input_image_path,
        )
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()

    def test_import_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Import", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.import_image_to_krita(file_path)

    def on_generation_finished(self, success, result):
        self.btn_generate.setEnabled(True)
        if success:
            self.status_label.setText("Done!")
            # Import to Krita
            self.import_image_to_krita(result)
            QMessageBox.information(
                self, "Success", f"Image saved to:\n{result}\nAnd imported as layer."
            )
        else:
            self.status_label.setText("Error")
            QMessageBox.warning(self, "Error", f"Generation failed:\n{result}")

    def setup_utilities_tab(self):
        layout = QVBoxLayout()
        self.utilities_tab.setLayout(layout)

        # Canvas Tools Group
        canvas_group = QGroupBox("Canvas Tools")
        canvas_layout = QVBoxLayout()
        canvas_group.setLayout(canvas_layout)

        # Aspect Ratios Label
        ratios_label = QLabel("Nano Banana Pro Aspect Ratios:")
        canvas_layout.addWidget(ratios_label)

        ratios_list = QLabel("1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9")
        ratios_list.setWordWrap(True)
        canvas_layout.addWidget(ratios_list)

        # Smart Resize Button
        self.btn_smart_resize = QPushButton("Smart Resize Canvas")
        self.btn_smart_resize.clicked.connect(self.smart_resize_canvas)
        canvas_layout.addWidget(self.btn_smart_resize)

        layout.addWidget(canvas_group)
        layout.addStretch()

    def smart_resize_canvas(self):
        doc = Krita.instance().activeDocument()
        if not doc:
            QMessageBox.warning(self, "Error", "No active document.")
            return

        width = doc.width()
        height = doc.height()
        current_ratio = width / height

        # Supported Ratios (Ordered as requested)
        ratios = [
            ("1:1", 1.0),
            ("2:3", 2 / 3),
            ("3:2", 3 / 2),
            ("3:4", 3 / 4),
            ("4:3", 4 / 3),
            ("4:5", 4 / 5),
            ("5:4", 5 / 4),
            ("9:16", 9 / 16),
            ("16:9", 16 / 9),
            ("21:9", 21 / 9),
        ]

        # Find closest ratio
        best_ratio_name = "1:1"
        best_ratio_val = 1.0
        min_diff = float("inf")

        for name, val in ratios:
            diff = abs(current_ratio - val)
            if diff < min_diff:
                min_diff = diff
                best_ratio_name = name
                best_ratio_val = val

        # Calculate new dimensions
        # Logic: Keep long edge, adjust short edge
        new_width = width
        new_height = height

        if best_ratio_val >= 1:
            # Target is Landscape or Square
            if width >= height:
                # Current is Landscape/Square -> Keep Width (Long), Adjust Height
                new_width = width
                new_height = int(round(width / best_ratio_val))
            else:
                # Current is Portrait, Target is Landscape
                # Long edge is Height.
                # If we keep Height (Long), NewWidth = Height * TargetRatio
                new_height = height
                new_width = int(round(height * best_ratio_val))
        else:
            # Target is Portrait (Ratio < 1)
            if height >= width:
                # Current is Portrait/Square -> Keep Height (Long), Adjust Width
                new_height = height
                new_width = int(round(height * best_ratio_val))
            else:
                # Current is Landscape, Target is Portrait
                # Long edge is Width.
                # Keep Width. NewHeight = Width / TargetRatio
                new_width = width
                new_height = int(round(width / best_ratio_val))

        # Resize Canvas (Not Scale Image)
        try:
            doc.setWidth(new_width)
            doc.setHeight(new_height)
            # Center the content if possible?
            # Krita setWidth/setHeight might crop from top-left.
            # For now, we stick to basic resizing as requested.

            QMessageBox.information(
                self,
                "Success",
                f"Resized to {best_ratio_name} ({new_width}x{new_height})",
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to resize: {e}")

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)

        # Provider Selection
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        self.provider_combo = QComboBox()
        self.refresh_provider_combo()
        self.provider_combo.currentIndexChanged.connect(self.load_provider_details)

        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        # Provider Actions
        action_layout = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_save = QPushButton("Save")
        self.btn_del = QPushButton("Del")

        self.btn_add.clicked.connect(self.add_provider)
        self.btn_save.clicked.connect(self.save_provider)
        self.btn_del.clicked.connect(self.delete_provider)

        action_layout.addWidget(self.btn_add)
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_del)
        layout.addLayout(action_layout)

        # Test Connection
        self.btn_test = QPushButton("Test Connection")
        self.btn_test.clicked.connect(self.test_connection)
        layout.addWidget(self.btn_test)

        # Provider Details Form
        form_layout = QFormLayout()

        self.input_name = QLineEdit()
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.Password)
        self.input_base_url = QLineEdit()
        self.input_model = QLineEdit()

        form_layout.addRow("Name:", self.input_name)
        form_layout.addRow("API Key:", self.input_api_key)
        form_layout.addRow("Base URL:", self.input_base_url)
        form_layout.addRow("Model ID:", self.input_model)

        layout.addLayout(form_layout)

        # General Settings
        self.chk_debug = QCheckBox("Enable Debug Mode")
        self.chk_save_images = QCheckBox("Save Generated Images")

        # Load initial checkbox states
        self.chk_debug.setChecked(self.settings_manager.get("debug_mode", False))
        self.chk_save_images.setChecked(
            self.settings_manager.get("save_generated_images", False)
        )

        self.chk_debug.stateChanged.connect(
            lambda: self.settings_manager.set("debug_mode", self.chk_debug.isChecked())
        )
        self.chk_save_images.stateChanged.connect(
            lambda: self.settings_manager.set(
                "save_generated_images", self.chk_save_images.isChecked()
            )
        )

        # WebP Settings
        webp_layout = QHBoxLayout()

        self.input_webp_quality = QSpinBox()
        self.input_webp_quality.setRange(0, 100)
        self.input_webp_quality.setValue(self.settings_manager.get("webp_quality", 80))
        self.input_webp_quality.setPrefix("WebP Quality: ")

        self.input_max_size = QSpinBox()
        self.input_max_size.setRange(512, 4096)
        self.input_max_size.setValue(self.settings_manager.get("input_max_size", 2048))
        self.input_max_size.setPrefix("Max Size: ")
        self.input_max_size.setSingleStep(128)

        # Connect signals
        self.input_webp_quality.valueChanged.connect(
            lambda v: self.settings_manager.set("webp_quality", v)
        )
        self.input_max_size.valueChanged.connect(
            lambda v: self.settings_manager.set("input_max_size", v)
        )

        webp_layout.addWidget(self.input_webp_quality)
        webp_layout.addWidget(self.input_max_size)
        layout.addLayout(webp_layout)

        layout.addWidget(self.chk_debug)
        layout.addWidget(self.chk_save_images)

        layout.addStretch()

        # Initial Load
        current_provider = self.settings_manager.get("selected_provider")
        if current_provider:
            index = self.provider_combo.findText(current_provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

        # Trigger load details for the initially selected item
        self.load_provider_details()

    def refresh_provider_combo(self):
        current = self.provider_combo.currentText()
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        names = self.provider_manager.get_all_names()
        self.provider_combo.addItems(names)

        if current in names:
            self.provider_combo.setCurrentText(current)

        self.provider_combo.blockSignals(False)

    def load_provider_details(self):
        name = self.provider_combo.currentText()
        if not name:
            return

        provider = self.provider_manager.get_provider(name)
        if provider:
            self.input_name.setText(provider.get("name", ""))
            self.input_api_key.setText(provider.get("apiKey", ""))
            self.input_base_url.setText(provider.get("baseUrl", ""))
            self.input_model.setText(provider.get("model", ""))

            # Save selection
            self.settings_manager.set("selected_provider", name)

    def add_provider(self):
        # Clear fields for new entry
        self.input_name.clear()
        self.input_api_key.clear()
        self.input_base_url.clear()
        self.input_model.clear()
        self.input_name.setFocus()
        # Deselect combo to indicate new mode? Or just let user type name and hit save.
        # Better approach: Just clear fields. Saving with a new name will create it.

    def save_provider(self):
        name = self.input_name.text().strip()
        api_key = self.input_api_key.text().strip()
        base_url = self.input_base_url.text().strip()
        model = self.input_model.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Provider Name is required.")
            return

        # Check if updating existing or adding new
        existing = self.provider_manager.get_provider(name)

        if existing:
            # Update
            success, msg = self.provider_manager.update_provider(
                name, api_key, base_url, model
            )
        else:
            # Add new
            success, msg = self.provider_manager.add_provider(
                name, api_key, base_url, model
            )
            if success:
                self.refresh_provider_combo()
                self.provider_combo.setCurrentText(name)

        QMessageBox.information(self, "Info", msg)

    def delete_provider(self):
        name = self.provider_combo.currentText()
        if not name:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete provider '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            success, msg = self.provider_manager.delete_provider(name)
            if success:
                self.refresh_provider_combo()
                self.load_provider_details()
            QMessageBox.information(self, "Info", msg)

    def test_connection(self):
        # Use current values from inputs
        config = {
            "name": self.input_name.text().strip(),
            "apiKey": self.input_api_key.text().strip(),
            "baseUrl": self.input_base_url.text().strip(),
            "model": self.input_model.text().strip(),
        }

        self.btn_test.setText("Testing...")
        self.btn_test.setEnabled(False)
        QApplication.processEvents()  # Force UI update

        success, msg = self.provider_manager.test_connection(config)

        self.btn_test.setText("Test Connection")
        self.btn_test.setEnabled(True)

        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Failed", msg)

    def canvasChanged(self, canvas):
        pass

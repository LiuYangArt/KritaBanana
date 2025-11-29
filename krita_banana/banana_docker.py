from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from krita import *
from .settings import SettingsManager
from .providers import ProviderManager


class BananaDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krita Banana")

        # Managers
        self.settings_manager = SettingsManager()
        self.provider_manager = ProviderManager()

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

    def setup_generate_tab(self):
        layout = QVBoxLayout()
        self.generate_tab.setLayout(layout)

        # Placeholder for now
        self.testButton = QPushButton(
            "Test Generation (Placeholder)", self.generate_tab
        )
        layout.addWidget(self.testButton)
        layout.addStretch()

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

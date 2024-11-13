import sys
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTextEdit,
    QVBoxLayout,
    QLabel,
    QFileDialog,
    QPushButton,
)
from PyQt5.QtCore import Qt
from PIL import Image, ExifTags, PngImagePlugin


class ExifReader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Drag and Drop Image Metadata Reader")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)

        layout = QVBoxLayout()

        self.info_label = QLabel("Drag and drop an image file here", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # Optional: Add a button to open file dialog
        self.open_button = QPushButton("Open Image", self)
        self.open_button.clicked.connect(self.openFileDialog)
        layout.addWidget(self.open_button)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if the dragged files are images
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    if self.is_image_file(url.toLocalFile()):
                        event.accept()
                        return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if self.is_image_file(file_path):
                    self.display_metadata(file_path)
                    break  # Handle one file at a time

    def openFileDialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.tiff *.bmp *.gif)",
            options=options,
        )
        if file_path:
            self.display_metadata(file_path)

    def is_image_file(self, file_path):
        image_extensions = (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")
        return file_path.lower().endswith(image_extensions)

    def display_metadata(self, file_path):
        self.info_label.setText(f"Metadata for: {file_path}")
        try:
            image = Image.open(file_path)
            if image.format == "PNG":
                self.display_png_info(image)
            else:
                self.display_exif_info(image)
        except Exception as e:
            self.text_edit.setText(f"Error reading image data:\n{e}")

    def display_exif_info(self, image):
        exif_data = image._getexif()
        if not exif_data:
            self.text_edit.setText("No EXIF data found.")
            return

        exif = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif_data.items()}

        exif_text = ""
        for tag, value in exif.items():
            exif_text += f"{tag}: {value}\n"

        self.text_edit.setText(exif_text)

    def display_png_info(self, image):
        png_info = image.info  # Contains PNG metadata
        text_chunks = []
        for k, v in png_info.items():
            if isinstance(v, PngImagePlugin.PngInfo):
                # Handle nested PngInfo objects
                for t_k, t_v in v.items():
                    text_chunks.append(self.process_metadata_item(t_k, t_v))
            else:
                text_chunks.append(self.process_metadata_item(k, v))

        # Get basic image info from IHDR chunk
        ihdr_info = (
            f"Width: {image.width}\n"
            f"Height: {image.height}\n"
            f"Mode: {image.mode}\n"
            f"Format: {image.format}\n"
        )

        # Combine IHDR info with other chunks
        metadata_text = ihdr_info + "\n".join(text_chunks)
        self.text_edit.setText(metadata_text)

    def process_metadata_item(self, key, value):
        # Attempt to parse the value as JSON
        parsed_value = value
        is_json = False
        if isinstance(value, str):
            try:
                parsed_json = json.loads(value)
                parsed_value = json.dumps(parsed_json, indent=4)
                is_json = True
            except json.JSONDecodeError:
                # Value is not JSON, leave it as is
                pass

        if is_json:
            # Create a human-readable version
            human_readable = self.human_readable_json(parsed_json)
            return (
                f"{key} (JSON):\n{parsed_value}\n\nHuman-readable:\n{human_readable}\n"
            )
        else:
            return f"{key}: {value}"

    def human_readable_json(self, json_data, indent_level=0):
        lines = []
        indent = "    " * indent_level
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent}{key}:")
                    lines.append(self.human_readable_json(value, indent_level + 1))
                else:
                    lines.append(f"{indent}{key}: {value}")
        elif isinstance(json_data, list):
            for index, item in enumerate(json_data):
                lines.append(f"{indent}- Item {index + 1}:")
                lines.append(self.human_readable_json(item, indent_level + 1))
        else:
            lines.append(f"{indent}{json_data}")
        return "\n".join(lines)


def main():
    app = QApplication(sys.argv)
    exif_reader = ExifReader()
    exif_reader.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

from PySide6.QtWidgets import QGridLayout, QTextEdit


def clearLayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


class GridKernel(QGridLayout):
    def __init__(self, parent):
        super().__init__(parent)
        self.size = None
        self.parent = parent

    def build(self, kernel, size=3):
        self.size = size
        clearLayout(self)
        for i in range(size):
            for j in range(size):
                edit = QTextEdit(self.parent)
                edit.setText(str(kernel[i][j]))
                self.addWidget(edit, i, j, 1, 1)

    def getSize(self):
        return self.size, self.size

    def getKernel(self):
        kernel = list()
        for i in range(self.size):
            for j in range(self.size):
                item = self.itemAtPosition(i, j)
                kernel.append(int(item.widget().toPlainText()))
        return kernel

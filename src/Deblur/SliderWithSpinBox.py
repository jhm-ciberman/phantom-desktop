from PySide6 import QtCore, QtWidgets


class SliderWithSpinBox(QtWidgets.QWidget):
    """
    A simple horizontal slider with a label and a SpinBox.
    """

    valueChanged = QtCore.Signal(float)
    """Signaled when the slider value changes"""

    _sliderScale = 1000  # Maximum precision is 3 decimal places

    def __init__(self, orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._slider = QtWidgets.QSlider(orientation)
        self._slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._slider.setFixedHeight(20)
        self._slider.setContentsMargins(0, 0, 0, 0)
        self._slider.valueChanged.connect(self._onSliderValueChanged)

        self._titleLabel = QtWidgets.QLabel()
        self._titleLabel.setFixedHeight(20)
        self._titleLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._titleLabel.setContentsMargins(0, 0, 0, 0)

        self._valueSpinBox = QtWidgets.QDoubleSpinBox()
        self._valueSpinBox.setFixedHeight(20)
        self._valueSpinBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._valueSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self._valueSpinBox.setContentsMargins(0, 0, 0, 0)
        self._valueSpinBox.valueChanged.connect(self._onSpinBoxValueChanged)

        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottomLayout.addWidget(self._titleLabel)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self._valueSpinBox)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._slider)
        self._layout.addLayout(bottomLayout)
        self.setLayout(self._layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)

        self._labelText = ""
        self._valueFormat = "{:.0f}"
        self._scale = 1

    def setRange(self, minimum: float, maximum: float):
        self._slider.setRange(int(minimum * self._sliderScale), int(maximum * self._sliderScale))
        self._valueSpinBox.setRange(minimum, maximum)

    def minimum(self) -> float:
        return self._valueSpinBox.minimum()

    def maximum(self) -> float:
        return self._valueSpinBox.maximum()

    def setSingleStep(self, step: float):
        self._slider.setSingleStep(int(step * self._sliderScale))
        self._valueSpinBox.setSingleStep(step)

    def singleStep(self) -> float:
        return self._valueSpinBox.singleStep()

    def value(self) -> float:
        return self._valueSpinBox.value()

    def setValue(self, value: float):
        self._slider.setValue(int(value * self._sliderScale))
        self._valueSpinBox.setValue(value)

    def setLabelText(self, text: str):
        self._labelText = text
        self._titleLabel.setText(self._labelText)

    def labelText(self) -> str:
        return self._labelText

    @QtCore.Slot()
    def _onSliderValueChanged(self) -> None:
        value = self._slider.value() / self._sliderScale
        self._valueSpinBox.setValue(value)
        self.valueChanged.emit(value)

    @QtCore.Slot()
    def _onSpinBoxValueChanged(self) -> None:
        value = self._valueSpinBox.value()
        self._slider.setValue(int(value * self._sliderScale))
        self.valueChanged.emit(value)

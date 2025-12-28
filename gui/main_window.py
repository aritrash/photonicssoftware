# gui/main_window.py

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QGroupBox,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from photology_simulator.gratingdesign import design_grating
from photology_simulator.ternaryops import Trit
from photology_simulator.logicengine import (
    list_unary_functions,
    list_binary_functions,
    is_unary,
    eval_unary,
    eval_binary,
)
from photology_simulator.polarization_encoder import encode_trit
from photology_simulator.trichanneldetector import TripleChannelDetector
from photology_simulator.visualizationhelpers import (
    create_all_output_figures,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Photology Simulator")

        self.detector = TripleChannelDetector.default()

        tab_widget = QTabWidget()
        tab_widget.addTab(self._create_grating_tab(), "Grating")
        tab_widget.addTab(self._create_logic_tab(), "Logic")

        self.setCentralWidget(tab_widget)
        self.resize(1200, 700)

    # ---------- Grating tab ----------

    def _create_grating_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Inputs
        form_layout = QHBoxLayout()

        # Wavelength input
        self.lambda_spin = QDoubleSpinBox()
        self.lambda_spin.setRange(200.0, 5000.0)
        self.lambda_spin.setValue(1550.0)
        self.lambda_spin.setSuffix(" nm")

        # Material selection
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Si", "SiN"])

        design_button = QPushButton("Design grating")
        design_button.clicked.connect(self.on_design_grating_clicked)

        form_layout.addWidget(QLabel("Wavelength:"))
        form_layout.addWidget(self.lambda_spin)
        form_layout.addWidget(QLabel("Material:"))
        form_layout.addWidget(self.material_combo)
        form_layout.addWidget(design_button)
        form_layout.addStretch()

        layout.addLayout(form_layout)

        # Outputs
        self.period_label = QLabel("Period: -")
        self.slit_label = QLabel("Slit width: -")
        self.duty_label = QLabel("Duty cycle: -")

        layout.addWidget(self.period_label)
        layout.addWidget(self.slit_label)
        layout.addWidget(self.duty_label)
        layout.addStretch()

        return widget

    def on_design_grating_clicked(self):
        wavelength = float(self.lambda_spin.value())
        material = self.material_combo.currentText()

        design = design_grating(
            wavelength_nm=wavelength,
            material_name=material,  # type: ignore[arg-type]
            n_clad=1.44,
        )

        self.period_label.setText(f"Period: {design.period_nm:.1f} nm")
        self.slit_label.setText(f"Slit width: {design.slit_width_nm:.1f} nm")
        self.duty_label.setText(f"Duty cycle: {design.duty_cycle:.3f}")

    # ---------- Logic tab ----------

    def _create_logic_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Function selection
        func_layout = QHBoxLayout()
        self.func_combo = QComboBox()
        self.func_combo.addItems(list_unary_functions() + list_binary_functions())
        self.func_combo.currentTextChanged.connect(self.on_function_changed)

        self.physical_checkbox = QCheckBox("Physical (triple-channel) mode")
        self.physical_checkbox.setChecked(False)

        func_layout.addWidget(QLabel("Function:"))
        func_layout.addWidget(self.func_combo)
        func_layout.addWidget(self.physical_checkbox)
        func_layout.addStretch()

        layout.addLayout(func_layout)

        # Input trits
        input_group = QGroupBox("Inputs")
        input_layout = QHBoxLayout(input_group)

        self.input1_combo = QComboBox()
        self._populate_trit_combo(self.input1_combo)

        self.input2_combo = QComboBox()
        self._populate_trit_combo(self.input2_combo)

        input_layout.addWidget(QLabel("Input 1:"))
        input_layout.addWidget(self.input1_combo)
        input_layout.addWidget(QLabel("Input 2:"))
        input_layout.addWidget(self.input2_combo)

        layout.addWidget(input_group)

        # Run button and output label
        run_layout = QHBoxLayout()
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.on_run_clicked)

        self.output_label = QLabel("Output: -")

        run_layout.addWidget(run_button)
        run_layout.addWidget(self.output_label)
        run_layout.addStretch()

        layout.addLayout(run_layout)

        # Matplotlib canvases for the three visualizations
        plots_layout = QHBoxLayout()

        self.fig_angle = None
        self.fig_poincare = None
        self.fig_jones = None

        # Create empty figures and canvases
        import matplotlib.pyplot as plt

        self.fig_angle = plt.figure()
        self.canvas_angle = FigureCanvas(self.fig_angle)

        self.fig_poincare = plt.figure()
        self.canvas_poincare = FigureCanvas(self.fig_poincare)

        self.fig_jones = plt.figure()
        self.canvas_jones = FigureCanvas(self.fig_jones)

        plots_layout.addWidget(self.canvas_angle)
        plots_layout.addWidget(self.canvas_poincare)
        plots_layout.addWidget(self.canvas_jones)

        layout.addLayout(plots_layout)

        # Initialize visibility based on selected function
        self.on_function_changed(self.func_combo.currentText())

        return widget

    @staticmethod
    def _populate_trit_combo(combo: QComboBox):
        combo.clear()
        # Display label, store actual Trit value in userData
        combo.addItem("-1", Trit.MINUS)
        combo.addItem("0", Trit.ZERO)
        combo.addItem("+1", Trit.PLUS)

    def on_function_changed(self, name: str):
        # Show/hide second input depending on unary/binary
        from photology_simulator.logicengine import is_unary, is_binary

        if is_unary(name):
            self.input2_combo.setEnabled(False)
        elif is_binary(name):
            self.input2_combo.setEnabled(True)
        else:
            # Unknown, enable both just in case
            self.input2_combo.setEnabled(True)

    def _get_trit_from_combo(self, combo: QComboBox) -> Trit:
        data = combo.currentData()
        if isinstance(data, Trit):
            return data
        # Fallback: parse text
        text = combo.currentText().strip()
        value = int(text)
        return Trit.from_int(value)  # type: ignore[attr-defined]

    def on_run_clicked(self):
        name = self.func_combo.currentText()
        from photology_simulator.logicengine import (
            is_unary,
            eval_unary,
            eval_binary,
        )

        t1 = self._get_trit_from_combo(self.input1_combo)

        # Determine input to logic engine
        if is_unary(name):
            if self.physical_checkbox.isChecked():
                # Physical mode: encode trit -> polarization -> detect -> decoded trit
                state = encode_trit(t1)
                det_result = self.detector.detect_from_state(state)
                logical_input = det_result.decoded
            else:
                logical_input = t1

            out_trit = eval_unary(name, logical_input)

        else:
            # Binary op
            t2 = self._get_trit_from_combo(self.input2_combo)

            if self.physical_checkbox.isChecked():
                # For now, apply physical path to both inputs separately
                state1 = encode_trit(t1)
                state2 = encode_trit(t2)
                det1 = self.detector.detect_from_state(state1)
                det2 = self.detector.detect_from_state(state2)
                in1 = det1.decoded
                in2 = det2.decoded
            else:
                in1, in2 = t1, t2

            out_trit = eval_binary(name, in1, in2)

        # Encode output to polarization state
        out_state = encode_trit(out_trit)

        # Update textual output
        color_name = {
            Trit.MINUS: "red",
            Trit.ZERO: "blue",
            Trit.PLUS: "green",
        }[out_trit]
        self.output_label.setText(f"Output: {out_trit} ({color_name})")

        # Update Matplotlib figures
        self._update_plots(out_trit, out_state)

    def _update_plots(self, out_trit: Trit, out_state):
        import matplotlib.pyplot as plt
        from photology_simulator.visualizationhelpers import create_all_output_figures

        # Clear existing figures
        self.fig_angle.clf()
        self.fig_poincare.clf()
        self.fig_jones.clf()

        # Create new plots on the same figure objects
        # We can reuse the helper by passing figures, or simplest: regenerate
        fig_angle, fig_poincare, fig_jones = create_all_output_figures(
            out_trit, out_state
        )

        # Draw onto our existing canvases:
        # Replace the figure objects underlying the canvases
        self.canvas_angle.figure = fig_angle
        self.canvas_poincare.figure = fig_poincare
        self.canvas_jones.figure = fig_jones

        self.canvas_angle.draw()
        self.canvas_poincare.draw()
        self.canvas_jones.draw()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

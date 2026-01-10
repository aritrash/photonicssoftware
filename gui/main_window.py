# gui/main_window.py

from __future__ import annotations

import sys
import numpy as np
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

# NEW: import comparison utilities
from photology_simulator.comparison_results import (
    PhotonicTechParams,
    ElectronicTechParams,
    compare_function_delays,
    plot_delay_comparison,
    plot_TER_vs_angle_noise,
)

from photology_simulator.TrineDSL import run_source, Env
from PyQt6 import QtWidgets

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Trine PICSIM v1.0-beta.3")

        self.detector = TripleChannelDetector.default()

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_grating_tab(), "Grating")
        self.tab_widget.addTab(self._create_logic_tab(), "Logic")
        self.tab_widget.addTab(self._create_comparison_tab(), "Comparison")
        self.tab_widget.addTab(self._create_trinedsl_tab(), "Terminal")

        self.setCentralWidget(self.tab_widget)
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
        fig_angle, fig_poincare, fig_jones = create_all_output_figures(
            out_trit, out_state
        )

        # Draw onto our existing canvases:
        self.canvas_angle.figure = fig_angle
        self.canvas_poincare.figure = fig_poincare
        self.canvas_jones.figure = fig_jones

        self.canvas_angle.draw()
        self.canvas_poincare.draw()
        self.canvas_jones.draw()

    # ---------- Comparison tab (NEW) ----------

    def _create_comparison_tab(self) -> QWidget:
        """
        Comparative analysis tab: structural delay and TER estimation.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Top controls: function selection and wavelength range
        control_layout = QHBoxLayout()

        self.comp_func_combo = QComboBox()
        # Allow all logic functions plus HA/FA
        base_funcs = list_unary_functions() + list_binary_functions()
        extra_funcs = ["HA", "FA"]
        self.comp_func_combo.addItems(base_funcs + extra_funcs)

        self.comp_lambda_min = QDoubleSpinBox()
        self.comp_lambda_min.setRange(200.0, 5000.0)
        self.comp_lambda_min.setValue(1300.0)
        self.comp_lambda_min.setSuffix(" nm")

        self.comp_lambda_max = QDoubleSpinBox()
        self.comp_lambda_max.setRange(200.0, 5000.0)
        self.comp_lambda_max.setValue(1700.0)
        self.comp_lambda_max.setSuffix(" nm")

        # Angle noise σ (deg) for TER plot
        self.comp_noise_spin = QDoubleSpinBox()
        self.comp_noise_spin.setRange(0.0, 20.0)
        self.comp_noise_spin.setDecimals(2)
        self.comp_noise_spin.setValue(2.0)
        self.comp_noise_spin.setSuffix(" deg")

        run_comp_button = QPushButton("Run comparison")
        run_comp_button.clicked.connect(self.on_run_comparison_clicked)

        control_layout.addWidget(QLabel("Function:"))
        control_layout.addWidget(self.comp_func_combo)
        control_layout.addWidget(QLabel("λ min:"))
        control_layout.addWidget(self.comp_lambda_min)
        control_layout.addWidget(QLabel("λ max:"))
        control_layout.addWidget(self.comp_lambda_max)
        control_layout.addWidget(QLabel("Angle noise σ:"))
        control_layout.addWidget(self.comp_noise_spin)
        control_layout.addWidget(run_comp_button)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # Numeric delay results
        self.comp_pho_label = QLabel("Photonic delay: -")
        self.comp_elec_label = QLabel("Electronic delay: -")
        self.comp_ratio_label = QLabel("Delay ratio (pho/elec): -")

        layout.addWidget(self.comp_pho_label)
        layout.addWidget(self.comp_elec_label)
        layout.addWidget(self.comp_ratio_label)

        # Matplotlib canvases for comparison plots
        plots_layout = QHBoxLayout()

        import matplotlib.pyplot as plt

        self.fig_delay_comp = plt.figure()
        self.canvas_delay_comp = FigureCanvas(self.fig_delay_comp)

        self.fig_ter = plt.figure()
        self.canvas_ter = FigureCanvas(self.fig_ter)

        plots_layout.addWidget(self.canvas_delay_comp)
        plots_layout.addWidget(self.canvas_ter)

        layout.addLayout(plots_layout)
        layout.addStretch()

        return widget

    def on_run_comparison_clicked(self):
        """
        Slot for the 'Run comparison' button in the Comparison tab.
        """
        func_name = self.comp_func_combo.currentText()

        # Build technology parameter objects (later you can expose more controls)
        pho_params = PhotonicTechParams(
            wavelength_m=float(self.lambda_spin.value()) * 1e-9,
            # you can tweak pipeline_depth etc. here if desired
        )
        elec_params = ElectronicTechParams()

        # Numeric delays at the current central wavelength
        pho_delays, elec_delay = compare_function_delays(
            func_name, pho_params, elec_params
        )

        pho_total_ps = pho_delays["total"] * 1e12
        elec_total_ps = elec_delay * 1e12
        ratio = pho_total_ps / elec_total_ps if elec_total_ps > 0 else float("inf")

        self.comp_pho_label.setText(f"Photonic delay (total): {pho_total_ps:.2f} ps")
        self.comp_elec_label.setText(f"Electronic delay (total): {elec_total_ps:.2f} ps")
        self.comp_ratio_label.setText(f"Delay ratio (pho/elec): {ratio:.2f}")

        # Delay vs wavelength plot (structural model)
        lam_min = float(self.comp_lambda_min.value()) * 1e-9
        lam_max = float(self.comp_lambda_max.value()) * 1e-9
        lam_vec = np.linspace(lam_min, lam_max, 50)

        self.fig_delay_comp.clf()
        fig_delay = plot_delay_comparison(
            func_name, pho_params, elec_params, lam_vec
        )
        self.canvas_delay_comp.figure = fig_delay
        self.canvas_delay_comp.draw()

        # TER vs angle noise plot (threshold-crossing model)
        noise_sigma = float(self.comp_noise_spin.value())
        noise_list = np.linspace(0.0, max(0.1, noise_sigma * 2.0), 8)

        self.fig_ter.clf()
        fig_ter = plot_TER_vs_angle_noise(
            noise_std_deg_list=list(noise_list),
            decision_margin_deg=45.0,
            trials=3000,
        )
        self.canvas_ter.figure = fig_ter
        self.canvas_ter.draw()

        # ---------- TrineDSL "Terminal" tab ----------
    

    def _create_trinedsl_tab(self) -> QWidget:
        """
        Terminal-like tab for running TrineDSL code.
        Text editor on top, output screen at bottom.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Top: code editor (70% height)
        self.dsl_editor = QtWidgets.QPlainTextEdit(widget)
        self.dsl_editor.setPlaceholderText(
            "// TrineDSL example\n"
            "trit A, B, S, C;\n"
            "A = -1;\n"
            "B = +1;\n"
            "S = TSUM(A, B);\n"
            "C = TCARRY(A, B);\n"
        )
        editor_font = self.dsl_editor.font()
        editor_font.setFamily("Consolas")
        editor_font.setPointSize(10)
        self.dsl_editor.setFont(editor_font)

        # Button row
        button_layout = QHBoxLayout()
        self.dsl_run_button = QPushButton("Run", widget)
        self.dsl_run_button.clicked.connect(self.on_run_trinedsl)
        self.dsl_clear_button = QPushButton("Clear", widget)
        self.dsl_clear_button.clicked.connect(self.dsl_editor.clear)

        button_layout.addWidget(self.dsl_run_button)
        button_layout.addWidget(self.dsl_clear_button)
        button_layout.addStretch(1)

        # Bottom: output screen (30% height)
        self.dsl_output = QtWidgets.QPlainTextEdit(widget)
        self.dsl_output.setReadOnly(True)
        out_font = self.dsl_output.font()
        out_font.setFamily("Consolas")
        out_font.setPointSize(10)
        self.dsl_output.setFont(out_font)

        # Approximate 70/30 split via stretch factors
        layout.addWidget(self.dsl_editor, stretch=7)
        layout.addLayout(button_layout)
        layout.addWidget(self.dsl_output, stretch=3)

        return widget

    def on_run_trinedsl(self):
        """
        Execute TrineDSL code from the editor and show results or errors
        in the output pane.
        """
        src = self.dsl_editor.toPlainText()
        self.dsl_output.clear()

        try:
            env = run_source(src, env=None)
        except Exception as e:
            # Later replace str(e) with your formatted TrineDSL error message
            self.dsl_output.setPlainText(str(e))
            return

        # On success, show all variable values
        if not env.vars:
            self.dsl_output.setPlainText("(no variables declared)")
            return

        lines = [f"{name} = {value}" for name, value in env.vars.items()]
        self.dsl_output.setPlainText("\n".join(lines))




def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

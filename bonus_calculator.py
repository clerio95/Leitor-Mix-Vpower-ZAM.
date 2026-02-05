import copy
import datetime
import json
import locale
import os
import re
import sys

from PySide6 import QtCore, QtGui, QtWidgets

try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except Exception:
    pass


# =========================
# Helpers: caminhos (PyInstaller)
# =========================
def resource_path(relative_path: str) -> str:
    """
    Retorna o caminho absoluto para um recurso, funcionando em:
    - dev (rodando .py)
    - PyInstaller onefile/onedir
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def app_writable_dir() -> str:
    """
    Diretório gravável (onde fica o .exe ou o .py).
    No onefile, sys.executable aponta pro .exe.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))


# =========================
# Parsing do relatório
# =========================
def converter_numero_brasileiro(valor: str) -> float:
    """Converte número no formato brasileiro (1.234,567) para float."""
    if not valor or not valor.strip():
        return 0.0
    valor = valor.strip().replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0


def extrair_cabecalho(linhas):
    """Extrai informações do cabeçalho do relatório."""
    header = {}
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith("+") or linha.startswith("-"):
            continue

        match = re.search(r"Empresa:\s*(.+?)\s*\|\s*$", linha, re.IGNORECASE)
        if match:
            header["empresa"] = match.group(1).strip()

        match = re.search(r"Período:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["periodo"] = match.group(1).strip()

        match = re.search(r"Modo:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["modo"] = match.group(1).strip()

        match = re.search(r"Agrupar:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["agrupar"] = match.group(1).strip()

        match = re.search(r"Ordenar:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["ordenar"] = match.group(1).strip()

        match = re.search(r"Produtividade:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["produtividade"] = match.group(1).strip()

        match = re.search(r"Grupo empresa:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["grupo_empresa"] = match.group(1).strip()

        match = re.search(r"Grupo produto:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["grupo_produto"] = match.group(1).strip()

        match = re.search(r"Exibir:\s*(.+)", linha, re.IGNORECASE)
        if match:
            header["exibir"] = match.group(1).strip()

        if "Funcionário:" in linha and "Vendas:" in linha:
            break

    return header


def parsear_linha_item(linha):
    """Parseia uma linha de item da tabela de produtos."""
    if (
        not linha.strip()
        or linha.strip().startswith("+")
        or "Código" in linha
        or "Produto" in linha
    ):
        return None

    if not linha.strip().startswith("|") or not linha.strip().endswith("|"):
        return None

    if "Total do vendedor" in linha:
        return None

    campos = [campo.strip() for campo in linha.split("|")]
    campos = campos[1:-1]

    if len(campos) != 7:
        return None

    try:
        return {
            "codigo": int(campos[0]) if campos[0] else 0,
            "produto": campos[1],
            "fornecedor": campos[2],
            "quantidade": converter_numero_brasileiro(campos[3]),
            "unidade": campos[4],
            "valor": converter_numero_brasileiro(campos[5]),
            "percentual": converter_numero_brasileiro(campos[6]),
        }
    except (ValueError, IndexError):
        return None


def parsear_total_funcionario(linha):
    """Extrai informações do total do funcionário."""
    if "Total do vendedor e participação geral nas vendas" not in linha:
        return None

    campos = [campo.strip() for campo in linha.split("|")]
    campos = campos[1:-1]

    if len(campos) < 6:
        return None

    try:
        return {
            "quantidade": converter_numero_brasileiro(campos[2]),
            "valor": converter_numero_brasileiro(campos[4]),
            "percentual": converter_numero_brasileiro(campos[5]),
        }
    except (ValueError, IndexError):
        return None


def extrair_funcionarios(linhas):
    """Extrai todos os blocos de funcionários e seus itens vendidos."""
    funcionarios = []
    funcionario_atual = None
    itens_atual = []

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        match = re.search(r"Funcionário:\s*(\d+)\s*-\s*(.+?)\s+Vendas:\s*(\d+)", linha)
        if match:
            if funcionario_atual:
                funcionario_atual["itens"] = itens_atual
                funcionarios.append(funcionario_atual)

            codigo = int(match.group(1))
            nome = match.group(2).strip()
            vendas = int(match.group(3))

            funcionario_atual = {
                "codigo": codigo,
                "nome": nome,
                "vendas": vendas,
                "itens": [],
                "total": None,
            }
            itens_atual = []
            i += 1
            continue

        if funcionario_atual:
            item = parsear_linha_item(linha)
            if item:
                itens_atual.append(item)

            total = parsear_total_funcionario(linha)
            if total:
                funcionario_atual["total"] = total

        i += 1

    if funcionario_atual:
        funcionario_atual["itens"] = itens_atual
        funcionarios.append(funcionario_atual)

    return funcionarios


def extrair_totais_gerais(linhas):
    """Extrai totais gerais do relatório."""
    totais = {}

    for linha in linhas:
        if "Total geral de vendas no período" in linha:
            campos = [campo.strip() for campo in linha.split("|")]
            campos = campos[1:-1]

            if len(campos) >= 4:
                totais["quantidade"] = converter_numero_brasileiro(campos[1])
                totais["valor"] = converter_numero_brasileiro(campos[3])
            break

    if not totais:
        for linha in linhas:
            if "Total de vendas da empresa" in linha:
                campos = [campo.strip() for campo in linha.split("|")]
                campos = campos[1:-1]

                if len(campos) >= 4:
                    totais["quantidade"] = converter_numero_brasileiro(campos[2])
                    totais["valor"] = converter_numero_brasileiro(campos[3])
                break

    return totais


def parsear_relatorio(caminho_arquivo: str):
    """Função principal que parseia o arquivo de relatório completo."""
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        with open(caminho_arquivo, "r", encoding="latin1") as f:
            linhas = f.readlines()

    return {
        "header": extrair_cabecalho(linhas),
        "funcionarios": extrair_funcionarios(linhas),
        "totaisGerais": extrair_totais_gerais(linhas),
    }


# =========================
# Config padrão
# =========================
DEFAULT_CONFIG = {
    "bonus_rules": [
        {"min": 35, "max": 40, "winner": 0.01, "loser": 0.01},
        {"min": 40, "max": 45, "winner": 0.015, "loser": 0.015},
        {"min": 45, "max": 50, "winner": 0.02, "loser": 0.02},
        {"min": 50, "max": 100, "winner": 0.0225, "loser": 0.02},
    ],
    "mix_rule_type": "team",  # "team" ou "all_or_nothing"
    "mix_rules": {
        "all_or_nothing": {
            "min_mix": 40.0,
            "bonus_per_liter": 0.02,
        }
    },
    "employee_settings": {},  # {"123": {"team": "A", "stars": 0}}
    "search_history": [],
    "mix_history": {},
    "last_report_update": None,
    "last_directory": None,
}


# =========================
# UI: Dialogs
# =========================
class SettingsPasswordDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso às configurações")
        self.setModal(True)
        self.setFixedWidth(380)
        self.setStyleSheet(
            """
            QDialog { background: #FFFFFF; }
            QLabel { color: #1f2937; }
            """
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Configurações protegidas")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ED1C24;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        subtitle = QtWidgets.QLabel("Digite a senha para acessar as regras e times.")
        subtitle.setStyleSheet("font-size: 12px; color: #4b5563;")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px; font-size: 14px;
                border: 2px solid #FFD500; border-radius: 10px;
                color: #111827; background: #FFFFFF;
            }
            QLineEdit:focus { border-color: #ED1C24; }
            """
        )

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()

        cancel = QtWidgets.QPushButton("Cancelar")
        cancel.setStyleSheet(
            """
            QPushButton {
                background: #FFF4B5; color: #ED1C24;
                border: 1px solid #FFD500;
                font-size: 13px; padding: 8px 16px;
                border-radius: 10px;
            }
            QPushButton:hover { background: #FFE98B; }
            """
        )
        cancel.clicked.connect(self.reject)

        ok = QtWidgets.QPushButton("Acessar")
        ok.setStyleSheet(
            """
            QPushButton {
                background: #ED1C24; color: #FFFFFF;
                font-size: 13px; padding: 8px 16px;
                border-radius: 10px;
            }
            QPushButton:hover { background: #d81920; }
            """
        )
        ok.clicked.connect(self.accept)

        buttons.addWidget(cancel)
        buttons.addSpacing(10)
        buttons.addWidget(ok)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(4)
        layout.addWidget(self.password_input)
        layout.addSpacing(4)
        layout.addLayout(buttons)

        self.password_input.returnPressed.connect(self.accept)

    def password(self):
        return self.password_input.text().strip()


class SettingsDialog(QtWidgets.QDialog):
    TEAM_OPTIONS = [
        ("A", "Time A"),
        ("B", "Time B"),
        ("A_NIGHT", "Time A (Noturno)"),
        ("B_NIGHT", "Time B (Noturno)"),
        ("OIL", "Troca de Óleo"),
        ("INACTIVE", "Inativo"),
    ]

    def __init__(self, parent, config, employee_data):
        super().__init__(parent)
        self.setWindowTitle("Configurações - Regras e Times")
        self.setModal(True)
        self.resize(860, 590)
        self.setStyleSheet("background-color: #FFFFFF;")

        self.original_config = copy.deepcopy(config)
        self.employee_data = employee_data

        self.build_ui()
        self.populate_data()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        header = QtWidgets.QLabel("Configurações de Mix e Times")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #ED1C24;")
        header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {border: 1px solid #FFD500; border-radius: 12px; background: #FFFFFF;}
            QTabBar::tab {padding: 10px 16px; font-size: 13px; color: #374151; background: #FFF4B5; border-top-left-radius: 10px; border-top-right-radius: 10px;}
            QTabBar::tab:selected {background-color: #FFD500; color: #ED1C24; font-weight: 700;}
            """
        )

        self.rules_tab = QtWidgets.QWidget()
        self.teams_tab = QtWidgets.QWidget()
        self.stars_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.rules_tab, "Regras")
        self.tabs.addTab(self.teams_tab, "Times")
        self.tabs.addTab(self.stars_tab, "Estrelas")

        self.build_rules_tab()
        self.build_teams_tab()
        self.build_stars_tab()

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()

        cancel_button = QtWidgets.QPushButton("Cancelar")
        cancel_button.setStyleSheet(self.btn_secondary())

        save_button = QtWidgets.QPushButton("Salvar")
        save_button.setStyleSheet(self.btn_primary())
        save_button.clicked.connect(self.handle_save)
        cancel_button.clicked.connect(self.reject)

        button_row.addWidget(cancel_button)
        button_row.addSpacing(10)
        button_row.addWidget(save_button)

        layout.addWidget(header)
        layout.addWidget(self.tabs)
        layout.addLayout(button_row)

    def build_rules_tab(self):
        layout = QtWidgets.QVBoxLayout(self.rules_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Tipo de regra principal:")
        lbl.setStyleSheet("font-size: 12px; color: #374151;")

        self.rule_type_combo = QtWidgets.QComboBox()
        self.rule_type_combo.addItem("Por time (vencedor x perdedor)", "team")
        self.rule_type_combo.addItem("Tudo ou nada (mix individual)", "all_or_nothing")
        self.rule_type_combo.setStyleSheet(self.combo_style())

        row.addWidget(lbl)
        row.addSpacing(10)
        row.addWidget(self.rule_type_combo)
        row.addStretch()

        self.bonus_table = QtWidgets.QTableWidget()
        self.bonus_table.setColumnCount(4)
        self.bonus_table.setHorizontalHeaderLabels(
            [
                "Mix mínimo (%)",
                "Mix máximo (%)",
                "Bônus vencedor (R$/L)",
                "Bônus perdedor (R$/L)",
            ]
        )
        self.bonus_table.horizontalHeader().setStretchLastSection(True)
        self.bonus_table.verticalHeader().setVisible(False)
        self.bonus_table.setStyleSheet(
            """
            QTableWidget {border: 1px solid #FFD500; border-radius: 12px; color: #111827; gridline-color: #FFE98B;}
            QHeaderView::section {background-color: #FFF4B5; padding: 8px; font-weight: 700; color: #374151; border: none;}
            """
        )

        bonus_buttons = QtWidgets.QHBoxLayout()
        add_bonus = QtWidgets.QPushButton("Adicionar faixa")
        add_bonus.setStyleSheet(self.btn_secondary())
        add_bonus.clicked.connect(self.add_bonus_row)

        remove_bonus = QtWidgets.QPushButton("Remover faixa")
        remove_bonus.setStyleSheet(self.btn_danger())
        remove_bonus.clicked.connect(self.remove_bonus_row)

        bonus_buttons.addWidget(add_bonus)
        bonus_buttons.addSpacing(8)
        bonus_buttons.addWidget(remove_bonus)
        bonus_buttons.addStretch()

        all_or_nothing_group = QtWidgets.QGroupBox("Regra tudo ou nada")
        all_or_nothing_group.setStyleSheet(
            """
            QGroupBox {font-weight: 800; border: 1px solid #FFD500; border-radius: 12px; padding: 10px; color: #374151;}
            QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 6px;}
            """
        )
        all_layout = QtWidgets.QGridLayout(all_or_nothing_group)

        self.min_mix_spin = QtWidgets.QDoubleSpinBox()
        self.min_mix_spin.setRange(0, 100)
        self.min_mix_spin.setSuffix(" %")
        self.min_mix_spin.setDecimals(2)
        self.min_mix_spin.setStyleSheet(self.spinbox_style())

        self.all_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.all_bonus_spin.setRange(0, 10)
        self.all_bonus_spin.setDecimals(4)
        self.all_bonus_spin.setStyleSheet(self.spinbox_style())

        all_layout.addWidget(QtWidgets.QLabel("Mix mínimo:"), 0, 0)
        all_layout.addWidget(self.min_mix_spin, 0, 1)
        all_layout.addWidget(QtWidgets.QLabel("Bônus por litro:"), 1, 0)
        all_layout.addWidget(self.all_bonus_spin, 1, 1)

        layout.addLayout(row)
        layout.addWidget(QtWidgets.QLabel("Faixas de bonificação (regra por time):"))
        layout.addWidget(self.bonus_table)
        layout.addLayout(bonus_buttons)
        layout.addWidget(all_or_nothing_group)
        layout.addStretch()

    def build_teams_tab(self):
        layout = QtWidgets.QVBoxLayout(self.teams_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info = QtWidgets.QLabel(
            "Defina o time de cada funcionário para o cálculo do mix."
        )
        info.setStyleSheet("font-size: 12px; color: #374151;")

        self.team_table = QtWidgets.QTableWidget()
        self.team_table.setColumnCount(2)
        self.team_table.setHorizontalHeaderLabels(["Funcionário", "Time"])
        self.team_table.horizontalHeader().setStretchLastSection(True)
        self.team_table.verticalHeader().setVisible(False)
        self.team_table.setStyleSheet(
            """
            QTableWidget {border: 1px solid #FFD500; border-radius: 12px; color: #111827;}
            QHeaderView::section {background-color: #FFF4B5; padding: 8px; font-weight: 700; color: #374151; border: none;}
            """
        )

        layout.addWidget(info)
        layout.addWidget(self.team_table)
        layout.addStretch()

    def build_stars_tab(self):
        layout = QtWidgets.QVBoxLayout(self.stars_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info = QtWidgets.QLabel("Defina a pontuação em estrelas (1 estrela = 1 ponto).")
        info.setStyleSheet("font-size: 12px; color: #374151;")

        self.stars_table = QtWidgets.QTableWidget()
        self.stars_table.setColumnCount(2)
        self.stars_table.setHorizontalHeaderLabels(["Funcionário", "Estrelas"])
        self.stars_table.horizontalHeader().setStretchLastSection(True)
        self.stars_table.verticalHeader().setVisible(False)
        self.stars_table.setStyleSheet(
            """
            QTableWidget {border: 1px solid #FFD500; border-radius: 12px; color: #111827;}
            QHeaderView::section {background-color: #FFF4B5; padding: 8px; font-weight: 700; color: #374151; border: none;}
            """
        )

        layout.addWidget(info)
        layout.addWidget(self.stars_table)
        layout.addStretch()

    def populate_data(self):
        bonus_rules = self.original_config.get("bonus_rules", [])
        self.bonus_table.setRowCount(len(bonus_rules))
        for row, rule in enumerate(bonus_rules):
            self.set_bonus_row(
                row,
                rule.get("min", 0.0),
                rule.get("max", 0.0),
                rule.get("winner", 0.0),
                rule.get("loser", 0.0),
            )

        mix_rule_type = self.original_config.get("mix_rule_type", "team")
        index = self.rule_type_combo.findData(mix_rule_type)
        if index >= 0:
            self.rule_type_combo.setCurrentIndex(index)

        mix_rules = self.original_config.get("mix_rules", {})
        all_or_nothing = mix_rules.get("all_or_nothing", {})
        self.min_mix_spin.setValue(all_or_nothing.get("min_mix", 40.0))
        self.all_bonus_spin.setValue(all_or_nothing.get("bonus_per_liter", 0.02))

        employee_settings = self.original_config.get("employee_settings", {})
        employees = sorted(
            self.employee_data.values(), key=lambda e: e.get("display_name", "")
        )

        self.team_table.setRowCount(len(employees))
        self.stars_table.setRowCount(len(employees))

        for row, employee in enumerate(employees):
            display_name = employee.get("display_name", "")
            emp_id = employee.get("id")
            settings_entry = employee_settings.get(emp_id, {})
            team_value = settings_entry.get("team", "A")
            stars_value = int(settings_entry.get("stars", 0) or 0)

            name_item = QtWidgets.QTableWidgetItem(display_name)
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.team_table.setItem(row, 0, name_item)

            combo = QtWidgets.QComboBox()
            for value, label in self.TEAM_OPTIONS:
                combo.addItem(label, value)
            idx = combo.findData(team_value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.setStyleSheet(self.combo_style())
            self.team_table.setCellWidget(row, 1, combo)

            stars_name_item = QtWidgets.QTableWidgetItem(display_name)
            stars_name_item.setFlags(
                stars_name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.stars_table.setItem(row, 0, stars_name_item)

            stars_spin = QtWidgets.QSpinBox()
            stars_spin.setRange(0, 1_000_000)
            stars_spin.setValue(stars_value)
            stars_spin.setToolTip("Pontuação em estrelas (1 estrela = 1 ponto).")
            stars_spin.setStyleSheet(self.spinbox_style())
            self.stars_table.setCellWidget(row, 1, stars_spin)

    def set_bonus_row(self, row, min_value, max_value, winner_value, loser_value):
        def mk_dspin(minv, maxv, dec, val):
            s = QtWidgets.QDoubleSpinBox()
            s.setRange(minv, maxv)
            s.setDecimals(dec)
            s.setValue(float(val))
            s.setStyleSheet(self.spinbox_style())
            return s

        self.bonus_table.setCellWidget(row, 0, mk_dspin(0, 100, 2, min_value))
        self.bonus_table.setCellWidget(row, 1, mk_dspin(0, 100, 2, max_value))
        self.bonus_table.setCellWidget(row, 2, mk_dspin(0, 10, 4, winner_value))
        self.bonus_table.setCellWidget(row, 3, mk_dspin(0, 10, 4, loser_value))

    def add_bonus_row(self):
        row = self.bonus_table.rowCount()
        self.bonus_table.insertRow(row)
        self.set_bonus_row(row, 0, 0, 0, 0)

    def remove_bonus_row(self):
        row = self.bonus_table.currentRow()
        if row >= 0:
            self.bonus_table.removeRow(row)

    def handle_save(self):
        bonus_rules = []
        for row in range(self.bonus_table.rowCount()):
            min_spin = self.bonus_table.cellWidget(row, 0)
            max_spin = self.bonus_table.cellWidget(row, 1)
            win_spin = self.bonus_table.cellWidget(row, 2)
            lose_spin = self.bonus_table.cellWidget(row, 3)

            if not (min_spin and max_spin and win_spin and lose_spin):
                continue

            min_value = float(min_spin.value())
            max_value = float(max_spin.value())

            if min_value > max_value:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Faixa inválida",
                    "O mix mínimo não pode ser maior que o mix máximo.",
                )
                return

            bonus_rules.append(
                {
                    "min": min_value,
                    "max": max_value,
                    "winner": float(win_spin.value()),
                    "loser": float(lose_spin.value()),
                }
            )

        employee_settings = copy.deepcopy(
            self.original_config.get("employee_settings", {})
        )

        for row in range(self.team_table.rowCount()):
            name_item = self.team_table.item(row, 0)
            combo = self.team_table.cellWidget(row, 1)
            if not name_item or not combo:
                continue
            emp_id = name_item.text().split(" - ")[0].strip()
            employee_settings.setdefault(emp_id, {})
            employee_settings[emp_id]["team"] = combo.currentData()

        for row in range(self.stars_table.rowCount()):
            name_item = self.stars_table.item(row, 0)
            spin = self.stars_table.cellWidget(row, 1)
            if not name_item or not isinstance(spin, QtWidgets.QSpinBox):
                continue
            emp_id = name_item.text().split(" - ")[0].strip()
            employee_settings.setdefault(emp_id, {})
            employee_settings[emp_id]["stars"] = int(spin.value())

        self.original_config["bonus_rules"] = bonus_rules
        self.original_config["mix_rule_type"] = self.rule_type_combo.currentData()
        self.original_config["mix_rules"] = {
            "all_or_nothing": {
                "min_mix": float(self.min_mix_spin.value()),
                "bonus_per_liter": float(self.all_bonus_spin.value()),
            }
        }
        self.original_config["employee_settings"] = employee_settings

        self.accept()

    def get_config(self):
        return self.original_config

    @staticmethod
    def spinbox_style():
        return """
        QSpinBox, QDoubleSpinBox {
            padding: 6px;
            border: 1px solid #FFD500;
            border-radius: 10px;
            color: #111827;
            background-color: #FFFFFF;
        }
        QSpinBox:focus, QDoubleSpinBox:focus { border-color: #ED1C24; }
        """

    @staticmethod
    def combo_style():
        return """
        QComboBox {
            padding: 6px;
            border: 1px solid #FFD500;
            border-radius: 10px;
            color: #111827;
            background-color: #FFFFFF;
        }
        QComboBox:focus { border-color: #ED1C24; }
        """

    @staticmethod
    def btn_primary():
        return """
        QPushButton {
            background-color: #ED1C24;
            color: white;
            font-size: 13px;
            padding: 8px 18px;
            border-radius: 12px;
        }
        QPushButton:hover { background-color: #d81920; }
        """

    @staticmethod
    def btn_secondary():
        return """
        QPushButton {
            background-color: #FFF4B5;
            color: #ED1C24;
            font-size: 13px;
            padding: 8px 18px;
            border: 1px solid #FFD500;
            border-radius: 12px;
        }
        QPushButton:hover { background-color: #FFE98B; }
        """

    @staticmethod
    def btn_danger():
        return """
        QPushButton {
            background-color: #111827;
            color: white;
            font-size: 13px;
            padding: 8px 18px;
            border-radius: 12px;
        }
        QPushButton:hover { background-color: #0b1220; }
        """


# =========================
# App principal
# =========================
class BonusCalculator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Paths
        self.app_dir = app_writable_dir()
        self.config_file = os.path.join(self.app_dir, "config.json")

        self.setWindowTitle("Mix V-Power - Calculadora de Bonificação")
        self.setMinimumSize(980, 650)
        self.setWindowIcon(QtGui.QIcon(resource_path("icons/iconV.ico")))

        # Cores
        self.primary_color = "#FFFFFF"
        self.secondary_yellow = "#FFD500"
        self.secondary_red = "#ED1C24"
        self.text_main = "#111827"
        self.text_muted = "#6b7280"
        self.card_border = "#FFE98B"
        self.card_bg = "#FFFFFF"
        self.surface_bg = "#FFFDF4"

        self.last_directory = os.getcwd()
        self.last_report_update = None
        self.employee_data = {}
        self.employees = []
        self.search_history = []
        self.mix_history = {}

        self._mix_anim = None

        self.load_config()
        self.apply_global_style()
        self.build_ui()
        self.setup_shortcuts()
        self.load_report()

    def apply_global_style(self):
        self.setStyleSheet(
            """
            QWidget { font-family: "Segoe UI"; }
            QToolTip {
                background: #111827;
                color: white;
                border: 1px solid #374151;
                padding: 8px;
                border-radius: 8px;
            }
            """
        )

    # -------------------------
    # Config
    # -------------------------
    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = copy.deepcopy(DEFAULT_CONFIG)

        self.config.setdefault("mix_rule_type", DEFAULT_CONFIG["mix_rule_type"])
        self.config.setdefault("mix_rules", copy.deepcopy(DEFAULT_CONFIG["mix_rules"]))
        self.config.setdefault("employee_settings", {})
        self.config.setdefault("search_history", [])
        self.config.setdefault("mix_history", {})
        self.config.setdefault("last_report_update", None)
        self.config.setdefault("last_directory", None)

        self.config["bonus_rules"] = self.normalize_bonus_rules(
            self.config.get("bonus_rules", copy.deepcopy(DEFAULT_CONFIG["bonus_rules"]))
        )

        self.last_directory = self.config.get("last_directory") or os.getcwd()
        self.search_history = self.config.get("search_history", [])
        self.mix_history = self.config.get("mix_history", {})

        last_update_str = self.config.get("last_report_update")
        if last_update_str:
            try:
                self.last_report_update = datetime.datetime.fromisoformat(
                    last_update_str
                )
            except ValueError:
                self.last_report_update = None

    @staticmethod
    def normalize_bonus_rules(bonus_rules):
        normalized = []
        for rule in bonus_rules or []:
            min_value = rule.get("min")
            max_value = rule.get("max")
            if min_value is None or max_value is None:
                continue

            if "winner" in rule or "loser" in rule:
                normalized.append(
                    {
                        "min": float(min_value),
                        "max": float(max_value),
                        "winner": float(rule.get("winner", 0.0)),
                        "loser": float(rule.get("loser", 0.0)),
                    }
                )
            else:
                value = float(rule.get("value", 0.0))
                normalized.append(
                    {
                        "min": float(min_value),
                        "max": float(max_value),
                        "winner": value,
                        "loser": value,
                    }
                )

        if not normalized:
            return copy.deepcopy(DEFAULT_CONFIG["bonus_rules"])

        normalized.sort(key=lambda r: (r.get("min", 0), r.get("max", 0)))
        return normalized

    def save_config(self):
        self.config["last_directory"] = self.last_directory
        self.config["search_history"] = self.search_history
        self.config["mix_history"] = self.mix_history
        self.config["last_report_update"] = (
            self.last_report_update.isoformat() if self.last_report_update else None
        )

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    # -------------------------
    # UI
    # -------------------------
    def build_ui(self):
        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background-color: {self.primary_color};")
        self.setCentralWidget(central)

        self.stack = QtWidgets.QStackedWidget()
        self.login_page = self.build_login_page()
        self.result_page = self.build_result_page()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.result_page)

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.stack)

    def setup_shortcuts(self):
        self.shortcut_escape = QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Escape), self
        )
        self.shortcut_escape.activated.connect(self.handle_escape)

        self.shortcut_copy = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self)
        self.shortcut_copy.activated.connect(self.copy_results_to_clipboard)

    def handle_escape(self):
        current = self.stack.currentWidget()
        if current == self.result_page:
            self.return_to_login()
        else:
            self.close()

    def copy_results_to_clipboard(self):
        emp = self.employee_name_label.text().strip()
        if not emp:
            return

        texto = (
            f"{emp}\n"
            f"{self.mix_big_label.text()}\n"
            f"Time: {self.kpi_values['time'].text()}\n"
            f"Comum: {self.kpi_values['comum'].text()} L\n"
            f"V-Power: {self.kpi_values['vpower'].text()} L\n"
            f"Total: {self.kpi_values['total'].text()} L\n"
            f"Bônus/L: {self.kpi_values['bonus_per_liter'].text()}\n"
            f"Total: {self.kpi_values['bonus_total'].text()}\n"
            f"Relatório: {self.kpi_values['update_time'].text()}\n"
            f"Estrelas: {self.kpi_values['stars'].text()}\n"
        )
        QtWidgets.QApplication.clipboard().setText(texto)

    def build_login_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 50, 20, 20)
        layout.setSpacing(10)

        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(resource_path("Logo_Vpower.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaledToWidth(
                    280, QtCore.Qt.TransformationMode.SmoothTransformation
                )
            )
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title = QtWidgets.QLabel("Mix V-Power")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 34px; font-weight: 900; color: #ED1C24;")

        subtitle = QtWidgets.QLabel("Consulta rápida por funcionário")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #6b7280;")

        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setPlaceholderText("Código do funcionário")
        self.code_input.setFixedWidth(340)
        self.code_input.setStyleSheet(
            """
            QLineEdit {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #FFD500;
                border-radius: 14px;
                color: #111827;
                background-color: #FFFFFF;
            }
            QLineEdit:focus { border-color: #ED1C24; }
            """
        )
        self.code_input.returnPressed.connect(self.handle_login)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.login_button = QtWidgets.QPushButton("Entrar")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ED1C24;
                color: white;
                font-size: 18px;
                padding: 12px 34px;
                border-radius: 16px;
            }
            QPushButton:hover { background-color: #d81920; }
            QPushButton:disabled { background-color: #f19aa0; }
            """
        )

        self.refresh_button = QtWidgets.QToolButton()
        self.refresh_button.setIcon(QtGui.QIcon(resource_path("icons/atualizar.png")))
        self.refresh_button.setIconSize(QtCore.QSize(30, 30))
        self.refresh_button.setToolTip("Atualizar relatório")
        self.refresh_button.setStyleSheet(
            """
            QToolButton {
                background-color: #FFF4B5;
                border: 1px solid #FFD500;
                border-radius: 14px;
                padding: 10px;
            }
            QToolButton:hover { background-color: #FFE98B; }
            """
        )
        self.refresh_button.clicked.connect(self.reload_report)

        self.refresh_spinner = QtWidgets.QProgressBar()
        self.refresh_spinner.setFixedWidth(140)
        self.refresh_spinner.setRange(0, 0)
        self.refresh_spinner.setVisible(False)
        self.refresh_spinner.setStyleSheet(
            """
            QProgressBar {border: 1px solid #FFD500; border-radius: 10px; text-align: center; color: #111827; background: #FFFFFF;}
            QProgressBar::chunk {background-color: #FFD500; border-radius: 10px;}
            """
        )

        button_row.addWidget(self.login_button)
        button_row.addSpacing(14)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.refresh_spinner)

        settings_button = QtWidgets.QToolButton()
        settings_button.setIcon(QtGui.QIcon(resource_path("icons/cog.ico")))
        settings_button.setIconSize(QtCore.QSize(22, 22))
        settings_button.setToolTip("Configurações")
        settings_button.setStyleSheet(
            "QToolButton { background: transparent; border: none; padding: 8px; }"
        )
        settings_button.clicked.connect(self.open_settings)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #ED1C24; font-weight: 700;"
        )

        center_layout = QtWidgets.QVBoxLayout()
        center_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(10)
        center_layout.addWidget(title)
        center_layout.addWidget(subtitle)
        center_layout.addSpacing(10)
        center_layout.addWidget(
            self.code_input, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        center_layout.addSpacing(10)
        center_layout.addWidget(logo)
        center_layout.addSpacing(10)
        center_layout.addLayout(button_row)
        center_layout.addWidget(self.status_label)

        layout.addStretch()
        layout.addLayout(center_layout)
        layout.addStretch()

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addStretch()
        bottom_row.addWidget(
            settings_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        layout.addLayout(bottom_row)
        return widget

    # -------------------------
    # RESULT PAGE (leve)
    # -------------------------
    def build_result_page(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet(f"background: {self.primary_color};")
        root = QtWidgets.QVBoxLayout(widget)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(14)

        header_card = self.make_card(flat=True)
        header_layout = QtWidgets.QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(10)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(10)

        self.employee_name_label = QtWidgets.QLabel("")
        self.employee_name_label.setStyleSheet(
            "font-size: 22px; font-weight: 900; color: #111827;"
        )
        self.employee_name_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.team_badge = QtWidgets.QLabel("—")
        self.team_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.team_badge.setMinimumWidth(140)
        self.team_badge.setStyleSheet(self.badge_style("neutral"))

        info_row = QtWidgets.QHBoxLayout()
        info_row.setSpacing(10)

        self.rule_chip = QtWidgets.QLabel("Regra: —")
        self.rule_chip.setStyleSheet(self.chip_style())

        self.update_chip = QtWidgets.QLabel("Atualizado: —")
        self.update_chip.setStyleSheet(self.chip_style())

        self.night_chip = QtWidgets.QLabel("Noturno: —")
        self.night_chip.setStyleSheet(self.chip_style())
        self.night_chip.setVisible(False)

        info_row.addWidget(self.rule_chip)
        info_row.addWidget(self.update_chip)
        info_row.addWidget(self.night_chip)
        info_row.addStretch()

        top_row.addWidget(self.employee_name_label)
        top_row.addStretch()
        top_row.addWidget(self.team_badge)

        mix_row = QtWidgets.QHBoxLayout()
        mix_row.setSpacing(14)

        mix_left = QtWidgets.QVBoxLayout()
        mix_left.setSpacing(6)

        self.mix_big_label = QtWidgets.QLabel("Mix: —")
        self.mix_big_label.setStyleSheet(
            "font-size: 40px; font-weight: 950; color: #ED1C24;"
        )
        self.mix_sub_label = QtWidgets.QLabel("Bateu a meta? Veja o medidor.")
        self.mix_sub_label.setStyleSheet(
            "font-size: 12px; color: #6b7280; font-weight: 600;"
        )

        mix_left.addWidget(self.mix_big_label)
        mix_left.addWidget(self.mix_sub_label)

        mix_right = QtWidgets.QVBoxLayout()
        mix_right.setSpacing(8)

        self.mix_progress = QtWidgets.QProgressBar()
        self.mix_progress.setRange(0, 10000)
        self.mix_progress.setValue(0)
        self.mix_progress.setTextVisible(False)
        self.mix_progress.setFixedHeight(14)
        self.mix_progress.setStyleSheet(self.progress_style("ok"))

        self.mix_progress_label = QtWidgets.QLabel("0,00%")
        self.mix_progress_label.setStyleSheet(
            "font-size: 12px; color: #111827; font-weight: 800;"
        )
        self.mix_progress_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        mix_right.addWidget(self.mix_progress_label)
        mix_right.addWidget(self.mix_progress)

        mix_row.addLayout(mix_left, 2)
        mix_row.addLayout(mix_right, 3)

        header_layout.addLayout(top_row)
        header_layout.addLayout(info_row)
        header_layout.addLayout(mix_row)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.kpi_values = {}

        card_team = self.make_kpi_card(
            "🏁 Resumo do time",
            [("Time", "time"), ("Mix do time (%)", "team_mix")],
        )
        card_liters = self.make_kpi_card(
            "⛽ Litros vendidos",
            [
                ("Gasolina Comum (L)", "comum"),
                ("V-Power (L)", "vpower"),
                ("Total (L)", "total"),
            ],
        )
        card_bonus = self.make_kpi_card(
            "💰 Bonificação",
            [("Bônus por litro", "bonus_per_liter"), ("Total estimado", "bonus_total")],
        )
        card_highlights = self.make_kpi_card(
            "⭐ Destaques",
            [("Estrelas", "stars"), ("Relatório", "update_time")],
        )

        grid.addWidget(card_team, 0, 0)
        grid.addWidget(card_bonus, 0, 1)
        grid.addWidget(card_liters, 1, 0)
        grid.addWidget(card_highlights, 1, 1)

        footer = QtWidgets.QHBoxLayout()
        footer.setSpacing(10)

        hint = QtWidgets.QLabel("Dica: Ctrl+C copia o resumo do funcionário.")
        hint.setStyleSheet("font-size: 6px; color: #6b7280; font-weight: 600;")

        back_button = QtWidgets.QPushButton("Voltar")
        back_button.clicked.connect(self.return_to_login)
        back_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FFF4B5;
                color: #ED1C24;
                font-size: 14px;
                padding: 10px 20px;
                border: 1px solid #FFD500;
                border-radius: 14px;
                font-weight: 800;
            }
            QPushButton:hover { background-color: #FFE98B; }
            """
        )

        footer.addWidget(hint)
        footer.addStretch()
        footer.addWidget(back_button)

        root.addWidget(header_card)
        root.addLayout(grid)
        root.addStretch()
        root.addLayout(footer)

        return widget

    # -------------------------
    # Cards leves: sem DropShadowEffect
    # -------------------------
    def make_card(self, flat: bool = True) -> QtWidgets.QFrame:
        """
        flat=True => sem QGraphicsDropShadowEffect (remove warnings QPainter e fica mais leve)
        """
        card = QtWidgets.QFrame()
        if flat:
            card.setStyleSheet(
                f"""
                QFrame {{
                    background: {self.card_bg};
                    border: 1px solid {self.card_border};
                    border-radius: 18px;
                }}
                """
            )
        else:
            # (não usar por padrão)
            card.setStyleSheet(
                f"""
                QFrame {{
                    background: {self.card_bg};
                    border: 1px solid {self.card_border};
                    border-radius: 18px;
                }}
                """
            )
        return card

    def make_kpi_card(
        self, title: str, fields: list[tuple[str, str]]
    ) -> QtWidgets.QFrame:
        card = self.make_card(flat=True)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        t = QtWidgets.QLabel(title)
        t.setStyleSheet("font-size: 14px; font-weight: 900; color: #ED1C24;")
        layout.addWidget(t)

        for label, key in fields:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(8)

            name_label = QtWidgets.QLabel(label)
            name_label.setStyleSheet(
                "font-size: 18px; color: #808080; font-weight: 900;"
            )

            value_label = QtWidgets.QLabel("—")
            value_label.setStyleSheet(
                "font-size: 18px; font-weight: 950; color: #111827;"
            )
            value_label.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            )

            row.addWidget(name_label)
            row.addStretch()
            row.addWidget(value_label)

            layout.addLayout(row)
            self.kpi_values[key] = value_label

        return card

    def chip_style(self) -> str:
        return """
        QLabel {
            background: #FFFDF4;
            border: 1px solid #FFE98B;
            border-radius: 12px;
            padding: 6px 10px;
            color: #111827;
            font-size: 12px;
            font-weight: 800;
        }
        """

    def badge_style(self, kind: str) -> str:
        if kind == "A":
            bg, fg, border = "#FFF4B5", "#111827", "#FFD500"
        elif kind == "B":
            bg, fg, border = "#FFE7E9", "#111827", "#ED1C24"
        elif kind == "NIGHT":
            bg, fg, border = "#111827", "#FFFFFF", "#111827"
        else:
            bg, fg, border = "#F3F4F6", "#111827", "#E5E7EB"

        return f"""
        QLabel {{
            background: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 950;
        }}
        """

    def progress_style(self, kind: str) -> str:
        if kind == "bad":
            chunk = "#ED1C24"
        elif kind == "warn":
            chunk = "#FFD500"
        else:
            chunk = "#22c55e"

        return f"""
        QProgressBar {{
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            background: #F9FAFB;
        }}
        QProgressBar::chunk {{
            background: {chunk};
            border-radius: 8px;
        }}
        """

    # -------------------------
    # Relatório
    # -------------------------
    def update_status(self):
        if self.last_report_update:
            update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
            self.status_label.setText(f"Atualizado em {update_time}")
        else:
            self.status_label.setText("")

    def show_buffering(self, active: bool):
        self.refresh_spinner.setVisible(active)
        self.refresh_button.setEnabled(not active)
        self.login_button.setEnabled(not active)

    def load_report(self):
        self.show_buffering(True)
        QtWidgets.QApplication.processEvents()

        default_report = os.path.join(self.last_directory, "relatorio.txt")
        if os.path.exists(default_report):
            file_path = default_report
        else:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Selecione o arquivo de relatório",
                self.last_directory,
                "Arquivos de texto (*.txt);;Todos os arquivos (*.*)",
            )

        if not file_path:
            self.show_buffering(False)
            return

        self.last_directory = os.path.dirname(file_path)

        report_data = parsear_relatorio(file_path)
        if not report_data or not report_data.get("funcionarios"):
            self.show_buffering(False)
            QtWidgets.QMessageBox.warning(
                self, "Relatório inválido", "O relatório não é válido ou está vazio."
            )
            return

        self.employees = []
        self.employee_data = {}

        employee_settings = self.config.get("employee_settings", {})
        now = datetime.datetime.now().isoformat()

        for emp in report_data["funcionarios"]:
            employee_id = str(emp["codigo"])
            employee_name = emp["nome"]
            display_name = f"{employee_id} - {employee_name}"

            gasolina_comum = 0.0
            gasolina_vpower = 0.0

            for item in emp.get("itens", []):
                produto = (item.get("produto", "") or "").strip().upper()
                quantidade = float(item.get("quantidade", 0.0) or 0.0)

                if produto == "GASOLINA C COMUM":
                    gasolina_comum += quantidade
                elif produto == "GASOLINA C COMUM ADITIVADA":
                    gasolina_vpower += quantidade

            total_quantity = gasolina_comum + gasolina_vpower
            mix = (
                (gasolina_vpower / total_quantity * 100) if total_quantity > 0 else 0.0
            )
            previous_mix = self.mix_history.get(employee_id, {}).get("mix")

            self.employee_data[employee_id] = {
                "id": employee_id,
                "name": employee_name,
                "display_name": display_name,
                "sales_count": emp["vendas"],
                "products": emp.get("itens", []),
                "total_quantity": total_quantity,
                "gasolina_comum": gasolina_comum,
                "gasolina_vpower": gasolina_vpower,
                "mix": mix,
                "previous_mix": previous_mix,
            }
            self.employees.append(employee_id)

            if employee_id not in employee_settings:
                employee_settings[employee_id] = {"team": "A", "stars": 0}
            else:
                employee_settings[employee_id].setdefault("team", "A")
                employee_settings[employee_id].setdefault("stars", 0)

            self.mix_history[employee_id] = {
                "name": display_name,
                "mix": mix,
                "timestamp": now,
            }

        self.config["employee_settings"] = employee_settings
        self.last_report_update = datetime.datetime.fromtimestamp(
            os.path.getmtime(file_path)
        )
        self.save_config()

        self.show_buffering(False)
        self.update_status()

    def handle_login(self):
        code = self.code_input.text().strip()
        if not code:
            self.status_label.setText("Digite o código do funcionário para consultar.")
            return

        if code not in self.employee_data:
            QtWidgets.QMessageBox.warning(
                self,
                "Funcionário não encontrado",
                "Não foi possível encontrar o funcionário informado.",
            )
            return

        employee = self.employee_data[code]
        self.add_to_search_history(employee["id"], employee["display_name"])
        self.show_employee_results(code)
        self.switch_page(self.result_page)
        self.code_input.clear()

    def switch_page(self, target):
        current = self.stack.currentWidget()
        if current == target:
            return
        target_index = self.stack.indexOf(target)
        self.fade_transition(target_index)

    def return_to_login(self):
        self.switch_page(self.login_page)

    def fade_transition(self, target_index):
        current_widget = self.stack.currentWidget()
        effect = QtWidgets.QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(effect)

        fade_out = QtCore.QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(180)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        def on_fade_out():
            current_widget.setGraphicsEffect(None)
            self.stack.setCurrentIndex(target_index)
            new_widget = self.stack.currentWidget()
            effect_in = QtWidgets.QGraphicsOpacityEffect(new_widget)
            new_widget.setGraphicsEffect(effect_in)

            fade_in = QtCore.QPropertyAnimation(effect_in, b"opacity")
            fade_in.setDuration(180)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.finished.connect(lambda: new_widget.setGraphicsEffect(None))
            fade_in.start()
            self._fade_in_anim = fade_in

        fade_out.finished.connect(on_fade_out)
        fade_out.start()
        self._fade_out_anim = fade_out

    # -------------------------
    # Lógica de bônus
    # -------------------------
    def _valid_employees_for_team_calc(self):
        valid = []
        settings = self.config.get("employee_settings", {})
        for emp in self.employee_data.values():
            team = settings.get(emp["id"], {}).get("team", "A")
            if team not in ("OIL", "INACTIVE"):
                valid.append(emp)
        return valid

    def _split_teams(self, valid_emps):
        settings = self.config.get("employee_settings", {})
        teams = {"A": [], "B": []}
        for emp in valid_emps:
            team = settings.get(emp["id"], {}).get("team", "A")
            if str(team).startswith("A"):
                teams["A"].append(emp)
            elif str(team).startswith("B"):
                teams["B"].append(emp)
        return teams

    @staticmethod
    def _calc_team_mix(team_emps):
        total_premium = sum(e["gasolina_vpower"] for e in team_emps)
        total = sum(e["total_quantity"] for e in team_emps)
        return (total_premium / total * 100) if total > 0 else 0.0

    def _bonus_rule_for_mix(self, mix_percentage: float):
        for rule in self.config.get("bonus_rules", []):
            min_value = float(rule.get("min", 0))
            max_value = float(rule.get("max", 0))
            if min_value <= mix_percentage <= max_value:
                return rule
        return None

    def animate_progress(self, bar: QtWidgets.QProgressBar, target_value: int):
        start_value = bar.value()
        anim = QtCore.QPropertyAnimation(bar, b"value")
        anim.setDuration(260)
        anim.setStartValue(start_value)
        anim.setEndValue(target_value)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        anim.start()
        self._mix_anim = anim

    def show_employee_results(self, employee_id):
        employee_data = self.employee_data[employee_id]
        emp_id = employee_data["id"]

        emp_settings = self.config.get("employee_settings", {}).get(
            emp_id, {"team": "A", "stars": 0}
        )
        emp_team = emp_settings.get("team", "A")

        if emp_team in ("OIL", "INACTIVE"):
            QtWidgets.QMessageBox.information(
                self,
                "Sem bonificação",
                "Este funcionário não participa do cálculo de bonificação.",
            )
            return

        valid_emps = self._valid_employees_for_team_calc()
        teams = self._split_teams(valid_emps)

        mix_a = self._calc_team_mix(teams["A"])
        mix_b = self._calc_team_mix(teams["B"])

        total_quantity = float(employee_data["total_quantity"])
        premium_quantity = float(employee_data["gasolina_vpower"])
        mix_percentage = (
            (premium_quantity / total_quantity * 100) if total_quantity > 0 else 0.0
        )

        base_team = "A" if str(emp_team).startswith("A") else "B"
        team_mix = mix_a if base_team == "A" else mix_b

        is_night = emp_team in ("A_NIGHT", "B_NIGHT")
        mix_rule_type = self.config.get("mix_rule_type", "team")
        mix_rules = self.config.get("mix_rules", {})
        all_or_nothing = mix_rules.get("all_or_nothing", {})

        bonus_per_liter = 0.0
        rule_label = ""

        if mix_rule_type == "all_or_nothing":
            min_mix = float(all_or_nothing.get("min_mix", 40.0))
            base_bonus = float(all_or_nothing.get("bonus_per_liter", 0.0))
            bonus_per_liter = base_bonus if mix_percentage >= min_mix else 0.0
            rule_label = f"Tudo ou nada (mín. {self.format_brl(min_mix, 2)}%)"
        else:
            winner_team = "A" if mix_a > mix_b else "B" if mix_b > mix_a else "TIE"
            winner_mix = max(mix_a, mix_b)

            rule = self._bonus_rule_for_mix(winner_mix)
            if rule:
                win_bonus = float(rule.get("winner", 0.0))
                lose_bonus = float(rule.get("loser", 0.0))
            else:
                win_bonus = 0.0
                lose_bonus = 0.0

            if winner_team == "TIE":
                bonus_per_liter = win_bonus
            else:
                bonus_per_liter = win_bonus if base_team == winner_team else lose_bonus

            rule_label = "Por time (vencedor x perdedor)"

        if is_night:
            bonus_per_liter *= 0.7

        total_bonus = premium_quantity * bonus_per_liter

        diurnos = [
            emp
            for emp in valid_emps
            if self.config.get("employee_settings", {})
            .get(emp["id"], {})
            .get("team", "A")
            == base_team
        ]
        avg_team_liters_display = (
            (sum(emp["total_quantity"] for emp in diurnos) / len(diurnos))
            if diurnos
            else 0.0
        )

        self.employee_name_label.setText(employee_data["display_name"])

        badge_text = (
            str(emp_team)
            .replace("_NIGHT", " (Noturno)")
            .replace("OIL", "Troca de Óleo")
        )
        if emp_team in ("A", "A_NIGHT"):
            badge_kind = "NIGHT" if is_night else "A"
        else:
            badge_kind = "NIGHT" if is_night else "B"
        self.team_badge.setText(badge_text)
        self.team_badge.setStyleSheet(self.badge_style(badge_kind))

        self.rule_chip.setText(f"Regra: {rule_label}")
        self.update_chip.setText(
            "Atualizado: "
            + (
                self.last_report_update.strftime("%d/%m/%Y %H:%M")
                if self.last_report_update
                else "—"
            )
        )

        self.night_chip.setVisible(bool(is_night))
        if is_night:
            self.night_chip.setText("Noturno: 70% do bônus")

        self.mix_big_label.setText(f"Mix: {self.format_brl(mix_percentage, 2)}%")
        self.mix_progress_label.setText(f"{self.format_brl(mix_percentage, 2)}%")

        target = int(max(0.0, min(100.0, mix_percentage)) * 100)
        self.animate_progress(self.mix_progress, target)

        if mix_percentage < 35:
            self.mix_progress.setStyleSheet(self.progress_style("bad"))
        elif mix_percentage < 45:
            self.mix_progress.setStyleSheet(self.progress_style("warn"))
        else:
            self.mix_progress.setStyleSheet(self.progress_style("ok"))

        self.kpi_values["time"].setText(
            str(emp_team)
            .replace("_NIGHT", " (Noturno)")
            .replace("OIL", "Troca de Óleo")
        )
        self.kpi_values["team_mix"].setText(self.format_brl(team_mix, 2))
        self.kpi_values["comum"].setText(
            self.format_brl(employee_data["gasolina_comum"])
        )
        self.kpi_values["vpower"].setText(
            self.format_brl(employee_data["gasolina_vpower"])
        )
        self.kpi_values["total"].setText(self.format_brl(total_quantity))
        self.kpi_values["bonus_per_liter"].setText(
            self.format_brl_money(bonus_per_liter, decimals=4)
        )
        self.kpi_values["bonus_total"].setText(self.format_brl_money(total_bonus))
        self.kpi_values["stars"].setText(str(int(emp_settings.get("stars", 0) or 0)))
        self.kpi_values["update_time"].setText(
            self.last_report_update.strftime("%d/%m/%Y às %H:%M")
            if self.last_report_update
            else "-"
        )

        tooltip = (
            f"Mix do time: {self.format_brl(team_mix, 2)}%\n"
            f"Média do time: {self.format_brl(avg_team_liters_display)} L\n"
            f"Regra: {rule_label}\n"
            f"Bônus/L: {self.format_brl_money(bonus_per_liter, decimals=3)}"
        )
        self.mix_big_label.setToolTip(tooltip)
        self.mix_progress.setToolTip(tooltip)

    # -------------------------
    # Histórico / ações
    # -------------------------
    def add_to_search_history(self, employee_code, employee_name):
        history_entry = {
            "employee_id": employee_code,
            "employee_name": employee_name,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.search_history = [
            h for h in self.search_history if h.get("employee_id") != employee_code
        ]
        self.search_history.insert(0, history_entry)
        self.search_history = self.search_history[:10]
        self.save_config()

    def reload_report(self):
        self.load_report()

    def open_settings(self):
        password_dialog = SettingsPasswordDialog(self)
        if password_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        if password_dialog.password() != "Zam1234@":
            QtWidgets.QMessageBox.warning(
                self, "Senha incorreta", "A senha informada está incorreta."
            )
            return

        dialog = SettingsDialog(self, self.config, self.employee_data)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            self.config["bonus_rules"] = self.normalize_bonus_rules(
                self.config.get("bonus_rules")
            )
            self.save_config()

    # -------------------------
    # Utils
    # -------------------------
    @staticmethod
    def format_brl(value, decimals=3):
        return (
            f"{value:,.{decimals}f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    @staticmethod
    def format_brl_money(value, decimals=2):
        return (
            f"R$ {value:,.{decimals}f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )


if __name__ == "__main__":
    # Deixa mais suave em alguns PCs (evita repaint excessivo em certos drivers)
    QtCore.QCoreApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
    )

    app = QtWidgets.QApplication(sys.argv)
    window = BonusCalculator()
    window.show()
    sys.exit(app.exec())

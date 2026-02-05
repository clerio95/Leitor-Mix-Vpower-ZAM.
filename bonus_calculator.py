import json
import os
import re
import locale
import sys
import datetime
import copy

from PySide6 import QtCore, QtGui, QtWidgets


try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except Exception:
    pass


def converter_numero_brasileiro(valor: str) -> float:
    """Converte número no formato brasileiro (1.234,567) para float."""
    if not valor or not valor.strip():
        return 0.0

    valor = valor.strip().replace('.', '').replace(',', '.')

    try:
        return float(valor)
    except ValueError:
        return 0.0


def extrair_cabecalho(linhas):
    """Extrai informações do cabeçalho do relatório."""
    header = {}

    for linha in linhas:
        linha = linha.strip()

        if not linha or linha.startswith('+') or linha.startswith('-'):
            continue

        match = re.search(r'Empresa:\s*(.+?)\s*\|\s*$', linha, re.IGNORECASE)
        if match:
            header['empresa'] = match.group(1).strip()

        match = re.search(r'Período:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['periodo'] = match.group(1).strip()

        match = re.search(r'Modo:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['modo'] = match.group(1).strip()

        match = re.search(r'Agrupar:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['agrupar'] = match.group(1).strip()

        match = re.search(r'Ordenar:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['ordenar'] = match.group(1).strip()

        match = re.search(r'Produtividade:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['produtividade'] = match.group(1).strip()

        match = re.search(r'Grupo empresa:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['grupo_empresa'] = match.group(1).strip()

        match = re.search(r'Grupo produto:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['grupo_produto'] = match.group(1).strip()

        match = re.search(r'Exibir:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['exibir'] = match.group(1).strip()

        if 'Funcionário:' in linha and 'Vendas:' in linha:
            break

    return header


def parsear_linha_item(linha):
    """Parseia uma linha de item da tabela de produtos."""
    if not linha.strip() or linha.strip().startswith('+') or 'Código' in linha or 'Produto' in linha:
        return None

    if not linha.strip().startswith('|') or not linha.strip().endswith('|'):
        return None

    if 'Total do vendedor' in linha:
        return None

    campos = [campo.strip() for campo in linha.split('|')]
    campos = campos[1:-1]

    if len(campos) != 7:
        return None

    try:
        return {
            'codigo': int(campos[0]) if campos[0] else 0,
            'produto': campos[1],
            'fornecedor': campos[2],
            'quantidade': converter_numero_brasileiro(campos[3]),
            'unidade': campos[4],
            'valor': converter_numero_brasileiro(campos[5]),
            'percentual': converter_numero_brasileiro(campos[6])
        }
    except (ValueError, IndexError):
        return None


def parsear_total_funcionario(linha):
    """Extrai informações do total do funcionário."""
    if 'Total do vendedor e participação geral nas vendas' not in linha:
        return None

    campos = [campo.strip() for campo in linha.split('|')]
    campos = campos[1:-1]

    if len(campos) < 6:
        return None

    try:
        return {
            'quantidade': converter_numero_brasileiro(campos[2]),
            'valor': converter_numero_brasileiro(campos[4]),
            'percentual': converter_numero_brasileiro(campos[5])
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

        match = re.search(r'Funcionário:\s*(\d+)\s*-\s*(.+?)\s+Vendas:\s*(\d+)', linha)
        if match:
            if funcionario_atual:
                funcionario_atual['itens'] = itens_atual
                funcionarios.append(funcionario_atual)

            codigo = int(match.group(1))
            nome = match.group(2).strip()
            vendas = int(match.group(3))

            funcionario_atual = {
                'codigo': codigo,
                'nome': nome,
                'vendas': vendas,
                'itens': [],
                'total': None
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
                funcionario_atual['total'] = total

        i += 1

    if funcionario_atual:
        funcionario_atual['itens'] = itens_atual
        funcionarios.append(funcionario_atual)

    return funcionarios


def extrair_totais_gerais(linhas):
    """Extrai totais gerais do relatório."""
    totais = {}

    for linha in linhas:
        if 'Total geral de vendas no período' in linha:
            campos = [campo.strip() for campo in linha.split('|')]
            campos = campos[1:-1]

            if len(campos) >= 4:
                totais['quantidade'] = converter_numero_brasileiro(campos[1])
                totais['valor'] = converter_numero_brasileiro(campos[3])
            break

    if not totais:
        for linha in linhas:
            if 'Total de vendas da empresa' in linha:
                campos = [campo.strip() for campo in linha.split('|')]
                campos = campos[1:-1]

                if len(campos) >= 4:
                    totais['quantidade'] = converter_numero_brasileiro(campos[2])
                    totais['valor'] = converter_numero_brasileiro(campos[3])
                break

    return totais


def parsear_relatorio(caminho_arquivo: str):
    """Função principal que parseia o arquivo de relatório completo."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        with open(caminho_arquivo, 'r', encoding='latin1') as f:
            linhas = f.readlines()

    return {
        'header': extrair_cabecalho(linhas),
        'funcionarios': extrair_funcionarios(linhas),
        'totaisGerais': extrair_totais_gerais(linhas)
    }


DEFAULT_CONFIG = {
    "bonus_rules": [
        {"min": 35, "max": 40, "winner": 0.01, "loser": 0.01},
        {"min": 40, "max": 45, "winner": 0.015, "loser": 0.015},
        {"min": 45, "max": 50, "winner": 0.02, "loser": 0.02},
        {"min": 50, "max": 50, "winner": 0.0225, "loser": 0.02}
    ],
    "mix_rule_type": "team",
    "mix_rules": {
        "all_or_nothing": {
            "min_mix": 40.0,
            "bonus_per_liter": 0.02
        }
    },
    "employee_settings": {},
    "search_history": [],
    "mix_history": {},
    "last_report_update": None
}


class SettingsPasswordDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso às configurações")
        self.setModal(True)
        self.setFixedWidth(360)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QtWidgets.QLabel("Configurações protegidas")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ED1C24;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        subtitle = QtWidgets.QLabel("Digite a senha para acessar as regras e times.")
        subtitle.setStyleSheet("font-size: 12px; color: #333;")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setStyleSheet(
            "padding: 8px; font-size: 14px; border: 2px solid #FFD500; border-radius: 8px;"
            "color: #111; background-color: #FFFFFF;"
        )

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()

        cancel_button = QtWidgets.QPushButton("Cancelar")
        cancel_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 13px; padding: 6px 16px;"
            "border-radius: 10px;"
        )
        cancel_button.clicked.connect(self.reject)

        confirm_button = QtWidgets.QPushButton("Acessar")
        confirm_button.setStyleSheet(
            "background-color: #ED1C24; color: white; font-size: 13px; padding: 6px 16px;"
            "border-radius: 10px;"
        )
        confirm_button.clicked.connect(self.accept)

        button_row.addWidget(cancel_button)
        button_row.addSpacing(10)
        button_row.addWidget(confirm_button)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.password_input)
        layout.addSpacing(12)
        layout.addLayout(button_row)

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
        self.resize(760, 560)
        self.setStyleSheet("background-color: #FFFFFF;")

        self.original_config = copy.deepcopy(config)
        self.employee_data = employee_data

        self.build_ui()
        self.populate_data()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QtWidgets.QLabel("Configurações de Mix e Times")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #ED1C24;")
        header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane {border: 1px solid #FFD500; border-radius: 8px;}"
            "QTabBar::tab {padding: 8px 14px; font-size: 13px; color: #333; background-color: #FFFFFF;}"
            "QTabBar::tab:selected {background-color: #FFD500; color: #ED1C24;}"
            "QTabBar::tab:!selected {background-color: #FFF4B5;}"
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
        cancel_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 13px; padding: 6px 18px;"
            "border-radius: 10px;"
        )
        cancel_button.clicked.connect(self.reject)

        save_button = QtWidgets.QPushButton("Salvar")
        save_button.setStyleSheet(
            "background-color: #ED1C24; color: white; font-size: 13px; padding: 6px 20px;"
            "border-radius: 10px;"
        )
        save_button.clicked.connect(self.handle_save)

        button_row.addWidget(cancel_button)
        button_row.addSpacing(10)
        button_row.addWidget(save_button)

        layout.addWidget(header)
        layout.addSpacing(12)
        layout.addWidget(self.tabs)
        layout.addSpacing(12)
        layout.addLayout(button_row)

    def build_rules_tab(self):
        layout = QtWidgets.QVBoxLayout(self.rules_tab)

        rule_type_row = QtWidgets.QHBoxLayout()
        rule_type_label = QtWidgets.QLabel("Tipo de regra principal:")
        rule_type_label.setStyleSheet("font-size: 12px; color: #333;")

        self.rule_type_combo = QtWidgets.QComboBox()
        self.rule_type_combo.addItem("Por time (vencedor x perdedor)", "team")
        self.rule_type_combo.addItem("Tudo ou nada (mix individual)", "all_or_nothing")
        self.rule_type_combo.setStyleSheet(
            "padding: 6px; border: 1px solid #FFD500; border-radius: 6px;"
            "color: #111; background-color: #FFFFFF;"
        )

        rule_type_row.addWidget(rule_type_label)
        rule_type_row.addSpacing(10)
        rule_type_row.addWidget(self.rule_type_combo)
        rule_type_row.addStretch()

        self.bonus_table = QtWidgets.QTableWidget()
        self.bonus_table.setColumnCount(3)
        self.bonus_table.setHorizontalHeaderLabels([
            "Mix mínimo (%)",
            "Mix máximo (%)",
            "Bônus por litro",
        ])
        self.bonus_table.horizontalHeader().setStretchLastSection(True)
        self.bonus_table.verticalHeader().setVisible(False)
        self.bonus_table.setStyleSheet(
            "QTableWidget {border: 1px solid #FFD500; border-radius: 8px; color: #111;}"
            "QHeaderView::section {background-color: #FFF4B5; padding: 6px; font-weight: 600; color: #333;}"
        )

        bonus_buttons = QtWidgets.QHBoxLayout()
        add_bonus = QtWidgets.QPushButton("Adicionar faixa")
        add_bonus.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 12px; padding: 4px 12px;"
            "border-radius: 8px;"
        )
        add_bonus.clicked.connect(self.add_bonus_row)

        remove_bonus = QtWidgets.QPushButton("Remover faixa")
        remove_bonus.setStyleSheet(
            "background-color: #ED1C24; color: white; font-size: 12px; padding: 4px 12px;"
            "border-radius: 8px;"
        )
        remove_bonus.clicked.connect(self.remove_bonus_row)

        bonus_buttons.addWidget(add_bonus)
        bonus_buttons.addSpacing(8)
        bonus_buttons.addWidget(remove_bonus)
        bonus_buttons.addStretch()

        all_or_nothing_group = QtWidgets.QGroupBox("Regra tudo ou nada")
        all_or_nothing_group.setStyleSheet(
            "QGroupBox {font-weight: 600; border: 1px solid #FFD500; border-radius: 8px; padding: 8px;"
            "color: #333;}"
            "QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 4px;}"
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

        team_group = QtWidgets.QGroupBox("Regra por time")
        team_group.setStyleSheet(
            "QGroupBox {font-weight: 600; border: 1px solid #FFD500; border-radius: 8px; padding: 8px;"
            "color: #333;}"
            "QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 4px;}"
        )
        team_layout = QtWidgets.QGridLayout(team_group)

        self.winner_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.winner_bonus_spin.setRange(0, 10)
        self.winner_bonus_spin.setDecimals(4)
        self.winner_bonus_spin.setStyleSheet(self.spinbox_style())

        self.loser_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.loser_bonus_spin.setRange(0, 10)
        self.loser_bonus_spin.setDecimals(4)
        self.loser_bonus_spin.setStyleSheet(self.spinbox_style())

        team_layout.addWidget(QtWidgets.QLabel("Bônus vencedor:"), 0, 0)
        team_layout.addWidget(self.winner_bonus_spin, 0, 1)
        team_layout.addWidget(QtWidgets.QLabel("Bônus perdedor:"), 1, 0)
        team_layout.addWidget(self.loser_bonus_spin, 1, 1)

        layout.addLayout(rule_type_row)
        layout.addSpacing(10)
        layout.addWidget(QtWidgets.QLabel("Faixas de bonificação (mix individual):"))
        layout.addWidget(self.bonus_table)
        layout.addLayout(bonus_buttons)
        layout.addSpacing(10)
        layout.addWidget(all_or_nothing_group)
        layout.addSpacing(8)
        layout.addWidget(team_group)
        layout.addStretch()

    def build_teams_tab(self):
        layout = QtWidgets.QVBoxLayout(self.teams_tab)

        info = QtWidgets.QLabel(
            "Defina o time de cada funcionário para o cálculo do mix."
        )
        info.setStyleSheet("font-size: 12px; color: #333;")

        self.team_table = QtWidgets.QTableWidget()
        self.team_table.setColumnCount(2)
        self.team_table.setHorizontalHeaderLabels(["Funcionário", "Time"])
        self.team_table.horizontalHeader().setStretchLastSection(True)
        self.team_table.verticalHeader().setVisible(False)
        self.team_table.setStyleSheet(
            "QTableWidget {border: 1px solid #FFD500; border-radius: 8px; color: #111;}"
            "QHeaderView::section {background-color: #FFF4B5; padding: 6px; font-weight: 600; color: #333;}"
        )

        layout.addWidget(info)
        layout.addSpacing(8)
        layout.addWidget(self.team_table)
        layout.addStretch()

    def build_stars_tab(self):
        layout = QtWidgets.QVBoxLayout(self.stars_tab)

        info = QtWidgets.QLabel(
            "Defina a pontuação em estrelas (1 estrela = 1 ponto)."
        )
        info.setStyleSheet("font-size: 12px; color: #333;")

        self.stars_table = QtWidgets.QTableWidget()
        self.stars_table.setColumnCount(2)
        self.stars_table.setHorizontalHeaderLabels(["Funcionário", "Estrelas (pontos)"])
        self.stars_table.horizontalHeader().setStretchLastSection(True)
        self.stars_table.verticalHeader().setVisible(False)
        self.stars_table.setStyleSheet(
            "QTableWidget {border: 1px solid #FFD500; border-radius: 8px; color: #111;}"
            "QHeaderView::section {background-color: #FFF4B5; padding: 6px; font-weight: 600; color: #333;}"
        )

        layout.addWidget(info)
        layout.addSpacing(8)
        layout.addWidget(self.stars_table)
        layout.addStretch()

    def populate_data(self):
        bonus_rules = self.original_config.get("bonus_rules", [])
        self.bonus_table.setRowCount(len(bonus_rules))
        for row, rule in enumerate(bonus_rules):
            self.set_bonus_row(row, rule.get("min", 0), rule.get("max", 0), rule.get("value", 0))

        mix_rule_type = self.original_config.get("mix_rule_type", "team")
        index = self.rule_type_combo.findData(mix_rule_type)
        if index >= 0:
            self.rule_type_combo.setCurrentIndex(index)

        mix_rules = self.original_config.get("mix_rules", {})
        all_or_nothing = mix_rules.get("all_or_nothing", {})
        team_rules = mix_rules.get("team", {})

        self.min_mix_spin.setValue(all_or_nothing.get("min_mix", 40.0))
        self.all_bonus_spin.setValue(all_or_nothing.get("bonus_per_liter", 0.02))
        self.winner_bonus_spin.setValue(team_rules.get("winner_bonus_per_liter", 0.0225))
        self.loser_bonus_spin.setValue(team_rules.get("loser_bonus_per_liter", 0.02))

        employee_settings = self.original_config.get("employee_settings", {})
        employees = sorted(
            self.employee_data.values(),
            key=lambda e: e.get("display_name", "")
        )

        self.team_table.setRowCount(len(employees))
        self.stars_table.setRowCount(len(employees))
        for row, employee in enumerate(employees):
            display_name = employee.get("display_name", "")
            emp_id = employee.get("id")
            settings_entry = employee_settings.get(emp_id, {})
            team_value = settings_entry.get("team", "A")
            stars_value = settings_entry.get("stars", 0)

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
            stars_name_item.setFlags(stars_name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.stars_table.setItem(row, 0, stars_name_item)

            stars_input = QtWidgets.QLineEdit()
            stars_input.setValidator(QtGui.QIntValidator(0, 1000000, stars_input))
            stars_input.setText(str(stars_value))
            stars_input.setToolTip("Pontuação em estrelas (1 estrela = 1 ponto).")
            stars_input.setStyleSheet(self.line_edit_style())
            self.stars_table.setCellWidget(row, 1, stars_input)

    def set_bonus_row(self, row, min_value, max_value, bonus_value):
        min_spin = QtWidgets.QDoubleSpinBox()
        min_spin.setRange(0, 100)
        min_spin.setDecimals(2)
        min_spin.setValue(min_value)
        min_spin.setStyleSheet(self.spinbox_style())

        max_spin = QtWidgets.QDoubleSpinBox()
        max_spin.setRange(0, 100)
        max_spin.setDecimals(2)
        max_spin.setValue(max_value)
        max_spin.setStyleSheet(self.spinbox_style())

        bonus_spin = QtWidgets.QDoubleSpinBox()
        bonus_spin.setRange(0, 10)
        bonus_spin.setDecimals(4)
        bonus_spin.setValue(bonus_value)
        bonus_spin.setStyleSheet(self.spinbox_style())

        self.bonus_table.setCellWidget(row, 0, min_spin)
        self.bonus_table.setCellWidget(row, 1, max_spin)
        self.bonus_table.setCellWidget(row, 2, bonus_spin)

    def add_bonus_row(self):
        row = self.bonus_table.rowCount()
        self.bonus_table.insertRow(row)
        self.set_bonus_row(row, 0, 0, 0)

    def remove_bonus_row(self):
        row = self.bonus_table.currentRow()
        if row >= 0:
            self.bonus_table.removeRow(row)

    def handle_save(self):
        bonus_rules = []
        for row in range(self.bonus_table.rowCount()):
            min_spin = self.bonus_table.cellWidget(row, 0)
            max_spin = self.bonus_table.cellWidget(row, 1)
            bonus_spin = self.bonus_table.cellWidget(row, 2)
            min_value = min_spin.value()
            max_value = max_spin.value()
            if min_value > max_value:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Faixa inválida",
                    "O mix mínimo não pode ser maior que o mix máximo."
                )
                return
            bonus_rules.append({
                "min": min_value,
                "max": max_value,
                "value": bonus_spin.value()
            })

        employee_settings = copy.deepcopy(self.original_config.get("employee_settings", {}))
        for row in range(self.team_table.rowCount()):
            name_item = self.team_table.item(row, 0)
            combo = self.team_table.cellWidget(row, 1)
            if not name_item or not combo:
                continue
            display_name = name_item.text()
            emp_id = display_name.split(" - ")[0].strip()
            employee_settings.setdefault(emp_id, {})
            employee_settings[emp_id]["team"] = combo.currentData()

        for row in range(self.stars_table.rowCount()):
            name_item = self.stars_table.item(row, 0)
            stars_input = self.stars_table.cellWidget(row, 1)
            if not name_item or not stars_input:
                continue
            display_name = name_item.text()
            emp_id = display_name.split(" - ")[0].strip()
            employee_settings.setdefault(emp_id, {})
            try:
                stars_value = int(stars_input.text() or 0)
            except ValueError:
                stars_value = 0
            employee_settings[emp_id]["stars"] = stars_value

        self.original_config["bonus_rules"] = bonus_rules
        self.original_config["mix_rule_type"] = self.rule_type_combo.currentData()
        self.original_config["mix_rules"] = {
            "all_or_nothing": {
                "min_mix": self.min_mix_spin.value(),
                "bonus_per_liter": self.all_bonus_spin.value(),
            },
            "team": {
                "winner_bonus_per_liter": self.winner_bonus_spin.value(),
                "loser_bonus_per_liter": self.loser_bonus_spin.value(),
            },
        }
        self.original_config["employee_settings"] = employee_settings

        self.accept()

    def get_config(self):
        return self.original_config

    @staticmethod
    def spinbox_style():
        return (
            "QSpinBox, QDoubleSpinBox {padding: 4px; border: 1px solid #FFD500; border-radius: 6px;"
            "color: #111; background-color: #FFFFFF;}"
        )

    @staticmethod
    def combo_style():
        return (
            "QComboBox {padding: 4px; border: 1px solid #FFD500; border-radius: 6px;"
            "color: #111; background-color: #FFFFFF;}"
        )

    @staticmethod
    def line_edit_style():
        return (
            "QLineEdit {padding: 4px; border: 1px solid #FFD500; border-radius: 6px;"
            "color: #111; background-color: #FFFFFF;}"
        )


class BonusCalculator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mix V-Power - Calculadora de Bonificação")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QtGui.QIcon("icons/iconV.ico"))

        self.primary_color = "#FFFFFF"
        self.secondary_yellow = "#FFD500"
        self.secondary_red = "#ED1C24"

        self.config_file = "config.json"
        self.last_directory = os.getcwd()
        self.last_report_update = None
        self.employee_data = {}
        self.employees = []

        self.load_config()
        self.build_ui()
        self.setup_shortcuts()
        self.load_report()

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = DEFAULT_CONFIG.copy()

        self.config["bonus_rules"] = self.normalize_bonus_rules(
            self.config.get("bonus_rules", DEFAULT_CONFIG["bonus_rules"])
        )
        self.config.setdefault("mix_rule_type", "team")
        self.config.setdefault("mix_rules", DEFAULT_CONFIG["mix_rules"])
        self.config.setdefault("employee_settings", {})
        self.config.setdefault("search_history", [])
        self.config.setdefault("mix_history", {})
        self.config.setdefault("last_report_update", None)

        self.last_directory = self.config.get('last_directory', os.getcwd())
        self.search_history = self.config.get('search_history', [])
        self.mix_history = self.config.get('mix_history', {})

        last_update_str = self.config.get('last_report_update')
        if last_update_str:
            try:
                self.last_report_update = datetime.datetime.fromisoformat(last_update_str)
            except ValueError:
                self.last_report_update = None

    @staticmethod
    def normalize_bonus_rules(bonus_rules):
        default_rules = copy.deepcopy(DEFAULT_CONFIG["bonus_rules"])
        normalized = []
        for rule in bonus_rules:
            min_value = rule.get("min")
            max_value = rule.get("max")
            if min_value is None or max_value is None:
                continue
            if "winner" in rule or "loser" in rule:
                normalized.append({
                    "min": min_value,
                    "max": max_value,
                    "winner": rule.get("winner", 0.0),
                    "loser": rule.get("loser", 0.0),
                })
            else:
                value = rule.get("value", 0.0)
                normalized.append({
                    "min": min_value,
                    "max": max_value,
                    "winner": value,
                    "loser": value,
                })

        if not normalized:
            return default_rules

        return normalized

    def save_config(self):
        self.config["last_directory"] = self.last_directory
        self.config["search_history"] = self.search_history
        self.config["mix_history"] = self.mix_history
        self.config["last_report_update"] = (
            self.last_report_update.isoformat() if self.last_report_update else None
        )

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.stack)

    def setup_shortcuts(self):
        self.shortcut_escape = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), self)
        self.shortcut_escape.activated.connect(self.handle_escape)

        self.shortcut_copy = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self)
        self.shortcut_copy.activated.connect(self.copy_results_to_clipboard)

    def handle_escape(self):
        # Se estiver na tela de resultado, volta pro login; senão fecha o app
        current = self.stack.currentWidget()
        if current == self.result_page:
            self.return_to_login()
        else:
            self.close()

    def copy_results_to_clipboard(self):
        # Copia um resumo do resultado atual (se houver funcionário exibido)
        emp = self.employee_name_label.text().strip()
        if not emp:
            return

        texto = (
            f"{emp}\n"
            f"{self.mix_label.text()}\n"
            f"Time: {self.labels['time'].text()}\n"
            f"Comum: {self.labels['comum'].text()} L\n"
            f"V-Power: {self.labels['vpower'].text()} L\n"
            f"Total: {self.labels['total'].text()} L\n"
            f"Bônus/L: {self.labels['bonus_per_liter'].text()}\n"
            f"Total: {self.labels['bonus_total'].text()}\n"
            f"Relatório: {self.labels['update_time'].text()}\n"
        )

        QtWidgets.QApplication.clipboard().setText(texto)

    def build_login_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 50, 20, 20)
        layout.setSpacing(6)

        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("Logo_Vpower.png")
        logo.setPixmap(pixmap.scaledToWidth(260, QtCore.Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title = QtWidgets.QLabel("Mix V-Power")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 700; color: #ED1C24;")

        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setPlaceholderText("Código do funcionário")
        self.code_input.setFixedWidth(320)
        self.code_input.setStyleSheet(
            "padding: 10px; font-size: 18px; border: 2px solid #FFD500; border-radius: 10px;"
            "color: #111; background-color: #FFFFFF;"
        )
        self.code_input.returnPressed.connect(self.handle_login)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.login_button = QtWidgets.QPushButton("Entrar")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet(
            "background-color: #ED1C24; color: white; font-size: 18px; padding: 10px 30px;"
            "border-radius: 12px;"
        )

        self.refresh_button = QtWidgets.QToolButton()
        self.refresh_button.setIcon(QtGui.QIcon("icons/atualizar.png"))
        self.refresh_button.setIconSize(QtCore.QSize(32, 32))
        self.refresh_button.setToolTip("Atualizar relatório")
        self.refresh_button.setStyleSheet("background-color: transparent; border: none; padding: 8px;")
        self.refresh_button.clicked.connect(self.reload_report)

        self.refresh_spinner = QtWidgets.QProgressBar()
        self.refresh_spinner.setFixedWidth(120)
        self.refresh_spinner.setRange(0, 0)
        self.refresh_spinner.setVisible(False)
        self.refresh_spinner.setStyleSheet(
            "QProgressBar {border: 1px solid #FFD500; border-radius: 6px; text-align: center;}"
            "QProgressBar::chunk {background-color: #FFD500;}"
        )

        button_row.addWidget(self.login_button)
        button_row.addSpacing(20)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.refresh_spinner)

        settings_button = QtWidgets.QToolButton()
        settings_button.setIcon(QtGui.QIcon("icons/cog.ico"))
        settings_button.setIconSize(QtCore.QSize(24, 24))
        settings_button.setToolTip("Configurações")
        settings_button.setStyleSheet("background-color: transparent; border: none; padding: 6px;")
        settings_button.clicked.connect(self.open_settings)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #ED1C24;")

        center_layout = QtWidgets.QVBoxLayout()
        center_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(8)
        center_layout.addWidget(title)
        center_layout.addSpacing(8)
        center_layout.addWidget(self.code_input, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.addSpacing(8)
        center_layout.addWidget(logo)
        center_layout.addSpacing(8)
        center_layout.addLayout(button_row)
        center_layout.addSpacing(4)
        center_layout.addWidget(self.status_label)

        layout.addStretch()
        layout.addLayout(center_layout)
        layout.addStretch()
        layout.addWidget(
            settings_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom,
        )

        return widget

    def build_result_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.employee_name_label = QtWidgets.QLabel("")
        self.employee_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.employee_name_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #ED1C24;")

        self.mix_label = QtWidgets.QLabel("")
        self.mix_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mix_label.setStyleSheet("font-size: 40px; font-weight: 800; color: #ED1C24;")

        self.labels = {}

        info_container = QtWidgets.QFrame()
        info_container.setStyleSheet(
            "QFrame {background-color: #FFFDF4; border: 1px solid #FFD500; border-radius: 12px;}"
        )
        info_layout = QtWidgets.QVBoxLayout(info_container)
        info_layout.setContentsMargins(18, 16, 18, 16)
        info_layout.setSpacing(14)

        sections = [
            ("🏁 Resumo do time", [("Time", "time"), ("Mix do time (%)", "team_mix")]),
            ("⛽ Litros vendidos", [("Gasolina Comum (L)", "comum"), ("V-Power (L)", "vpower"), ("Total de litros (L)", "total")]),
            ("💰 Bonificação", [("Bonificação por litro", "bonus_per_liter"), ("Valor estimado", "bonus_total")]),
            ("⭐ Destaques", [("Estrelas", "stars"), ("Relatório atualizado", "update_time")]),
        ]

        for title, fields in sections:
            section_frame = QtWidgets.QFrame()
            section_frame.setStyleSheet(
                "QFrame {background-color: #FFFFFF; border: 1px solid #FFE17A; border-radius: 10px;}"
            )
            section_layout = QtWidgets.QVBoxLayout(section_frame)
            section_layout.setContentsMargins(14, 10, 14, 10)
            section_layout.setSpacing(6)

            section_title = QtWidgets.QLabel(title)
            section_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ED1C24;")
            section_layout.addWidget(section_title)

            for label, key in fields:
                row = QtWidgets.QHBoxLayout()
                name_label = QtWidgets.QLabel(label + ":")
                name_label.setStyleSheet("font-size: 13px; color: #444;")
                value_label = QtWidgets.QLabel("-")
                value_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #111;")
                row.addWidget(name_label)
                row.addStretch()
                row.addWidget(value_label)
                section_layout.addLayout(row)
                self.labels[key] = value_label

            info_layout.addWidget(section_frame)

        layout.addWidget(self.employee_name_label)
        layout.addWidget(self.mix_label)
        layout.addSpacing(20)
        layout.addWidget(info_container)
        layout.addStretch()

        back_button = QtWidgets.QPushButton("Voltar")
        back_button.clicked.connect(self.return_to_login)
        back_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 14px; padding: 6px 20px;"
            "border-radius: 10px;"
        )
        back_row = QtWidgets.QHBoxLayout()
        back_row.addStretch()
        back_row.addWidget(back_button)
        layout.addLayout(back_row)

        return widget

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
                "Arquivos de texto (*.txt);;Todos os arquivos (*.*)"
            )
        if not file_path:
            self.show_buffering(False)
            return

        self.last_directory = os.path.dirname(file_path)

        report_data = parsear_relatorio(file_path)
        if not report_data or not report_data['funcionarios']:
            self.show_buffering(False)
            QtWidgets.QMessageBox.warning(
                self,
                "Relatório inválido",
                "O relatório não é válido ou está vazio."
            )
            return

        self.employees = []
        self.employee_data = {}

        employee_settings = self.config.get("employee_settings", {})
        now = datetime.datetime.now().isoformat()

        for emp in report_data['funcionarios']:
            employee_id = str(emp['codigo'])
            employee_name = emp['nome']
            display_name = f"{employee_id} - {employee_name}"

            gasolina_comum = 0.0
            gasolina_vpower = 0.0

            for item in emp.get('itens', []):
                produto = item.get('produto', '').strip().upper()
                quantidade = item.get('quantidade', 0.0) or 0.0
                if produto == "GASOLINA C COMUM":
                    gasolina_comum += quantidade
                elif produto == "GASOLINA C COMUM ADITIVADA":
                    gasolina_vpower += quantidade

            total_quantity = gasolina_comum + gasolina_vpower
            mix = (gasolina_vpower / total_quantity * 100) if total_quantity > 0 else 0.0
            previous_mix = self.mix_history.get(employee_id, {}).get("mix")

            self.employee_data[employee_id] = {
                'id': employee_id,
                'name': employee_name,
                'display_name': display_name,
                'sales_count': emp['vendas'],
                'products': emp.get('itens', []),
                'total_quantity': total_quantity,
                'gasolina_comum': gasolina_comum,
                'gasolina_vpower': gasolina_vpower,
                'mix': mix,
                'previous_mix': previous_mix
            }
            self.employees.append(employee_id)

            if employee_id not in employee_settings:
                employee_settings[employee_id] = {"team": "A", "stars": 0}
            else:
                employee_settings[employee_id].setdefault("stars", 0)

            self.mix_history[employee_id] = {
                "name": display_name,
                "mix": mix,
                "timestamp": now
            }

        self.config["employee_settings"] = employee_settings
        self.last_report_update = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
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
                "Não foi possível encontrar o funcionário informado."
            )
            return

        employee = self.employee_data[code]
        self.add_to_search_history(employee['id'], employee['display_name'])
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
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        def on_fade_out():
            current_widget.setGraphicsEffect(None)
            self.stack.setCurrentIndex(target_index)
            new_widget = self.stack.currentWidget()
            effect_in = QtWidgets.QGraphicsOpacityEffect(new_widget)
            new_widget.setGraphicsEffect(effect_in)

            fade_in = QtCore.QPropertyAnimation(effect_in, b"opacity")
            fade_in.setDuration(200)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.finished.connect(lambda: new_widget.setGraphicsEffect(None))
            fade_in.start()
            self._fade_in_anim = fade_in

        fade_out.finished.connect(on_fade_out)
        fade_out.start()
        self._fade_out_anim = fade_out

    def show_employee_results(self, employee_id):
        employee_data = self.employee_data[employee_id]

        emp_id = employee_data['id']
        emp_settings = self.config.get('employee_settings', {}).get(emp_id, {"team": "A"})
        emp_team = emp_settings.get('team', 'A')

        if emp_team in ("OIL", "INACTIVE"):
            QtWidgets.QMessageBox.information(
                self,
                "Sem bonificação",
                "Este funcionário não participa do cálculo de bonificação."
            )
            return

        valid_emps = [
            emp for emp in self.employee_data.values()
            if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team')
            not in ("OIL", "INACTIVE")
        ]

        teams = {'A': [], 'B': []}
        for emp in valid_emps:
            team = self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team', 'A')
            if team.startswith('A'):
                teams['A'].append(emp)
            elif team.startswith('B'):
                teams['B'].append(emp)

        def calc_team_mix(team_emps):
            total_premium = sum(e['gasolina_vpower'] for e in team_emps)
            total = sum(e['total_quantity'] for e in team_emps)
            return (total_premium / total * 100) if total > 0 else 0.0

        mix_a = calc_team_mix(teams['A'])
        mix_b = calc_team_mix(teams['B'])

        total_quantity = employee_data['total_quantity']
        premium_quantity = employee_data['gasolina_vpower']
        mix_percentage = (premium_quantity / total_quantity * 100) if total_quantity > 0 else 0.0

        team_mix = mix_a if emp_team.startswith('A') else mix_b

        is_night = emp_team in ("A_NIGHT", "B_NIGHT")
        mix_rule_type = self.config.get("mix_rule_type", "team")
        mix_rules = self.config.get("mix_rules", {})
        all_or_nothing = mix_rules.get("all_or_nothing", {})

        if mix_rule_type == "all_or_nothing":
            min_mix = all_or_nothing.get("min_mix", 40.0)
            bonus_per_liter = all_or_nothing.get("bonus_per_liter", 0.0) if mix_percentage >= min_mix else 0.0
        else:
            bonus_per_liter = self.get_bonus_from_ranges(team_mix)

        if is_night:
            bonus_per_liter *= 0.7

        total_bonus = premium_quantity * bonus_per_liter

        base_team = 'A' if emp_team.startswith('A') else 'B'
        diurnos = [
            emp for emp in valid_emps
            if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team') == base_team
        ]
        avg_team_liters_display = (
            sum(emp['total_quantity'] for emp in diurnos) / len(diurnos)
            if diurnos else 0.0
        )

        mix_text = f"Mix: {self.format_brl(mix_percentage, 2)}%"
        mix_style = "font-size: 40px; font-weight: 800; color: #ED1C24;"
        self.employee_name_label.setText(employee_data['display_name'])
        self.mix_label.setText(mix_text)
        self.mix_label.setStyleSheet(mix_style)

        self.labels["time"].setText(
            emp_team.replace('_NIGHT', ' (Noturno)').replace('OIL', 'Troca de Óleo')
        )
        self.labels["team_mix"].setText(self.format_brl(team_mix, 2))
        self.labels["comum"].setText(self.format_brl(employee_data['gasolina_comum']))
        self.labels["vpower"].setText(self.format_brl(employee_data['gasolina_vpower']))
        self.labels["total"].setText(self.format_brl(total_quantity))
        self.labels["bonus_per_liter"].setText(self.format_brl_money(bonus_per_liter, decimals=3))
        self.labels["bonus_total"].setText(self.format_brl_money(total_bonus))
        self.labels["stars"].setText(str(emp_settings.get("stars", 0)))

        if self.last_report_update:
            update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
        else:
            update_time = "-"
        self.labels["update_time"].setText(update_time)

        rule_label = (
            "Tudo ou nada (mix individual)" if mix_rule_type == "all_or_nothing"
            else "Faixas por time"
        )
        tooltip = (
            f"Mix do time: {self.format_brl(team_mix, 2)}%\n"
            f"Média do time: {self.format_brl(avg_team_liters_display)} L\n"
            f"Regra aplicada: {rule_label}"
        )
        self.mix_label.setToolTip(tooltip)

    def get_bonus_from_ranges(self, mix_percentage):
        bonus_rules = self.config.get("bonus_rules", [])
        for rule in bonus_rules:
            min_value = rule.get("min", 0)
            max_value = rule.get("max", 0)
            if min_value <= mix_percentage <= max_value:
                return rule.get("value", 0.0)
        return 0.0

    def add_to_search_history(self, employee_code, employee_name):
        history_entry = {
            "employee_id": employee_code,
            "employee_name": employee_name,
            "timestamp": datetime.datetime.now().isoformat()
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
                self,
                "Senha incorreta",
                "A senha informada está incorreta."
            )
            return

        dialog = SettingsDialog(self, self.config, self.employee_data)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            self.save_config()

    @staticmethod
    def format_brl(value, decimals=3):
        return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @staticmethod
    def format_brl_money(value, decimals=2):
        return f'R$ {value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BonusCalculator()
    window.show()
    sys.exit(app.exec())

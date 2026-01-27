import json
import os
import re
import locale
import sys
import datetime

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
        {"min": 0, "max": 35, "value": 0.0},
        {"min": 35, "max": 40, "value": 0.01},
        {"min": 40, "max": 45, "value": 0.02},
        {"min": 45, "max": 50, "value": 0.03},
        {"min": 50, "max": 55, "value": 0.04},
        {"min": 55, "max": 60, "value": 0.05},
        {"min": 60, "max": 65, "value": 0.06},
        {"min": 65, "max": 70, "value": 0.07},
        {"min": 70, "max": 75, "value": 0.08},
        {"min": 75, "max": 80, "value": 0.09},
        {"min": 80, "max": 85, "value": 0.10},
        {"min": 85, "max": 90, "value": 0.11},
        {"min": 90, "max": 95, "value": 0.12},
        {"min": 95, "max": 100, "value": 0.13}
    ],
    "mix_rule_type": "team",
    "mix_rules": {
        "all_or_nothing": {
            "min_mix": 40.0,
            "bonus_per_liter": 0.02
        },
        "team": {
            "winner_bonus_per_liter": 0.0225,
            "loser_bonus_per_liter": 0.02
        }
    },
    "employee_settings": {},
    "search_history": [],
    "mix_history": {},
    "last_report_update": None
}


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

        self.config.setdefault("bonus_rules", DEFAULT_CONFIG["bonus_rules"])
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

    def build_login_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

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

        settings_button = QtWidgets.QPushButton("Configurações")
        settings_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 14px; padding: 6px 20px;"
            "border-radius: 10px;"
        )
        settings_button.clicked.connect(self.open_settings)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #ED1C24;")

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(logo)
        layout.addSpacing(20)
        layout.addWidget(self.code_input, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addLayout(button_row)
        layout.addSpacing(10)
        layout.addWidget(settings_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)

        return widget

    def build_result_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        top_row = QtWidgets.QHBoxLayout()
        back_button = QtWidgets.QPushButton("Voltar")
        back_button.clicked.connect(self.return_to_login)
        back_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 14px; padding: 6px 20px;"
            "border-radius: 10px;"
        )
        top_row.addWidget(back_button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()

        self.employee_name_label = QtWidgets.QLabel("")
        self.employee_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.employee_name_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #ED1C24;")

        self.mix_label = QtWidgets.QLabel("")
        self.mix_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mix_label.setStyleSheet("font-size: 40px; font-weight: 800; color: #ED1C24;")

        self.info_grid = QtWidgets.QGridLayout()
        self.info_grid.setHorizontalSpacing(20)
        self.info_grid.setVerticalSpacing(10)

        self.labels = {}
        fields = [
            ("Time", "time"),
            ("Gasolina Comum (L)", "comum"),
            ("V-Power (L)", "vpower"),
            ("Total de litros (L)", "total"),
            ("Bonificação por litro", "bonus_per_liter"),
            ("Valor estimado", "bonus_total"),
            ("Relatório atualizado", "update_time"),
        ]
        for row, (label, key) in enumerate(fields):
            name_label = QtWidgets.QLabel(label + ":")
            name_label.setStyleSheet("font-size: 14px; color: #333;")
            value_label = QtWidgets.QLabel("-")
            value_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #111;")
            self.labels[key] = value_label
            self.info_grid.addWidget(name_label, row, 0)
            self.info_grid.addWidget(value_label, row, 1)

        layout.addLayout(top_row)
        layout.addSpacing(20)
        layout.addWidget(self.employee_name_label)
        layout.addWidget(self.mix_label)
        layout.addSpacing(20)
        layout.addLayout(self.info_grid)
        layout.addStretch()

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
                employee_settings[employee_id] = {"team": "A"}

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

    def handle_escape(self):
        if self.stack.currentWidget() == self.result_page:
            self.return_to_login()
        else:
            self.close()

    def copy_results_to_clipboard(self):
        if self.stack.currentWidget() != self.result_page:
            return

        lines = [
            self.employee_name_label.text(),
            self.mix_label.text(),
            f"Time: {self.labels['time'].text()}",
            f"Gasolina Comum (L): {self.labels['comum'].text()}",
            f"V-Power (L): {self.labels['vpower'].text()}",
            f"Total de litros (L): {self.labels['total'].text()}",
            f"Bonificação por litro: {self.labels['bonus_per_liter'].text()}",
            f"Valor estimado: {self.labels['bonus_total'].text()}",
            f"Relatório atualizado: {self.labels['update_time'].text()}",
        ]

        QtWidgets.QApplication.clipboard().setText("\n".join(lines))

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

        winner = None
        loser = None
        if mix_a > mix_b:
            winner = 'A'
            loser = 'B'
        elif mix_b > mix_a:
            winner = 'B'
            loser = 'A'

        total_quantity = employee_data['total_quantity']
        premium_quantity = employee_data['gasolina_vpower']
        mix_percentage = (premium_quantity / total_quantity * 100) if total_quantity > 0 else 0.0

        team_mix = mix_a if emp_team.startswith('A') else mix_b

        is_night = emp_team in ("A_NIGHT", "B_NIGHT")
        is_winner = (winner is not None and emp_team.startswith(winner))
        is_loser = (loser is not None and emp_team.startswith(loser))

        mix_rule_type = self.config.get("mix_rule_type", "team")
        mix_rules = self.config.get("mix_rules", {})
        all_or_nothing = mix_rules.get("all_or_nothing", {})
        team_rules = mix_rules.get("team", {})

        if mix_rule_type == "all_or_nothing":
            min_mix = all_or_nothing.get("min_mix", 40.0)
            bonus_per_liter = all_or_nothing.get("bonus_per_liter", 0.0) if mix_percentage >= min_mix else 0.0
        else:
            winner_bonus = team_rules.get("winner_bonus_per_liter", 0.0)
            loser_bonus = team_rules.get("loser_bonus_per_liter", 0.0)
            if is_winner:
                bonus_per_liter = winner_bonus
            elif is_loser:
                bonus_per_liter = loser_bonus
            else:
                bonus_per_liter = loser_bonus if winner is None else 0.0

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

        comparison = self.get_mix_comparison(employee_data)
        mix_text = f"Mix: {self.format_brl(mix_percentage, 2)}%"
        mix_style = "font-size: 40px; font-weight: 800; color: #ED1C24;"
        if comparison:
            if comparison["status"] == "up":
                mix_text += f" ↗️ (+{self.format_brl(comparison['difference'], 2)}%)"
                mix_style = "font-size: 40px; font-weight: 800; color: #228B22;"
            elif comparison["status"] == "down":
                mix_text += f" ↘️ (-{self.format_brl(comparison['difference'], 2)}%)"
                mix_style = "font-size: 40px; font-weight: 800; color: #DC143C;"
            else:
                mix_text += " ➡️"
                mix_style = "font-size: 40px; font-weight: 800; color: #4169E1;"
        else:
            mix_text += " 🆕"
            mix_style = "font-size: 40px; font-weight: 800; color: #FF8C00;"

        self.employee_name_label.setText(employee_data['display_name'])
        self.mix_label.setText(mix_text)
        self.mix_label.setStyleSheet(mix_style)

        self.labels["time"].setText(
            emp_team.replace('_NIGHT', ' (Noturno)').replace('OIL', 'Troca de Óleo')
        )
        self.labels["comum"].setText(self.format_brl(employee_data['gasolina_comum']))
        self.labels["vpower"].setText(self.format_brl(employee_data['gasolina_vpower']))
        self.labels["total"].setText(self.format_brl(total_quantity))
        self.labels["bonus_per_liter"].setText(self.format_brl_money(bonus_per_liter))
        self.labels["bonus_total"].setText(self.format_brl_money(total_bonus))

        if self.last_report_update:
            update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
        else:
            update_time = "-"
        self.labels["update_time"].setText(update_time)

        rule_label = (
            "Tudo ou nada (mix individual)" if mix_rule_type == "all_or_nothing"
            else "Por time (vencedor x perdedor)"
        )
        tooltip = (
            f"Mix do time: {self.format_brl(team_mix, 2)}%\n"
            f"Média do time: {self.format_brl(avg_team_liters_display)} L\n"
            f"Regra aplicada: {rule_label}"
        )
        self.mix_label.setToolTip(tooltip)

    def get_mix_comparison(self, employee_data):
        previous_mix = employee_data.get("previous_mix")
        if previous_mix is None:
            return None

        current_mix = employee_data.get("mix", 0.0)
        difference = current_mix - previous_mix
        if abs(difference) < 0.01:
            status = "same"
        elif difference > 0:
            status = "up"
        else:
            status = "down"

        return {
            "status": status,
            "difference": abs(difference)
        }

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
        self.save_config()
        config_path = os.path.abspath(self.config_file)

        message = QtWidgets.QMessageBox(self)
        message.setWindowTitle("Configurações")
        message.setIcon(QtWidgets.QMessageBox.Icon.Information)
        message.setText(
            "As configurações são salvas no arquivo config.json.\n"
            "Clique em “Abrir config” para editar manualmente."
        )
        open_button = message.addButton("Abrir config", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        message.addButton("Fechar", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        message.exec()

        if message.clickedButton() == open_button:
            opened = QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(config_path)
            )
            if not opened:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Não foi possível abrir",
                    f"Não foi possível abrir o arquivo:\n{config_path}"
                )

    @staticmethod
    def format_brl(value, decimals=3):
        return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @staticmethod
    def format_brl_money(value):
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BonusCalculator()
    window.show()
    sys.exit(app.exec())

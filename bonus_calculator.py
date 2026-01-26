import json
import os
import re
import sys
import datetime

from PySide6 import QtCore, QtGui, QtWidgets


# Attempt to set Brazilian locale for number formatting
try:
    import locale

    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except Exception:
    pass


def converter_numero_brasileiro(valor: str) -> float:
    """
    Converte número no formato brasileiro (1.234,567) para float.

    Args:
        valor: String com número no formato brasileiro

    Returns:
        float: Número convertido
    """
    if not valor or not valor.strip():
        return 0.0

    # Remove espaços e converte vírgula para ponto
    valor = valor.strip().replace('.', '').replace(',', '.')

    try:
        return float(valor)
    except ValueError:
        return 0.0


def extrair_cabecalho(linhas):
    """
    Extrai informações do cabeçalho do relatório.
    Identifica linhas por palavras-chave semânticas.

    Args:
        linhas: Lista de linhas do arquivo

    Returns:
        dict: Dicionário com informações do cabeçalho
    """
    header = {}

    for linha in linhas:
        linha = linha.strip()

        # Ignora linhas vazias ou de separação
        if not linha or linha.startswith('+') or linha.startswith('-'):
            continue

        # Extrai Empresa
        match = re.search(r'Empresa:\s*(.+?)\s*\|\s*$', linha, re.IGNORECASE)
        if match:
            header['empresa'] = match.group(1).strip()

        # Extrai Período
        match = re.search(r'Período:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['periodo'] = match.group(1).strip()

        # Extrai Modo
        match = re.search(r'Modo:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['modo'] = match.group(1).strip()

        # Extrai Agrupar
        match = re.search(r'Agrupar:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['agrupar'] = match.group(1).strip()

        # Extrai Ordenar
        match = re.search(r'Ordenar:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['ordenar'] = match.group(1).strip()

        # Extrai Produtividade
        match = re.search(r'Produtividade:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['produtividade'] = match.group(1).strip()

        # Extrai Grupo empresa
        match = re.search(r'Grupo empresa:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['grupo_empresa'] = match.group(1).strip()

        # Extrai Grupo produto
        match = re.search(r'Grupo produto:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['grupo_produto'] = match.group(1).strip()

        # Extrai Exibir
        match = re.search(r'Exibir:\s*(.+)', linha, re.IGNORECASE)
        if match:
            header['exibir'] = match.group(1).strip()

        # Para quando encontrar a primeira linha de tabela (início dos funcionários)
        if 'Funcionário:' in linha and 'Vendas:' in linha:
            break

    return header


def parsear_linha_item(linha):
    """
    Parseia uma linha de item da tabela de produtos.

    Args:
        linha: Linha do arquivo contendo dados do item

    Returns:
        dict ou None: Dicionário com dados do item ou None se não for uma linha válida
    """
    # Ignora linhas de separação ou cabeçalho
    if not linha.strip() or linha.strip().startswith('+') or 'Código' in linha or 'Produto' in linha:
        return None

    # Verifica se é uma linha de item (começa e termina com |)
    if not linha.strip().startswith('|') or not linha.strip().endswith('|'):
        return None

    # Verifica se é linha de total do vendedor
    if 'Total do vendedor' in linha:
        return None

    # Divide pelos separadores |
    campos = [campo.strip() for campo in linha.split('|')]

    # Remove primeiro e último elemento (vazios devido ao | inicial e final)
    campos = campos[1:-1]

    # Deve ter exatamente 7 campos
    if len(campos) != 7:
        return None

    try:
        item = {
            'codigo': int(campos[0]) if campos[0] else 0,
            'produto': campos[1],
            'fornecedor': campos[2],
            'quantidade': converter_numero_brasileiro(campos[3]),
            'unidade': campos[4],
            'valor': converter_numero_brasileiro(campos[5]),
            'percentual': converter_numero_brasileiro(campos[6])
        }
        return item
    except (ValueError, IndexError):
        return None


def parsear_total_funcionario(linha):
    """
    Extrai informações do total do funcionário.

    Args:
        linha: Linha contendo o total do vendedor

    Returns:
        dict ou None: Dicionário com totais ou None se não for uma linha válida
    """
    if 'Total do vendedor e participação geral nas vendas' not in linha:
        return None

    # Divide pelos separadores |
    campos = [campo.strip() for campo in linha.split('|')]

    # Remove primeiro e último elemento
    campos = campos[1:-1]

    # A linha de total tem a estrutura: texto | | quantidade | | valor | percentual
    # Então temos: [texto, '', quantidade, '', valor, percentual]
    if len(campos) < 6:
        return None

    try:
        # Campos estão nas posições: 2 (quantidade), 4 (valor), 5 (percentual)
        total = {
            'quantidade': converter_numero_brasileiro(campos[2]),
            'valor': converter_numero_brasileiro(campos[4]),
            'percentual': converter_numero_brasileiro(campos[5])
        }
        return total
    except (ValueError, IndexError):
        return None


def extrair_funcionarios(linhas):
    """
    Extrai todos os blocos de funcionários e seus itens vendidos.

    Args:
        linhas: Lista de linhas do arquivo

    Returns:
        list: Lista de dicionários com dados dos funcionários
    """
    funcionarios = []
    funcionario_atual = None
    itens_atual = []

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        # Detecta início de novo funcionário
        match = re.search(r'Funcionário:\s*(\d+)\s*-\s*(.+?)\s+Vendas:\s*(\d+)', linha)
        if match:
            # Salva funcionário anterior se existir
            if funcionario_atual:
                funcionario_atual['itens'] = itens_atual
                funcionarios.append(funcionario_atual)

            # Inicia novo funcionário
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

        # Se estamos dentro de um bloco de funcionário
        if funcionario_atual:
            # Tenta parsear como item
            item = parsear_linha_item(linha)
            if item:
                itens_atual.append(item)

            # Tenta parsear como total do funcionário
            total = parsear_total_funcionario(linha)
            if total:
                funcionario_atual['total'] = total
                # Não resetamos ainda, aguardamos próximo funcionário ou fim

        i += 1

    # Adiciona último funcionário se existir
    if funcionario_atual:
        funcionario_atual['itens'] = itens_atual
        funcionarios.append(funcionario_atual)

    return funcionarios


def extrair_totais_gerais(linhas):
    """
    Extrai totais gerais do relatório.

    Args:
        linhas: Lista de linhas do arquivo

    Returns:
        dict: Dicionário com totais gerais
    """
    totais = {}

    # Procura pelas linhas de totais gerais
    for linha in linhas:
        # Procura por "Total geral de vendas no período"
        if 'Total geral de vendas no período' in linha:
            campos = [campo.strip() for campo in linha.split('|')]
            campos = campos[1:-1]  # Remove primeiro e último (vazios)

            # A estrutura é: texto | quantidade | | valor |
            # Então campos[1] = quantidade, campos[3] = valor
            if len(campos) >= 4:
                totais['quantidade'] = converter_numero_brasileiro(campos[1])
                totais['valor'] = converter_numero_brasileiro(campos[3])
            break

    # Se não encontrou "Total geral", tenta "Total de vendas da empresa"
    if not totais:
        for linha in linhas:
            if 'Total de vendas da empresa' in linha:
                campos = [campo.strip() for campo in linha.split('|')]
                campos = campos[1:-1]

                # A estrutura é: texto | quantidade | | valor | percentual
                if len(campos) >= 3:
                    totais['quantidade'] = converter_numero_brasileiro(campos[2])
                    totais['valor'] = converter_numero_brasileiro(campos[3])
                break

    return totais


def parsear_relatorio(caminho_arquivo: str):
    """
    Função principal que parseia o arquivo de relatório completo.

    Args:
        caminho_arquivo: Caminho para o arquivo relatorio.txt

    Returns:
        dict: Dicionário estruturado com todos os dados parseados
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        with open(caminho_arquivo, 'r', encoding='latin1') as f:
            linhas = f.readlines()

    # Extrai cabeçalho
    header = extrair_cabecalho(linhas)

    # Extrai funcionários
    funcionarios = extrair_funcionarios(linhas)

    # Extrai totais gerais
    totais_gerais = extrair_totais_gerais(linhas)

    resultado = {
        'header': header,
        'funcionarios': funcionarios,
        'totaisGerais': totais_gerais
    }

    return resultado


def format_brl(value, decimals=2):
    return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def format_brl_money(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


class MixVpowerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mix V-Power - Calculadora de Bonificação")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QtGui.QIcon("icons/iconV.ico"))

        self.primary_color = "#FFFFFF"

        self.config_file = "config.json"
        self.last_directory = os.getcwd()
        self.last_report_update = None
        self.employee_data = {}
        self.employees = []

        self.load_config()
        self.build_ui()
        self.load_report()

    def load_config(self):
        default_config = {
            "mix_rule_type": "team",
            "mix_rules": {
                "all_or_nothing": {"min_mix": 40.0, "bonus_per_liter": 0.02},
                "team": {"winner_bonus_per_liter": 0.0225, "loser_bonus_per_liter": 0.02}
            },
            "employee_settings": {}
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                self.config = default_config
        else:
            self.config = default_config
        self.config.setdefault("mix_rule_type", "team")
        self.config.setdefault("mix_rules", default_config["mix_rules"])
        self.config.setdefault("employee_settings", {})

    def save_config(self):
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
        title.setStyleSheet(
            "font-size: 32px; font-weight: 700; color: #ED1C24;"
        )

        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setPlaceholderText("Código do funcionário")
        self.code_input.setFixedWidth(320)
        self.code_input.setStyleSheet(
            "padding: 10px; font-size: 18px; border: 2px solid #FFD500; border-radius: 10px;"
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
        self.refresh_button.setStyleSheet(
            "background-color: transparent; border: none; padding: 8px;"
        )
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

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #ED1C24;")

        layout.addWidget(logo)
        layout.addSpacing(10)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.code_input, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addLayout(button_row)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)

        return widget

    def build_result_page(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        top_row = QtWidgets.QHBoxLayout()
        back_button = QtWidgets.QPushButton("Voltar")
        back_button.clicked.connect(lambda: self.switch_page(self.login_page))
        back_button.setStyleSheet(
            "background-color: #FFD500; color: #ED1C24; font-size: 14px; padding: 6px 20px;"
            "border-radius: 10px;"
        )
        top_row.addWidget(back_button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()

        self.employee_name_label = QtWidgets.QLabel("")
        self.employee_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.employee_name_label.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #ED1C24;"
        )

        self.mix_label = QtWidgets.QLabel("")
        self.mix_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mix_label.setStyleSheet(
            "font-size: 40px; font-weight: 800; color: #ED1C24;"
        )

        self.info_grid = QtWidgets.QGridLayout()
        self.info_grid.setHorizontalSpacing(20)
        self.info_grid.setVerticalSpacing(10)

        self.labels = {}
        fields = [
            ("Time", "time"),
            ("Gasolina Comum (L)", "comum"),
            ("V-Power (L)", "vpower"),
            ("Mix do time", "team_mix"),
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
        if self.employees:
            update_info = ""
            if self.last_report_update:
                update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
                update_info = f" | 🕒 Atualizado em {update_time}"
            self.status_label.setText(f"📊 {len(self.employees)} funcionários carregados{update_info}")
        else:
            self.status_label.setText("⚠️ Nenhum relatório carregado")

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
            QtWidgets.QMessageBox.critical(self, "Erro", "O relatório não é válido ou está vazio.")
            return

        self.employees = []
        self.employee_data = {}

        employee_settings = self.config.get("employee_settings", {})
        settings_updated = False

        for emp in report_data['funcionarios']:
            employee_id = str(emp['codigo'])
            employee_name = f"{employee_id} - {emp['nome']}"
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

            emp_data = {
                'id': employee_id,
                'name': emp['nome'],
                'sales_count': emp['vendas'],
                'total_quantity': total_quantity,
                'gasolina_comum': gasolina_comum,
                'gasolina_vpower': gasolina_vpower,
                'mix': mix
            }

            self.employee_data[employee_name] = emp_data
            self.employees.append(employee_name)

            if employee_id not in employee_settings:
                employee_settings[employee_id] = {"team": "A"}
                settings_updated = True

        if settings_updated:
            self.config["employee_settings"] = employee_settings
            self.save_config()

        file_mod_time = os.path.getmtime(file_path)
        self.last_report_update = datetime.datetime.fromtimestamp(file_mod_time)
        self.update_status()
        self.show_buffering(False)

    def reload_report(self):
        self.load_report()

    def handle_login(self):
        code = self.code_input.text().strip()
        if not code:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Informe o código do funcionário.")
            return

        employee_name = None
        for emp_name in self.employees:
            if emp_name.startswith(code + " -"):
                employee_name = emp_name
                break

        if not employee_name:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Funcionário não encontrado.")
            return

        self.show_employee_results(employee_name)
        self.switch_page(self.result_page)

    def switch_page(self, target):
        current = self.stack.currentWidget()
        if current == target:
            return

        target_index = self.stack.indexOf(target)
        self.fade_transition(target_index)

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

    def show_employee_results(self, employee_name):
        employee_data = self.employee_data[employee_name]
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
        mix_percentage = (premium_quantity / total_quantity) * 100 if total_quantity > 0 else 0.0

        team_mix = mix_a if emp_team.startswith('A') else mix_b

        is_night = emp_team in ("A_NIGHT", "B_NIGHT")
        is_winner = winner is not None and emp_team.startswith(winner)
        is_loser = loser is not None and emp_team.startswith(loser)

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

        self.employee_name_label.setText(employee_name)
        self.mix_label.setText(f"{format_brl(mix_percentage, 2)}%")

        update_time = "-"
        if self.last_report_update:
            update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")

        self.labels["time"].setText(emp_team.replace('_NIGHT', ' (Noturno)').replace('OIL', 'Troca de Óleo'))
        self.labels["comum"].setText(format_brl(employee_data['gasolina_comum']))
        self.labels["vpower"].setText(format_brl(employee_data['gasolina_vpower']))
        self.labels["team_mix"].setText(f"{format_brl(team_mix, 2)}%")
        self.labels["total"].setText(format_brl(total_quantity))
        self.labels["bonus_per_liter"].setText(format_brl_money(bonus_per_liter))
        self.labels["bonus_total"].setText(format_brl_money(total_bonus))
        self.labels["update_time"].setText(update_time)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MixVpowerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

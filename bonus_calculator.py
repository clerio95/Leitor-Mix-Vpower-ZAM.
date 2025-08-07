import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import re
from decimal import Decimal, InvalidOperation
import locale
import sys
import ctypes
from PIL import Image, ImageTk
from tkinter import Button as TkButton
from tkinter import simpledialog
import datetime

class ToolTip:
    """Simple tooltip class for widgets"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#FFFFDD", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()
    
    def on_leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Hide terminal window on Windows
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Attempt to set Brazilian locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    print("Warning: pt_BR.UTF-8 locale not available, using fallback number parsing.")

def parse_brazilian_number(value_str):
    if not value_str:
        return None
    try:
        # Remove any whitespace and replace comma with dot
        value_str = value_str.strip().replace('.', '').replace(',', '.')
        return float(value_str)
    except (ValueError, InvalidOperation):
        return None

def test_product_matching():
    """Test function to verify product name matching logic"""
    test_products = [
        "DIESEL B S-10 ADITIVADO",
        "ETANOL HIDRATADO COMUM ADITIVADO", 
        "GASOLINA C COMUM ADITIVADA",
        "GASOLINA C COMUM",
        "DIESEL S-10 EVOLUX",  # Old name
        "ETANOL ADITIVADO SHELL V-POWER",  # Old name
        "GASOLINA ADITIVADA V-POWER",  # Old name
        "GASOLINA COMUM"  # Old name
    ]
    
    print("Testing product name matching:")
    for product in test_products:
        product_upper = product.upper()
        if ('ETANOL' in product_upper and 'ADITIVADO' in product_upper):
            print(f"✓ {product} -> etanol_vpower")
        elif ('GASOLINA' in product_upper and 'ADITIVADA' in product_upper):
            print(f"✓ {product} -> gasolina_vpower")
        elif ('GASOLINA' in product_upper and 'COMUM' in product_upper and 'ADITIVADA' not in product_upper):
            print(f"✓ {product} -> gasolina_comum")
        elif 'DIESEL' in product_upper:
            print(f"- {product} -> ignored (diesel)")
        else:
            print(f"✗ {product} -> UNMATCHED!")
    print()

def parse_relatorio(file_path):
    print(f"Loading report: {file_path}")
    
    # Tentar abrir com UTF-8, fallback para latin1
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = [line.rstrip('\r\n') for line in file.readlines()]
    except UnicodeDecodeError:
        print("UTF-8 encoding failed, trying latin1...")
        with open(file_path, 'r', encoding='latin1') as file:
            lines = [line.rstrip('\r\n') for line in file.readlines()]

    report_data = {
        'header': {},
        'employees': [],
        'totals': {}
    }

    current_employee = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Identificar linha de funcionário
        employee_match = re.match(r'\|\s*Funcionário:\s*(\d+)\s*-\s*([^|]+?)\s+Vendas:\s*(\d+)\s*\|', line)
        if employee_match:
            if current_employee:
                # Finalizar o funcionário anterior
                report_data['employees'].append(current_employee)
            
            # Iniciar novo funcionário
            employee_id, employee_name, sales_count = employee_match.groups()
            current_employee = {
                'id': employee_id.strip(),
                'name': employee_name.strip(),
                'sales_count': int(sales_count),
                'products': [],
                'total_quantity': 0.0,
                'total_value': 0.0,
                'participation': 0.0,
                'gasolina_comum': 0.0,
                'gasolina_vpower': 0.0,
                'etanol_vpower': 0.0
            }
            print(f"Found employee: {employee_name}")
            i += 1
            continue
        
        # Identificar linha de produto
        if current_employee and re.match(r'\|\s*\d+\s*\|', line):
            # Dividir a linha, mantendo todos os campos, mesmo os vazios
            parts = line.split('|')
            # Debug: Processing product line
            
            if len(parts) >= 7:  # Adjusted to be more flexible
                # Try to identify the correct column indices
                code = parts[1].strip() if len(parts) > 1 else ""
                product_name = parts[2].strip().upper() if len(parts) > 2 else ""
                
                # Find quantity and value columns (they should contain numbers)
                quantity_str = ""
                value_str = ""
                
                # Look for quantity and value in the remaining columns
                for idx in range(3, len(parts)):
                    part = parts[idx].strip()
                    if part and re.match(r'[\d.,]+', part):
                        if not quantity_str:
                            quantity_str = part
                        elif not value_str:
                            value_str = part
                            break
                
                # Debug: Product details parsed
                
                quantity = parse_brazilian_number(quantity_str)
                value = parse_brazilian_number(value_str)
                
                if quantity is not None:
                    product_info = {
                        'code': code,
                        'name': product_name,
                        'quantity': quantity,
                        'value': value if value is not None else 0.0
                    }
                    current_employee['products'].append(product_info)
                    
                    # Mapear produtos para os campos correspondentes
                    # More flexible product name matching to handle variations
                    product_matched = False
                    
                    # Check for Etanol Aditivado (V-Power equivalent)
                    if ('ETANOL' in product_name and 'ADITIVADO' in product_name) or \
                       ('ETANOL HIDRATADO COMUM ADITIVADO' in product_name) or \
                       ('ETANOL ADITIVADO SHELL V-POWER' in product_name):
                        current_employee['etanol_vpower'] += quantity  # Use += to handle multiple lines
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        # Accumulated etanol_vpower
                        product_matched = True
                    
                    # Check for Gasolina Aditivada (V-Power equivalent)
                    elif ('GASOLINA' in product_name and 'ADITIVADA' in product_name) or \
                         ('GASOLINA C COMUM ADITIVADA' in product_name) or \
                         ('GASOLINA ADITIVADA V-POWER' in product_name):
                        current_employee['gasolina_vpower'] += quantity  # Use += to handle multiple lines
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        # Accumulated gasolina_vpower
                        product_matched = True
                    
                    # Check for Gasolina Comum (regular gasoline)
                    elif ('GASOLINA' in product_name and 'COMUM' in product_name and 'ADITIVADA' not in product_name) or \
                         ('GASOLINA C COMUM' in product_name and 'ADITIVADA' not in product_name):
                        current_employee['gasolina_comum'] += quantity  # Somar, caso haja múltiplas linhas
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        # Accumulated gasolina_comum
                        product_matched = True
                    
                    # Log unmatched products for debugging
                    if not product_matched and 'DIESEL' not in product_name:
                        print(f"Warning: Unmatched product: {product_name}")
                    
                    # Diesel é ignorado conforme especificado
                    
            i += 1
            continue
        
        # Identificar linha de total do funcionário
        if current_employee and 'Total do vendedor' in line:
            # Found total line for employee
            i += 1
            continue
        
        i += 1
    
    # Adicionar o último funcionário, se existir
    if current_employee:
        report_data['employees'].append(current_employee)
    
    print(f"Successfully loaded {len(report_data['employees'])} employees")
    
    return report_data

class BonusCalculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Mix V-Power - Calculadora de Bonificação")
        self.window.geometry("800x600")
        
        # Set minimum window size
        self.window.minsize(600, 400)
        
        # Initialize search history and mix history
        self.search_history = []
        self.mix_history = {}  # Store previous mix percentages for comparison
        # Definir ícone do programa
        try:
            self.window.iconbitmap("icons/iconV.ico")
        except Exception as e:
            print(f"Erro ao definir ícone: {e}")
        # Configurar cores Shell V-Power
        self.shell_red = '#ED1C24'
        self.shell_yellow = '#FFD500'
        self.shell_white = '#FFFFFF'
        self.shell_bg = self.shell_white
        self.shell_fg = self.shell_red
        self.window.configure(bg=self.shell_bg)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme as base
        
        # Estilos com base nas cores Shell
        self.style.configure("TFrame", background=self.shell_bg)
        self.style.configure("TLabel", background=self.shell_bg, foreground=self.shell_fg, font=('Roboto', 14))
        self.style.configure("Title.TLabel", background=self.shell_bg, foreground=self.shell_red, font=('Roboto', 36, 'bold'))
        self.style.configure("Result.TLabel", background=self.shell_bg, foreground=self.shell_fg, font=('Roboto', 16))
        self.style.configure("Mix.TLabel", background=self.shell_bg, foreground=self.shell_red, font=('Roboto', 20, 'bold'))
        self.style.configure("TButton", 
                           background=self.shell_red, 
                           foreground=self.shell_white,
                           font=('Roboto', 14),
                           padding=10,
                           borderwidth=0,
                           relief="flat",
                           focuscolor="none")  # Remove focus outline
        
        # Disable hover effects to prevent flashing
        self.style.map("TButton",
                      background=[('active', self.shell_red),    # Keep same color on hover
                                ('pressed', self.shell_red)],     # Keep same color when pressed
                      foreground=[('active', self.shell_white),
                                ('pressed', self.shell_white)],
                      relief=[('pressed', 'flat'),
                             ('active', 'flat')])
        
        self.style.configure("Cog.TButton",
                           background="#FFFFFF",  # Branco
                           foreground="black",
                           borderwidth=0,
                           relief="flat",
                           focuscolor="none")
        
        # Disable cog button hover effects
        self.style.map("Cog.TButton",
                      background=[('active', '#FFFFFF'),    # Keep same white background
                                ('pressed', '#FFFFFF')],     # Keep same white background
                      foreground=[('active', 'black'),
                                ('pressed', 'black')],
                      relief=[('pressed', 'flat'),
                             ('active', 'flat')])
        
        self.style.configure("Update.TButton", 
                           background=self.shell_red, 
                           foreground=self.shell_white, 
                           font=('Roboto', 14, 'bold'), 
                           padding=10, 
                           relief="flat",
                           focuscolor="none")
        
        # Disable Update button hover effects too
        self.style.map("Update.TButton", 
                      background=[('active', self.shell_red),    # Keep same red background
                                ('pressed', self.shell_red)],     # Keep same red background
                      foreground=[('active', self.shell_white),
                                ('pressed', self.shell_white)])
        # Estilo para botão refresh só ícone, sem fundo/borda
        self.style.configure("Icon.TButton", 
                           background=self.shell_bg, 
                           foreground=self.shell_fg, 
                           font=('Roboto', 28, 'bold'), 
                           borderwidth=0, 
                           relief="flat", 
                           padding=0,
                           focuscolor="none")
        
        # Disable icon button hover effects completely
        self.style.map("Icon.TButton",
                      background=[('active', self.shell_bg),  # Keep same background
                                ('pressed', self.shell_bg)],
                      foreground=[('active', self.shell_fg),  # Keep same text color
                                ('pressed', self.shell_fg)],
                      relief=[('pressed', 'flat'),
                             ('active', 'flat')])
        
        self.employee_code = tk.StringVar()  # Substitui username por employee_code
        self.employees = []
        self.last_report_update = None  # Track when the report was last loaded
        self.search_history = []  # Track search history
        
        # Load last directory
        self.config_file = "config.json"
        self.load_config()
        
        # Create login widgets
        self.create_login_widgets()
        
        # Load report
        self.load_report()
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.last_directory = config.get('last_directory', os.getcwd())
                self.config = config
                self.search_history = config.get('search_history', [])
                self.mix_history = config.get('mix_history', {})
                
                # Load last report update time
                last_update_str = config.get('last_report_update')
                if last_update_str:
                    try:
                        import datetime
                        self.last_report_update = datetime.datetime.fromisoformat(last_update_str)
                    except:
                        self.last_report_update = None
                else:
                    self.last_report_update = None
                
                # Clean up old search history format
                self.migrate_search_history()
                # Configuration loaded successfully
        except (FileNotFoundError, json.JSONDecodeError):
            # Default configuration
            self.config = {
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
                "employee_settings": {},  # Include employee_settings in default config
                "search_history": [],  # Add search history for admin access
                "mix_history": {},  # Add mix history for comparison
                "last_report_update": None  # Track when report was last updated
            }
            self.last_directory = os.getcwd()
            self.search_history = []
            self.mix_history = {}
            self.save_config()
    
    def save_config(self):
        config = {
            "bonus_rules": self.config["bonus_rules"],
            "last_directory": self.last_directory,
            "employee_settings": self.config.get("employee_settings", {}),
            "search_history": self.search_history,
            "mix_history": self.mix_history,
            "last_report_update": self.last_report_update.isoformat() if self.last_report_update else None
        }
        # Saving configuration
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def create_login_widgets(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Não usar marca d'água, logo será exibida abaixo do botão Entrar
        main_frame = ttk.Frame(self.window, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        login_frame = ttk.Frame(main_frame, padding="20")
        login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        login_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(login_frame, text="Mix V-Power", style="Title.TLabel").grid(row=0, column=0, pady=(0, 40))
        ttk.Label(login_frame, text="Código do Funcionário:", style="TLabel").grid(row=1, column=0, pady=10)
        code_entry = ttk.Entry(login_frame, textvariable=self.employee_code, width=30, font=('Roboto', 20))
        code_entry.grid(row=2, column=0, pady=(0, 30))
        
        # Add Enter key binding and focus
        code_entry.bind('<Return>', lambda event: self.login())
        code_entry.focus_set()  # Set focus to the entry field
        
        # Add input validation and visual feedback
        def on_code_change(*args):
            try:
                if code_entry.winfo_exists():
                    code = self.employee_code.get().strip()
                    if code and code.isdigit():
                        code_entry.configure(style="Valid.TEntry")
                    elif code:
                        code_entry.configure(style="Invalid.TEntry")
                    else:
                        code_entry.configure(style="TEntry")
            except:
                pass  # Widget may have been destroyed
        
        # Store the trace id so we can remove it later
        self.trace_id = self.employee_code.trace('w', on_code_change)
        
        # Configure entry styles for validation feedback
        self.style.configure("Valid.TEntry", fieldbackground="#E8F5E8")
        self.style.configure("Invalid.TEntry", fieldbackground="#FFE8E8")
        
        # Add status bar with helpful information
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        if hasattr(self, 'employees') and self.employees:
            # Add last update time if available
            update_info = ""
            if self.last_report_update:
                update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
                update_info = f" | 🕒 Atualizado em {update_time}"
            
            status_text = f"📊 {len(self.employees)} funcionários carregados{update_info} | 💡 Pressione Enter para entrar"
        else:
            status_text = "⚠️ Nenhum relatório carregado | 🔄 Clique no botão de atualizar"
            
        status_label = ttk.Label(status_frame, text=status_text, style="TLabel", font=('Roboto', 10))
        status_label.pack()
        # Frame para botões lado a lado
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=3, column=0, pady=20)
        
        enter_button = ttk.Button(button_frame, text="Entrar", command=self.login, style="TButton")
        enter_button.pack(side=tk.LEFT, padx=(0, 10), anchor="center")
        ToolTip(enter_button, "Clique ou pressione Enter para fazer login")
        
        reload_button = TkButton(button_frame, text="🔄", command=self.reload_report, font=("Roboto", 28, "bold"), bd=0, relief="flat", bg=self.shell_bg, activebackground=self.shell_bg, fg=self.shell_fg, activeforeground=self.shell_fg, highlightthickness=0, padx=0, pady=0)
        reload_button.pack(side=tk.LEFT, anchor="center")
        ToolTip(reload_button, "Recarregar relatório")
        # Exibir logo V-Power centralizada abaixo do botão Entrar
        try:
            logo_img = Image.open("Logo_Vpower.png").convert("RGBA")
            max_width, max_height = 500, 200
            orig_width, orig_height = logo_img.size
            ratio = min(max_width / orig_width, max_height / orig_height, 1.0)
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
            logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(login_frame, image=self.logo_photo, background=self.shell_bg)
            logo_label.grid(row=4, column=0, pady=(30, 0))
        except Exception as e:
            print(f"Erro ao carregar logo V-Power: {e}")
        
        # Botão de configuração (cog) com fundo branco
        try:
            cog_image = Image.open("icons/cog.ico")
            cog_image = cog_image.resize((20, 20), Image.Resampling.LANCZOS)
            background = Image.new('RGBA', (20, 20), (255, 255, 255, 255))  # Fundo branco
            bg_width, bg_height = background.size
            cog_width, cog_height = cog_image.size
            x = (bg_width - cog_width) // 2
            y = (bg_height - cog_height) // 2
            background.paste(cog_image, (x, y), cog_image if cog_image.mode == 'RGBA' else None)
            cog_photo = ImageTk.PhotoImage(background)
            self.style.configure(
                "Cog.TButton",
                background="#FFFFFF",  # Branco
                foreground="black",
                borderwidth=0,
                relief="flat"
            )
            cog_button = ttk.Button(
                self.window,
                image=cog_photo,
                command=self.select_report_file,
                style="Cog.TButton",
                width=1
            )
            cog_button.image = cog_photo
            def position_cog_button():
                try:
                    window_width = self.window.winfo_width()
                    window_height = self.window.winfo_height()
                    x = window_width - 30
                    y = window_height - 30
                    if cog_button.winfo_exists():
                        cog_button.place(x=x, y=y)
                except:
                    pass  # Button may have been destroyed
            position_cog_button()
            self.window.bind('<Configure>', lambda e: position_cog_button())
        except Exception as e:
            print(f"Error loading cog icon: {e}")
            fallback_button = ttk.Button(
                self.window,
                text="⚙",
                command=self.select_report_file,
                style="Cog.TButton"
            )
            def position_fallback_button():
                try:
                    window_width = self.window.winfo_width()
                    window_height = self.window.winfo_height()
                    x = window_width - 30
                    y = window_height - 30
                    if fallback_button.winfo_exists():
                        fallback_button.place(x=x, y=y)
                except:
                    pass  # Button may have been destroyed
            position_fallback_button()
            self.window.bind('<Configure>', lambda e: position_fallback_button())
    
    def select_report_file(self):
        # Prompt de senha antes de abrir a configuração
        password = simpledialog.askstring("Senha de administrador", "Digite a senha para acessar as configurações:", show='*', parent=self.window)
        if password != "Zam1234@":
            messagebox.showerror("Erro", "Senha incorreta!")
            return
        # Nova janela de opções administrativas
        admin_win = tk.Toplevel(self.window)
        admin_win.title("Opções de Administração")
        admin_win.geometry("350x340")
        admin_win.grab_set()
        def open_settings():
            admin_win.destroy()
            self.show_employee_settings_window()
        def open_file():
            admin_win.destroy()
            file_path = filedialog.askopenfilename(
                initialdir=self.last_directory,
                title="Selecione o arquivo de relatório",
                filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*"))
            )
            if file_path:
                self.last_directory = os.path.dirname(file_path)
                self.save_config()
                self.report_file = file_path
                self.load_report()
        def generate_mix_report():
            # Gera relatório de mix de todos os funcionários e dos times
            if not hasattr(self, 'employee_data') or not self.employee_data:
                messagebox.showerror("Erro", "Nenhum relatório carregado.")
                return
            # Ignorar OIL e INACTIVE
            valid_emps = [emp for emp in self.employee_data.values() if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team') not in ("OIL", "INACTIVE")]
            teams = {'A': [], 'B': []}
            for emp in valid_emps:
                team = self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team', 'A')
                if team.startswith('A'):
                    teams['A'].append(emp)
                elif team.startswith('B'):
                    teams['B'].append(emp)
            def calc_team_mix(team_emps):
                total_premium = sum(e['gasolina_vpower'] + e['etanol_vpower'] for e in team_emps)
                total = sum(e['total_quantity'] for e in team_emps)
                return (total_premium / total * 100) if total > 0 else 0.0
            mix_A = calc_team_mix(teams['A'])
            mix_B = calc_team_mix(teams['B'])
            # Gerar texto do relatório
            lines = []
            lines.append("Relatório de Mix de Funcionários e Times\n")
            lines.append(f"Mix do Time A: {mix_A:.2f}%\n")
            lines.append(f"Mix do Time B: {mix_B:.2f}%\n\n")
            lines.append("Funcionários:\n")
            for emp in valid_emps:
                emp_id = emp['id']
                emp_name = emp['name']
                total = emp['total_quantity']
                premium = emp['gasolina_vpower'] + emp['etanol_vpower']
                mix = (premium / total * 100) if total > 0 else 0.0
                team = self.config.get('employee_settings', {}).get(emp_id, {"team": "A"}).get('team', 'A')
                lines.append(f"{emp_id} - {emp_name} | Time: {team} | Mix: {mix:.2f}% | Total: {total:.2f} L\n")
            # Salvar arquivo
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt")],
                title="Salvar relatório de mix"
            )
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                messagebox.showinfo("Relatório gerado", f"Relatório salvo em:\n{save_path}")
        def show_search_history():
            admin_win.destroy()
            self.show_search_history_window()
        
        def show_mix_history():
            admin_win.destroy()
            self.show_mix_history_window()
        
        ttk.Button(admin_win, text="Configurar Funcionários/Times", command=open_settings, style="TButton").pack(pady=10, fill=tk.X, padx=30)
        ttk.Button(admin_win, text="Alterar arquivo de relatório", command=open_file, style="TButton").pack(pady=10, fill=tk.X, padx=30)
        ttk.Button(admin_win, text="Gerar relatório de mix", command=generate_mix_report, style="TButton").pack(pady=10, fill=tk.X, padx=30)
        ttk.Button(admin_win, text="Histórico de Consultas", command=show_search_history, style="TButton").pack(pady=10, fill=tk.X, padx=30)
        ttk.Button(admin_win, text="Histórico de Mix", command=show_mix_history, style="TButton").pack(pady=10, fill=tk.X, padx=30)

    def show_employee_settings_window(self):
        # Carregar lista de funcionários do relatório atual
        if not hasattr(self, 'employee_data') or not self.employee_data:
            messagebox.showerror("Erro", "Nenhum relatório carregado. Carregue um relatório antes de configurar funcionários.")
            return
        # Janela de configuração
        settings_win = tk.Toplevel(self.window)
        settings_win.title("Configuração de Funcionários e Times")
        settings_win.geometry("600x500")
        settings_win.grab_set()
        # Times disponíveis
        teams = [
            ("A", "Time A"),
            ("B", "Time B"),
            ("A_NIGHT", "Noturno Time A"),
            ("B_NIGHT", "Noturno Time B"),
            ("OIL", "Troca de Óleo (sem bonificação)"),
            ("INACTIVE", "Funcionário Desativado")
        ]
        # Carregar configurações existentes
        employee_settings = self.config.get("employee_settings", {})
        # Frame de rolagem
        canvas = tk.Canvas(settings_win)
        frame = ttk.Frame(canvas)
        scrollbar = ttk.Scrollbar(settings_win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=frame, anchor='nw')
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        frame.bind('<Configure>', on_configure)
        # Widgets para cada funcionário
        row = 0
        emp_vars = {}
        for emp_name, emp_data in self.employee_data.items():
            emp_id = emp_data['id']
            label = ttk.Label(frame, text=f"{emp_id} - {emp_data['name']}", style="TLabel")
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            var = tk.StringVar()
            # Get the current team value and convert it to the corresponding label
            current_team = employee_settings.get(emp_id, {}).get('team', 'A')
            current_label = "Time A"  # Default
            for tval, tlabel in teams:
                if tval == current_team:
                    current_label = tlabel
                    break
            var.set(current_label)
            emp_vars[emp_id] = var
            option = ttk.Combobox(frame, textvariable=var, values=[t[1] for t in teams], state="readonly", width=30)
            option.grid(row=row, column=1, padx=5, pady=5)
            row += 1
        # Botão salvar
        def save_settings():
            new_settings = {}
            for emp_id, var in emp_vars.items():
                team_label = var.get()
                # Mapear label para valor
                for tval, tlabel in teams:
                    if tlabel == team_label:
                        new_settings[emp_id] = {"team": tval}
                        break
            self.config["employee_settings"] = new_settings
            self.save_config()
            messagebox.showinfo("Salvo", "Configurações salvas com sucesso!")
            settings_win.destroy()
        save_btn = ttk.Button(settings_win, text="Salvar", command=save_settings, style="TButton")
        save_btn.pack(pady=10)
    
    def show_search_history_window(self):
        """Show search history window (admin only)"""
        history_win = tk.Toplevel(self.window)
        history_win.title("Histórico de Consultas - Administrador")
        history_win.geometry("700x500")
        history_win.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(history_win, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Histórico de Consultas", font=('Roboto', 16, 'bold')).pack(pady=(0, 20))
        
        if not self.search_history:
            ttk.Label(main_frame, text="Nenhuma consulta registrada ainda.", font=('Roboto', 12)).pack(pady=50)
            ttk.Button(main_frame, text="Fechar", command=history_win.destroy, style="TButton").pack(pady=20)
            return
        
        # Create treeview for better display
        columns = ('timestamp', 'employee_id', 'employee_name')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        tree.heading('timestamp', text='Data/Hora')
        tree.heading('employee_id', text='Código')
        tree.heading('employee_name', text='Nome do Funcionário')
        
        # Configure column widths
        tree.column('timestamp', width=150)
        tree.column('employee_id', width=100)
        tree.column('employee_name', width=400)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with search history
        for entry in self.search_history:
            # Format timestamp
            try:
                from datetime import datetime
                if 'timestamp' in entry:
                    # Try to parse ISO format first, then fallback to string format
                    try:
                        dt = datetime.fromisoformat(entry['timestamp'])
                    except:
                        dt = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                    formatted_time = dt.strftime('%d/%m/%Y %H:%M:%S')
                else:
                    formatted_time = "N/A"
            except:
                formatted_time = entry.get('timestamp', 'N/A')
            
            # Handle both old and new format
            if 'employee_name' in entry:
                # New format
                employee_name = entry['employee_name']
                employee_id = entry['employee_id']
            else:
                # Old format - convert
                employee_name = entry.get('code', 'N/A')
                employee_id = entry.get('name', 'N/A')
            
            # Extract employee name without ID if it contains ID
            if ' - ' in employee_name:
                employee_name = employee_name.split(' - ', 1)[1]
            
            tree.insert('', tk.END, values=(formatted_time, employee_id, employee_name))
        
        # Button frame
        button_frame = ttk.Frame(history_win)
        button_frame.pack(fill=tk.X, pady=20, padx=20)
        
        def clear_history():
            if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar todo o histórico de consultas?", parent=history_win):
                self.search_history = []
                self.save_config()
                history_win.destroy()
                messagebox.showinfo("Sucesso", "Histórico de consultas limpo com sucesso!")
        
        def export_history():
            if not self.search_history:
                messagebox.showwarning("Aviso", "Não há histórico para exportar.", parent=history_win)
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt"), ("Arquivo CSV", "*.csv")],
                title="Exportar histórico de consultas",
                parent=history_win
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("Histórico de Consultas - Mix V-Power\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for entry in self.search_history:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(entry['timestamp'])
                                formatted_time = dt.strftime('%d/%m/%Y %H:%M:%S')
                            except:
                                formatted_time = entry['timestamp']
                            
                            employee_name = entry['employee_name']
                            if ' - ' in employee_name:
                                employee_name = employee_name.split(' - ', 1)[1]
                            
                            f.write(f"Data/Hora: {formatted_time}\n")
                            f.write(f"Código: {entry['employee_id']}\n")
                            f.write(f"Funcionário: {employee_name}\n")
                            f.write("-" * 30 + "\n\n")
                    
                    messagebox.showinfo("Sucesso", f"Histórico exportado para:\n{file_path}", parent=history_win)
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao exportar histórico: {str(e)}", parent=history_win)
        
        ttk.Button(button_frame, text="Exportar Histórico", command=export_history, style="TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Limpar Histórico", command=clear_history, style="TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Fechar", command=history_win.destroy, style="TButton").pack(side=tk.RIGHT)
    
    def show_mix_history_window(self):
        """Show mix history window (admin only)"""
        history_win = tk.Toplevel(self.window)
        history_win.title("Histórico de Mix - Administrador")
        history_win.geometry("800x600")
        history_win.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(history_win, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Histórico de Mix dos Funcionários", font=('Roboto', 16, 'bold')).pack(pady=(0, 20))
        
        if not self.mix_history:
            ttk.Label(main_frame, text="Nenhum histórico de mix registrado ainda.", font=('Roboto', 12)).pack(pady=50)
            ttk.Button(main_frame, text="Fechar", command=history_win.destroy, style="TButton").pack(pady=20)
            return
        
        # Create treeview for better display
        columns = ('employee_id', 'employee_name', 'mix_percentage', 'timestamp')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        tree.heading('employee_id', text='Código')
        tree.heading('employee_name', text='Nome do Funcionário')
        tree.heading('mix_percentage', text='Mix (%)')
        tree.heading('timestamp', text='Data/Hora')
        
        # Configure column widths
        tree.column('employee_id', width=100)
        tree.column('employee_name', width=350)
        tree.column('mix_percentage', width=120)
        tree.column('timestamp', width=180)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with mix history
        for emp_id, data in self.mix_history.items():
            # Format timestamp
            try:
                dt = datetime.datetime.fromisoformat(data['timestamp'])
                formatted_time = dt.strftime('%d/%m/%Y %H:%M:%S')
            except:
                formatted_time = data.get('timestamp', 'N/A')
            
            # Extract employee name without ID
            employee_name = data['name']
            if ' - ' in employee_name:
                employee_name = employee_name.split(' - ', 1)[1]
            
            # Format mix percentage
            mix_formatted = f"{data['mix']:.2f}%"
            
            tree.insert('', tk.END, values=(emp_id, employee_name, mix_formatted, formatted_time))
        
        # Button frame
        button_frame = ttk.Frame(history_win)
        button_frame.pack(fill=tk.X, pady=20, padx=20)
        
        def clear_mix_history():
            if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar todo o histórico de mix?\nIsso removerá as comparações de tendência.", parent=history_win):
                self.mix_history = {}
                self.save_config()
                history_win.destroy()
                messagebox.showinfo("Sucesso", "Histórico de mix limpo com sucesso!")
        
        def export_mix_history():
            if not self.mix_history:
                messagebox.showwarning("Aviso", "Não há histórico para exportar.", parent=history_win)
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt"), ("Arquivo CSV", "*.csv")],
                title="Exportar histórico de mix",
                parent=history_win
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("Histórico de Mix - Mix V-Power\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for emp_id, data in self.mix_history.items():
                            try:
                                dt = datetime.datetime.fromisoformat(data['timestamp'])
                                formatted_time = dt.strftime('%d/%m/%Y %H:%M:%S')
                            except:
                                formatted_time = data.get('timestamp', 'N/A')
                            
                            employee_name = data['name']
                            if ' - ' in employee_name:
                                employee_name = employee_name.split(' - ', 1)[1]
                            
                            f.write(f"Código: {emp_id}\n")
                            f.write(f"Funcionário: {employee_name}\n")
                            f.write(f"Mix: {data['mix']:.2f}%\n")
                            f.write(f"Data/Hora: {formatted_time}\n")
                            f.write("-" * 30 + "\n\n")
                    
                    messagebox.showinfo("Sucesso", f"Histórico exportado para:\n{file_path}", parent=history_win)
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao exportar histórico: {str(e)}", parent=history_win)
        
        ttk.Button(button_frame, text="Exportar Histórico", command=export_mix_history, style="TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Limpar Histórico", command=clear_mix_history, style="TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Fechar", command=history_win.destroy, style="TButton").pack(side=tk.RIGHT)
    
    def create_result_widgets(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        # Frame dos resultados (ocupa o topo e cresce)
        result_frame = ttk.Frame(main_frame, padding="20")
        result_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text = tk.Text(
            result_frame,
            height=20,
            width=70,
            font=('Roboto', 11),
            spacing3=3,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            bg=self.shell_bg,
            fg=self.shell_fg,
            insertbackground=self.shell_fg
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)
        # Frame fixo para o botão sair
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        # Create button frame with multiple options
        exit_button = ttk.Button(button_frame, text="Sair (ESC)", command=self.logout, style="TButton")
        exit_button.pack(side=tk.LEFT, pady=20, padx=(0, 10))
        ToolTip(exit_button, "Voltar à tela de login (ESC)")
        

        
        # Add a "Copy Results" button
        copy_button = ttk.Button(button_frame, text="Copiar (Ctrl+C)", command=self.copy_results, style="TButton")
        copy_button.pack(side=tk.LEFT, pady=20)
        ToolTip(copy_button, "Copiar resultados para área de transferência (Ctrl+C)")
        
        # Add keyboard shortcuts
        self.window.bind('<Escape>', lambda event: self.logout())
        self.window.bind('<Control-c>', lambda event: self.copy_results())
        self.window.focus_set()  # Allow window to receive key events
    
    def show_loading_message(self, message="Carregando..."):
        """Show a loading message"""
        # Create a temporary loading label
        loading_label = ttk.Label(self.window, text=message, style="TLabel", font=('Roboto', 12))
        loading_label.place(relx=0.5, rely=0.9, anchor='center')
        self.window.update()
        return loading_label
    
    def hide_loading_message(self, loading_widget):
        """Hide the loading message"""
        if loading_widget:
            loading_widget.destroy()
    
    def load_report(self):
        """Load the report file and process employee data."""
        loading_widget = None
        try:
            loading_widget = self.show_loading_message("📂 Carregando relatório...")
            
            # Try to find relatorio.txt in the current directory
            default_report = os.path.join(self.last_directory, "relatorio.txt")
            if os.path.exists(default_report):
                file_path = default_report
            else:
                self.hide_loading_message(loading_widget)
                file_path = filedialog.askopenfilename(
                    initialdir=self.last_directory,
                    title="Selecione o arquivo de relatório",
                    filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
                )
                if file_path:
                    loading_widget = self.show_loading_message("📂 Carregando relatório...")
            
            if not file_path:
                self.hide_loading_message(loading_widget)
                return
            
            self.last_directory = os.path.dirname(file_path)
            self.save_config()
            
            # Update loading message
            self.hide_loading_message(loading_widget)
            loading_widget = self.show_loading_message("⚙️ Processando dados...")
            
            # Parse the report
            report_data = parse_relatorio(file_path)
            
            if not report_data or not report_data['employees']:
                self.hide_loading_message(loading_widget)
                messagebox.showerror("Erro", "O relatório não é válido ou está vazio.")
                return
            
            # Update the employees list and store data
            self.employees = []
            self.employee_data = {}
            
            # Ensure all employees have team settings (without overwriting existing ones)
            employee_settings = self.config.get("employee_settings", {})
            settings_updated = False
            
            for emp in report_data['employees']:
                employee_name = f"{emp['id']} - {emp['name']}"
                self.employees.append(employee_name)
                
                # Calculate mix percentage
                total = emp['gasolina_comum'] + emp['gasolina_vpower'] + emp['etanol_vpower']
                mix = ((emp['gasolina_vpower'] + emp['etanol_vpower']) / total * 100) if total > 0 else 0.0
                emp['mix'] = mix
                
                # Update mix history for comparison
                self.update_mix_history(emp['id'], employee_name, mix)
                
                self.employee_data[employee_name] = emp
                
                # Add default team setting only if employee doesn't have one
                if emp['id'] not in employee_settings:
                    employee_settings[emp['id']] = {"team": "A"}
                    settings_updated = True
                    # Added default team setting for new employee
            
            # Update config with new employee settings if any were added
            if settings_updated:
                self.config["employee_settings"] = employee_settings
                self.save_config()
            
            # Track when the report file was last modified
            import datetime
            file_mod_time = os.path.getmtime(file_path)
            self.last_report_update = datetime.datetime.fromtimestamp(file_mod_time)
            
            self.hide_loading_message(loading_widget)
            
        except Exception as e:
            self.hide_loading_message(loading_widget)
            messagebox.showerror("Erro", f"Erro ao carregar o relatório: {str(e)}")
    
    def login(self):
        if not self.employees:
            messagebox.showwarning("Aviso", "Erro ao carregar o relatório. Selecione um arquivo de relatório válido.")
            return
        
        code = self.employee_code.get().strip()
        
        if not code:
            messagebox.showerror("Erro", "Por favor, insira o código do funcionário")
            self.focus_entry_field()
            return
        
        # Show loading state
        original_cursor = self.window.cget("cursor")
        self.window.config(cursor="wait")
        self.window.update()
        
        try:
            employee_name = None
            for emp_name in self.employees:
                emp_id = emp_name.split(" - ", 1)[0].strip()
                if code == emp_id:
                    employee_name = emp_name
                    break
            
            if not employee_name:
                messagebox.showerror("Erro", f"Funcionário com código '{code}' não encontrado")
                # Clear the entry and refocus
                self.employee_code.set("")
                self.focus_entry_field()
                return
            
            # Track the search in history
            employee_id = employee_name.split(" - ", 1)[0].strip()
            self.add_to_search_history(employee_name, employee_id)
            
            self.create_result_widgets()
            self.show_employee_results(employee_name)
            
        finally:
            # Restore cursor
            self.window.config(cursor=original_cursor)
    
    def focus_entry_field(self):
        """Helper method to focus on the employee code entry field"""
        def find_and_focus(widget):
            if isinstance(widget, ttk.Entry):
                widget.focus_set()
                return True
            for child in widget.winfo_children():
                if find_and_focus(child):
                    return True
            return False
        find_and_focus(self.window)
    
    def add_to_search_history(self, employee_name, employee_id):
        """Add a search to the history (admin only feature)"""
        import datetime
        
        search_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "employee_id": employee_id,
            "employee_name": employee_name
        }
        
        # Add to beginning of list
        self.search_history.insert(0, search_entry)
        
        # Keep only last 50 searches
        self.search_history = self.search_history[:50]
        
        # Save to config
        self.save_config()
    
    def migrate_search_history(self):
        """Migrate old search history format to new format"""
        migrated = False
        new_history = []
        
        for entry in self.search_history:
            if 'employee_name' not in entry and 'code' in entry:
                # Old format - migrate
                migrated = True
                # Skip migration for now, just clear old entries
                continue
            else:
                # New format - keep
                new_history.append(entry)
        
        if migrated:
            self.search_history = new_history
            self.save_config()
    
    def update_mix_history(self, employee_id, employee_name, current_mix):
        """Update mix history for an employee"""
        # Store current mix as the new "previous" mix for next comparison
        self.mix_history[employee_id] = {
            "name": employee_name,
            "mix": current_mix,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.save_config()
    
    def get_mix_comparison(self, employee_id, current_mix):
        """Get mix comparison data for an employee"""
        if employee_id not in self.mix_history:
            return None
        
        previous_mix = self.mix_history[employee_id]["mix"]
        difference = current_mix - previous_mix
        
        if abs(difference) < 0.01:  # Less than 0.01% difference is considered no change
            return {"status": "same", "difference": 0, "previous": previous_mix}
        elif difference > 0:
            return {"status": "up", "difference": difference, "previous": previous_mix}
        else:
            return {"status": "down", "difference": abs(difference), "previous": previous_mix}
    
    def get_bonus_value(self, mix_percentage):
        for rule in self.config["bonus_rules"]:
            if rule["min"] <= mix_percentage < rule["max"]:
                return rule["value"]
        return 0.0
    
    def show_employee_results(self, employee_name):
        employee_data = self.employee_data[employee_name]
        
        # Update window title with employee name
        self.window.title(f"Mix V-Power - {employee_name}")
        def format_brl(value, decimals=3):
            return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        def format_centavos(value):
            return f'{value:.2f} Centavos'
        def format_brl_money(value):
            return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        self.result_text.delete(1.0, tk.END)

        emp_id = employee_data['id']
        emp_settings = self.config.get('employee_settings', {}).get(emp_id, {"team": "A"})
        emp_team = emp_settings.get('team', 'A')

        # Se funcionário for OIL ou INACTIVE, mostrar mensagem especial e não mostrar mix/bonificação
        if emp_team in ("OIL", "INACTIVE"):
            self.result_text.tag_configure("title", font=('Roboto', 16, 'bold'), foreground=self.shell_red)
            self.result_text.tag_configure("normal", font=('Roboto', 12), foreground=self.shell_fg)
            self.result_text.insert(tk.END, f"Funcionário: {employee_name}\n", "title")
            
            # Add last report update time
            if self.last_report_update:
                update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
                self.result_text.insert(tk.END, f"Relatório atualizado em: {update_time}\n\n", "normal")
            else:
                self.result_text.insert(tk.END, "\n", "normal")
            
            self.result_text.insert(tk.END, f"Time: {emp_team.replace('OIL', 'Troca de Óleo').replace('INACTIVE', 'Desativado')}\n", "normal")
            self.result_text.insert(tk.END, "Este funcionário não participa do cálculo de bonificação.\n", "normal")
            self.result_text.config(state=tk.DISABLED)
            return

        # Carregar todos os funcionários válidos (excluindo OIL)
        valid_emps = [emp for emp in self.employee_data.values() if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team') != 'OIL']
        # Agrupar por time
        teams = {'A': [], 'B': []}
        for emp in valid_emps:
            team = self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team', 'A')
            if team.startswith('A'):
                teams['A'].append(emp)
            elif team.startswith('B'):
                teams['B'].append(emp)
        # Calcular mix de cada time
        def calc_team_mix(team_emps):
            total_premium = sum(e['gasolina_vpower'] + e['etanol_vpower'] for e in team_emps)
            total = sum(e['total_quantity'] for e in team_emps)
            return (total_premium / total * 100) if total > 0 else 0.0
        mix_A = calc_team_mix(teams['A'])
        mix_B = calc_team_mix(teams['B'])
        # Determinar vencedora
        if mix_A > mix_B:
            winner = 'A'
            loser = 'B'
        elif mix_B > mix_A:
            winner = 'B'
            loser = 'A'
        else:
            winner = loser = None  # Empate
        # Calcular mix do funcionário
        total_quantity = employee_data['total_quantity']
        if total_quantity > 0:
            gasolina_vpower = employee_data['gasolina_vpower']
            etanol_vpower = employee_data['etanol_vpower']
            premium_quantity = gasolina_vpower + etanol_vpower
            mix_percentage = (premium_quantity / total_quantity) * 100
        else:
            mix_percentage = 0
            premium_quantity = 0
        # Determinar valor por litro (em centavos)
        team_mix = mix_A if emp_team.startswith('A') else mix_B
        if team_mix > mix_A and emp_team.startswith('A'):
            team_mix = mix_A
        if team_mix > mix_B and emp_team.startswith('B'):
            team_mix = mix_B
        # Regras de bonificação
        def get_bonus_cents(team_mix, is_winner):
            if 35 < team_mix < 37.5:
                return 0.0
            elif 37.5 <= team_mix < 40:
                return 1.25 if is_winner else 0.75
            elif 40 <= team_mix < 45:
                return 1.50 if is_winner else 1.00
            elif 45 <= team_mix < 47.5:
                return 1.75 if is_winner else 1.50
            elif 47.5 <= team_mix < 50:
                return 2.00 if is_winner else 1.75
            elif team_mix >= 50:
                return 2.25 if is_winner else 2.00
            else:
                return 0.0
        # Determinar se funcionário é noturno
        is_night = emp_team in ("A_NIGHT", "B_NIGHT")
        # Determinar se é vencedor
        is_winner = (winner is not None and emp_team.startswith(winner))
        is_loser = (loser is not None and emp_team.startswith(loser))
        # Calcular bonificação
        if is_winner:
            bonus_per_liter = get_bonus_cents(team_mix, True)
        elif is_loser:
            bonus_per_liter = get_bonus_cents(team_mix, False)
        else:
            bonus_per_liter = 0.0
        # Aplicar 70% se noturno
        if is_night:
            bonus_per_liter *= 0.7
        total_bonus = premium_quantity * bonus_per_liter
        # Calcular média de litragem do time (base_team)
        base_team = 'A' if emp_team.startswith('A') else 'B'
        # Filtrar funcionários diurnos do mesmo time
        diurnos = [emp for emp in valid_emps if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team') == base_team]
        # Calcular bonificação individual de cada diurno
        diurno_bonuses = []
        for emp in diurnos:
            total_quantity = emp['total_quantity']
            premium_quantity = emp['gasolina_vpower'] + emp['etanol_vpower'] if total_quantity > 0 else 0
            # Recalcular mix do time (já feito acima)
            # Recalcular se é vencedor
            is_winner = (winner is not None and base_team == winner)
            is_loser = (loser is not None and base_team == loser)
            if is_winner:
                bonus_per_liter = get_bonus_cents(team_mix, True)
            elif is_loser:
                bonus_per_liter = get_bonus_cents(team_mix, False)
            else:
                bonus_per_liter = 0.0
            diurno_bonuses.append(premium_quantity * bonus_per_liter)
        # Calcular média
        if diurno_bonuses:
            avg_bonus = sum(diurno_bonuses) / len(diurno_bonuses)
        else:
            avg_bonus = 0.0
        # Para noturno, aplicar 0.7
        if is_night:
            avg_bonus *= 0.7
        # Exibir total de litros do funcionário (garantir que é o correto)
        total_litros_funcionario = employee_data['total_quantity']
        # Exibir média de litros do grupo (ativos, exceto OIL/INACTIVE)
        if diurnos:
            avg_team_liters_display = sum(emp['total_quantity'] for emp in diurnos) / len(diurnos)
        else:
            avg_team_liters_display = 0.0
        # Exibir na tela
        self.result_text.tag_configure("title", font=('Roboto', 13, 'bold'), foreground=self.shell_red)
        self.result_text.tag_configure("normal", font=('Roboto', 11), foreground=self.shell_fg)
        self.result_text.tag_configure("mix", font=('Roboto', 15, 'bold'), foreground=self.shell_red)
        self.result_text.tag_configure("bonus_label", font=('Roboto', 12, 'bold'), foreground=self.shell_red)
        self.result_text.tag_configure("bonus_value", font=('Roboto', 12, 'bold'), foreground="#228B22")
        self.result_text.insert(tk.END, f"Funcionário: {employee_name}\n", "title")
        
        # Add last report update time
        if self.last_report_update:
            update_time = self.last_report_update.strftime("%d/%m/%Y às %H:%M")
            self.result_text.insert(tk.END, f"Relatório atualizado em: {update_time}\n\n", "normal")
        else:
            self.result_text.insert(tk.END, "\n", "normal")
        
        self.result_text.insert(tk.END, f"Time: {emp_team.replace('_NIGHT', ' (Noturno)').replace('OIL', 'Troca de Óleo')}\n", "normal")
        self.result_text.insert(tk.END, f"Gasolina C Comum: {format_brl(employee_data['gasolina_comum'])} litros\n", "normal")
        self.result_text.insert(tk.END, f"Gasolina C Comum Aditivada: {format_brl(employee_data['gasolina_vpower'])} litros\n", "normal")
        self.result_text.insert(tk.END, f"Etanol Hidratado Comum Aditivado: {format_brl(employee_data['etanol_vpower'])} litros\n", "normal")
        self.result_text.insert(tk.END, f"Média de litragem do time: {format_brl(avg_team_liters_display)} litros\n", "normal")
        self.result_text.insert(tk.END, f"Total de litros do funcionário: {format_brl(total_litros_funcionario)} litros\n\n", "normal")
        # Get mix comparison for visual indicator
        comparison = self.get_mix_comparison(emp_id, mix_percentage)
        mix_display = f"Mix de Vendas do Funcionário: {format_brl(mix_percentage, 2)}%"
        
        if comparison:
            if comparison["status"] == "up":
                mix_display += f" ↗️ (+{format_brl(comparison['difference'], 2)}%)"
                mix_tag = "mix_up"
            elif comparison["status"] == "down":
                mix_display += f" ↘️ (-{format_brl(comparison['difference'], 2)}%)"
                mix_tag = "mix_down"
            else:
                mix_display += " ➡️"
                mix_tag = "mix_same"
        else:
            mix_display += " 🆕"  # New employee indicator
            mix_tag = "mix_new"
        
        # Configure mix comparison styles
        self.result_text.tag_configure("mix_up", font=('Roboto', 15, 'bold'), foreground="#228B22")  # Green
        self.result_text.tag_configure("mix_down", font=('Roboto', 15, 'bold'), foreground="#DC143C")  # Red
        self.result_text.tag_configure("mix_same", font=('Roboto', 15, 'bold'), foreground="#4169E1")  # Blue
        self.result_text.tag_configure("mix_new", font=('Roboto', 15, 'bold'), foreground="#FF8C00")  # Orange
        
        self.result_text.insert(tk.END, f"{mix_display}\n", mix_tag)
        self.result_text.insert(tk.END, f"Mix do Time: {format_brl(team_mix, 2)}%\n\n", "mix")
        self.result_text.insert(tk.END, f"Bonificação por litro: {format_centavos(bonus_per_liter)}\n", "bonus_label")
        # --- Regra especial: bonificação individual se mix 8% abaixo/acima do time ---
        base_team = 'A' if emp_team.startswith('A') else 'B'
        other_team_members = [emp for emp in teams[base_team] if emp['id'] != emp_id]
        if other_team_members:
            total_premium_others = sum(emp['gasolina_vpower'] + emp['etanol_vpower'] for emp in other_team_members)
            total_litros_others = sum(emp['total_quantity'] for emp in other_team_members)
            mix_others = (total_premium_others / total_litros_others * 100) if total_litros_others > 0 else 0.0
        else:
            mix_others = 0.0
        aplica_bonificacao_individual = False
        if mix_percentage < mix_others - 8 or mix_percentage > mix_others + 8:
            aplica_bonificacao_individual = True
        # Calcular bonificação individual se necessário
        bonus_individual = 0.0
        if aplica_bonificacao_individual:
            def get_bonus_cents_individual(mix):
                if 35 < mix < 37.5:
                    return 0.0
                elif 37.5 <= mix < 40:
                    return 0.75
                elif 40 <= mix < 45:
                    return 1.00
                elif 45 <= mix < 47.5:
                    return 1.50
                elif 47.5 <= mix < 50:
                    return 1.75
                elif mix >= 50:
                    return 2.00
                else:
                    return 0.0
            bonus_cents_individual = get_bonus_cents_individual(mix_percentage)
            bonus_individual = premium_quantity * bonus_cents_individual
            if emp_team in ("A_NIGHT", "B_NIGHT"):
                bonus_individual *= 0.7
        # Calcular bonificação estimada por empenho (apenas para diurnos do grupo)
        empenho_bonus = 0.0
        is_diurno = emp_team in ("A", "B")
        if is_diurno:
            diurnos_grupo = [emp for emp in teams[emp_team] if self.config.get('employee_settings', {}).get(emp['id'], {"team": "A"}).get('team') == base_team]
            if diurnos_grupo and len(diurnos_grupo) > 1:
                other_diurnos = [emp for emp in diurnos_grupo if emp['id'] != emp_id]
                if other_diurnos:
                    avg_team_liters = sum(emp['total_quantity'] for emp in other_diurnos) / len(other_diurnos)
                    if total_litros_funcionario > avg_team_liters and avg_team_liters > 0:
                        diff_percent = (total_litros_funcionario - avg_team_liters) / avg_team_liters
                        # Bonificação estimada por empenho: percentual * bonificação principal
                        if aplica_bonificacao_individual:
                            empenho_bonus = diff_percent * bonus_individual
                        else:
                            empenho_bonus = diff_percent * avg_bonus
        # Exibir bonificação principal para todos (diurnos e noturnos)
        if aplica_bonificacao_individual and bonus_individual > 0:
            self.result_text.insert(tk.END, "Bonificação individual por diferença de mix: ", "bonus_label")
            self.result_text.insert(tk.END, f"{format_brl_money(bonus_individual/100)}\n", "bonus_value")
        elif not aplica_bonificacao_individual and avg_bonus > 0:
            self.result_text.insert(tk.END, "Valor estimado da bonificação: ", "bonus_label")
            self.result_text.insert(tk.END, f"{format_brl_money(avg_bonus/100)}\n", "bonus_value")
        if is_diurno and empenho_bonus > 0:
            self.result_text.insert(tk.END, "Bonificação estimada por empenho: ", "bonus_label")
            self.result_text.insert(tk.END, f"{format_brl_money(empenho_bonus/100)}\n", "bonus_value")
        self.result_text.config(state=tk.DISABLED)
    
    def copy_results(self):
        """Copy the results to clipboard"""
        try:
            # Get all text from the result text widget
            content = self.result_text.get(1.0, tk.END)
            # Copy to clipboard
            self.window.clipboard_clear()
            self.window.clipboard_append(content)
            
            # Show confirmation
            original_text = self.result_text.get(tk.END + "-2l", tk.END + "-1l")
            self.result_text.insert(tk.END, "\n✅ Resultados copiados para a área de transferência!")
            self.result_text.see(tk.END)
            
            # Remove the confirmation message after 2 seconds
            self.window.after(2000, lambda: self.remove_copy_confirmation())
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar: {str(e)}")
    
    def remove_copy_confirmation(self):
        """Remove the copy confirmation message"""
        try:
            content = self.result_text.get(1.0, tk.END)
            if "✅ Resultados copiados" in content:
                lines = content.split('\n')
                # Remove the last confirmation line
                filtered_lines = [line for line in lines if "✅ Resultados copiados" not in line]
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, '\n'.join(filtered_lines))
        except:
            pass  # Ignore errors in cleanup
    
    def logout(self):
        # Unbind keyboard shortcuts
        try:
            self.window.unbind('<Escape>')
            self.window.unbind('<Control-c>')
        except:
            pass  # Ignore if bindings don't exist
        
        # Remove trace if it exists
        try:
            if hasattr(self, 'trace_id'):
                self.employee_code.trace_vdelete('w', self.trace_id)
        except:
            pass
        
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Reset window title
        self.window.title("Mix V-Power - Calculadora de Bonificação")
        
        self.create_login_widgets()
        self.employee_code.set("")
    
    def add_to_search_history(self, employee_code, employee_name):
        """Add employee to search history"""
        # Create history entry
        history_entry = {
            "code": employee_code,
            "name": employee_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Remove if already exists (to move to top)
        self.search_history = [h for h in self.search_history if h["code"] != employee_code]
        
        # Add to beginning of list
        self.search_history.insert(0, history_entry)
        
        # Keep only last 10 searches
        self.search_history = self.search_history[:10]
        
        # Save to config
        self.save_config()
    

    
    def reload_report(self):
        """Recarrega o relatório selecionado na configuração atual."""
        self.load_report()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = BonusCalculator()
    app.run()
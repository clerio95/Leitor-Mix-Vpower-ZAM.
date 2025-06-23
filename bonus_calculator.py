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

def parse_relatorio(file_path):
    print(f"\nDebug parse_relatorio:")
    print(f"Opening file: {file_path}")
    
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
            print(f"Debug: Employee found: {employee_name} (ID: {employee_id}, Sales: {sales_count})")
            i += 1
            continue
        
        # Identificar linha de produto
        if current_employee and re.match(r'\|\s*\d+\s*\|', line):
            # Dividir a linha, mantendo todos os campos, mesmo os vazios
            parts = line.split('|')
            if len(parts) >= 9:  # Espera-se pelo menos 9 partes (7 colunas + 2 barras laterais)
                # Ajustar índices para as colunas corretas
                code = parts[1].strip()  # Código
                product_name = parts[2].strip().upper()  # Produto
                quantity_str = parts[4].strip()  # Quantidade
                value_str = parts[6].strip()  # Valor
                
                print(f"\nDebug: Processing product line {i + 1}: '{line}'")
                print(f"Code: '{code}'")
                print(f"Product name: '{product_name}'")
                print(f"Quantity string: '{quantity_str}'")
                print(f"Value string: '{value_str}'")
                
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
                    if 'ETANOL ADITIVADO SHELL V-POWER' in product_name:
                        current_employee['etanol_vpower'] = quantity
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        print(f"Accumulated etanol_vpower: {quantity}")
                    elif 'GASOLINA ADITIVADA V-POWER' in product_name:
                        current_employee['gasolina_vpower'] = quantity
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        print(f"Accumulated gasolina_vpower: {quantity}")
                    elif 'GASOLINA COMUM' in product_name:
                        current_employee['gasolina_comum'] += quantity  # Somar, caso haja múltiplas linhas
                        current_employee['total_quantity'] += quantity
                        if value is not None:
                            current_employee['total_value'] += value
                        print(f"Accumulated gasolina_comum: {quantity}")
                    # Diesel é ignorado conforme especificado
                    
            i += 1
            continue
        
        # Identificar linha de total do funcionário
        if current_employee and 'Total do vendedor' in line:
            print(f"Debug: Found total line for employee at line {i + 1}: '{line}'")
            i += 1
            continue
        
        i += 1
    
    # Adicionar o último funcionário, se existir
    if current_employee:
        report_data['employees'].append(current_employee)
    
    print(f"\nDebug: Final report data:")
    print(f"Employees loaded: {len(report_data['employees'])}")
    for emp in report_data['employees']:
        print(f"\nEmployee: {emp['name']}")
        print(f"Products: {emp['products']}")
        print(f"Gasolina Comum: {emp['gasolina_comum']:.3f} L")
        print(f"Gasolina V-Power: {emp['gasolina_vpower']:.3f} L")
        print(f"Etanol V-Power: {emp['etanol_vpower']:.3f} L")
        print(f"Total quantity: {emp['total_quantity']:.3f}")
        print(f"Total value: {emp['total_value']:.3f}")
    
    return report_data

class BonusCalculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Calculadora de Bonificação - Mix de Vendas")
        self.window.geometry("800x600")
        
        # Configure dark theme
        self.window.configure(bg='black')
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme as base
        
        # Configure dark theme colors
        self.style.configure("TFrame", background="black")
        self.style.configure("TLabel", background="black", foreground="lime", font=('Roboto', 14))
        self.style.configure("Title.TLabel", background="black", foreground="lime", font=('Roboto', 24, 'bold'))
        self.style.configure("Result.TLabel", background="black", foreground="lime", font=('Roboto', 16))
        self.style.configure("Mix.TLabel", background="black", foreground="lime", font=('Roboto', 20, 'bold'))
        self.style.configure("TButton", 
                           background="#333333", 
                           foreground="lime",
                           font=('Roboto', 14),
                           padding=10)
        self.style.map("TButton",
                      background=[('active', '#444444')],
                      foreground=[('active', 'white')])
        
        self.employee_code = tk.StringVar()  # Substitui username por employee_code
        self.employees = []
        
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
                ]
            }
            self.last_directory = os.getcwd()
            self.save_config()
    
    def save_config(self):
        config = {
            "bonus_rules": self.config["bonus_rules"],
            "last_directory": self.last_directory
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def create_login_widgets(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Create main container with padding
        main_frame = ttk.Frame(self.window, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create a frame for the login form with padding
        login_frame = ttk.Frame(main_frame, padding="20")
        login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        login_frame.grid_columnconfigure(0, weight=1)
        
        # Add title
        ttk.Label(login_frame, text="Calculadora de Bonificação", style="Title.TLabel").grid(row=0, column=0, pady=(0, 40))
        
        # Add employee code field
        ttk.Label(login_frame, text="Código do Funcionário:", style="TLabel").grid(row=1, column=0, pady=10)
        code_entry = ttk.Entry(login_frame, textvariable=self.employee_code, width=30, font=('Roboto', 14))
        code_entry.grid(row=2, column=0, pady=(0, 30))
        
        # Add login button
        ttk.Button(login_frame, text="Entrar", command=self.login, style="TButton").grid(row=3, column=0, pady=20)
        
        # Add cog icon button at bottom-right
        try:
            # Load and resize the cog icon
            cog_image = Image.open("icons/cog.ico")
            cog_image = cog_image.resize((20, 20), Image.Resampling.LANCZOS)
            
            # Create a new image with lime background
            background = Image.new('RGBA', (20, 20), (50, 205, 50, 255))  # Lime green color
            
            # Calculate center position for the cog icon
            bg_width, bg_height = background.size
            cog_width, cog_height = cog_image.size
            x = (bg_width - cog_width) // 2
            y = (bg_height - cog_height) // 2
            
            # Paste the cog icon centered on the background
            background.paste(cog_image, (x, y), cog_image if cog_image.mode == 'RGBA' else None)
            
            cog_photo = ImageTk.PhotoImage(background)
            
            # Create a custom style for the cog button
            self.style.configure(
                "Cog.TButton",
                background="#32CD32",  # Lime green
                foreground="black",
                borderwidth=0,
                relief="flat"
            )
            self.style.map(
                "Cog.TButton",
                background=[('active', '#37E837')],  # 15% lighter lime on hover
                foreground=[('active', 'black')]
            )
            
            # Create the cog button with absolute positioning
            cog_button = ttk.Button(
                self.window,  # Parent is window instead of frame
                image=cog_photo,
                command=self.select_report_file,
                style="Cog.TButton",
                width=1
            )
            cog_button.image = cog_photo  # Keep a reference to prevent garbage collection
            
            # Position the button absolutely
            def position_cog_button():
                # Get window dimensions
                window_width = self.window.winfo_width()
                window_height = self.window.winfo_height()
                
                # Calculate position (20px from right and bottom edges)
                x = window_width - 30
                y = window_height - 30
                
                # Place the button
                cog_button.place(x=x, y=y)
            
            # Position initially and bind to window resize
            position_cog_button()
            self.window.bind('<Configure>', lambda e: position_cog_button())
            
        except Exception as e:
            print(f"Error loading cog icon: {e}")
            # Fallback to text button if icon loading fails
            fallback_button = ttk.Button(
                self.window,  # Parent is window instead of frame
                text="⚙",
                command=self.select_report_file,
                style="Cog.TButton"
            )
            
            # Position the fallback button absolutely
            def position_fallback_button():
                window_width = self.window.winfo_width()
                window_height = self.window.winfo_height()
                x = window_width - 30
                y = window_height - 30
                fallback_button.place(x=x, y=y)
            
            position_fallback_button()
            self.window.bind('<Configure>', lambda e: position_fallback_button())
    
    def select_report_file(self):
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
    
    def create_result_widgets(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Create main container with padding
        main_frame = ttk.Frame(self.window, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create a frame for the results with padding
        result_frame = ttk.Frame(main_frame, padding="20")
        result_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text widget with dark theme
        self.result_text = tk.Text(
            result_frame,
            height=20,
            width=70,
            font=('Roboto', 12),
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            bg='black',
            fg='lime',
            insertbackground='lime'  # Cursor color
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)
        
        # Add exit button
        ttk.Button(main_frame, text="Sair", command=self.logout).grid(row=1, column=0, pady=20)
    
    def load_report(self):
        """Load the report file and process employee data."""
        try:
            # Try to find relatorio.txt in the current directory
            default_report = os.path.join(self.last_directory, "relatorio.txt")
            if os.path.exists(default_report):
                file_path = default_report
            else:
                file_path = filedialog.askopenfilename(
                    initialdir=self.last_directory,
                    title="Selecione o arquivo de relatório",
                    filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
                )
            
            if not file_path:
                return
            
            self.last_directory = os.path.dirname(file_path)
            self.save_config()
            
            # Parse the report
            report_data = parse_relatorio(file_path)
            
            if not report_data or not report_data['employees']:
                messagebox.showerror("Erro", "O relatório não é válido ou está vazio.")
                return
            
            # Update the employees list and store data
            self.employees = []
            self.employee_data = {}
            
            for emp in report_data['employees']:
                employee_name = f"{emp['id']} - {emp['name']}"
                self.employees.append(employee_name)
                
                # Calculate mix percentage
                total = emp['gasolina_comum'] + emp['gasolina_vpower'] + emp['etanol_vpower']
                mix = ((emp['gasolina_vpower'] + emp['etanol_vpower']) / total * 100) if total > 0 else 0.0
                emp['mix'] = mix
                
                self.employee_data[employee_name] = emp
                print(f"Debug: Employee loaded: {employee_name}, Mix: {mix:.2f}%")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar o relatório: {str(e)}")
    
    def login(self):
        if not self.employees:
            messagebox.showwarning("Aviso", "Erro ao carregar o relatório. Selecione um arquivo de relatório válido.")
            return
        
        code = self.employee_code.get().strip()
        
        if not code:
            messagebox.showerror("Erro", "Por favor, insira o código do funcionário")
            return
        
        employee_name = None
        print(f"Debug: Searching for employee with code: '{code}'")
        for emp_name in self.employees:
            emp_id = emp_name.split(" - ", 1)[0].strip()
            print(f"Debug: Comparing with employee ID: '{emp_id}'")
            if code == emp_id:
                employee_name = emp_name
                break
        
        if not employee_name:
            print(f"Debug: Employee not found for code: '{code}'")
            messagebox.showerror("Erro", f"Funcionário com código '{code}' não encontrado")
            return
        
        print(f"Debug: Employee found: '{employee_name}'")
        self.create_result_widgets()
        self.show_employee_results(employee_name)
    
    def get_bonus_value(self, mix_percentage):
        for rule in self.config["bonus_rules"]:
            if rule["min"] <= mix_percentage < rule["max"]:
                return rule["value"]
        return 0.0
    
    def show_employee_results(self, employee_name):
        self.result_text.delete(1.0, tk.END)
        
        # Get employee data
        employee_data = self.employee_data[employee_name]
        
        # Calculate mix percentage
        total_quantity = employee_data['total_quantity']
        if total_quantity > 0:
            gasolina_vpower = employee_data['gasolina_vpower']
            etanol_vpower = employee_data['etanol_vpower']
            premium_quantity = gasolina_vpower + etanol_vpower
            mix_percentage = (premium_quantity / total_quantity) * 100
        else:
            mix_percentage = 0
        
        # Get bonus per liter based on mix percentage
        bonus_per_liter = min(self.get_bonus_value(mix_percentage), 0.0225)  # Apply ceiling
        
        # Calculate total bonus (only for premium fuels)
        total_bonus = premium_quantity * bonus_per_liter
        
        # Configure tags for different text styles
        self.result_text.tag_configure("title", font=('Roboto', 16, 'bold'), foreground="lime")
        self.result_text.tag_configure("normal", font=('Roboto', 12), foreground="lime")
        self.result_text.tag_configure("mix", font=('Roboto', 18, 'bold'), foreground="lime")
        self.result_text.tag_configure("bonus", font=('Roboto', 14, 'bold'), foreground="lime")
        
        # Insert content with appropriate tags
        self.result_text.insert(tk.END, f"Funcionário: {employee_name}\n\n", "title")
        self.result_text.insert(tk.END, f"Gasolina Comum: {employee_data['gasolina_comum']:.3f} litros\n", "normal")
        self.result_text.insert(tk.END, f"Gasolina Aditivada V-Power: {employee_data['gasolina_vpower']:.3f} litros\n", "normal")
        self.result_text.insert(tk.END, f"Etanol Aditivado Shell V-Power: {employee_data['etanol_vpower']:.3f} litros\n", "normal")
        self.result_text.insert(tk.END, f"Total: {total_quantity:.3f} litros\n\n", "normal")
        self.result_text.insert(tk.END, f"Mix de Vendas: {mix_percentage:.2f}%\n\n", "mix")
        self.result_text.insert(tk.END, f"Bonificação por litro: R$ {bonus_per_liter:.4f}\n", "normal")
        self.result_text.insert(tk.END, f"Valor estimado da bonificação: R$ {total_bonus:.2f}\n", "bonus")
        
        # Make text read-only
        self.result_text.config(state=tk.DISABLED)
    
    def logout(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.create_login_widgets()
        self.employee_code.set("")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = BonusCalculator()
    app.run()
# 🚀 Mix V-Power - Calculadora de Bonificação

> Sistema profissional para cálculo de bonificações baseado no mix de vendas de combustíveis Shell V-Power

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

## 📋 Sobre o Projeto

Esta aplicação processa relatórios de vendas de combustíveis e calcula bonificações para funcionários com base no mix de vendas de produtos Shell V-Power específicos. Desenvolvida para otimizar o processo de cálculo de incentivos de vendas.

## ✨ Funcionalidades

### 🎯 **Core Features**
- ✅ **Parser Inteligente** - Leitura automática de relatórios de vendas
- ✅ **Autenticação por Código** - Login seguro por código de funcionário
- ✅ **Cálculo Automático** - Mix de vendas e bonificações em tempo real
- ✅ **Interface Moderna** - GUI responsiva com tema Shell V-Power
- ✅ **Timestamp Preciso** - Mostra quando o relatório foi atualizado

### 🔧 **Recursos Avançados**
- ✅ **Histórico de Consultas** - Rastreamento para administradores
- ✅ **Configuração de Times** - Gestão de funcionários por equipes
- ✅ **Cópia de Resultados** - Export para área de transferência (Ctrl+C)
- ✅ **Atalhos de Teclado** - Enter para login, ESC para sair
- ✅ **Validação Visual** - Feedback em tempo real na entrada de dados
- ✅ **Estados de Carregamento** - Indicadores visuais de progresso

### 🛡️ **Administração**
- ✅ **Painel Admin** - Configurações avançadas (senha: `Zam1234@`)
- ✅ **Gestão de Times** - Configuração A/B, Noturno, Troca de Óleo
- ✅ **Relatórios de Mix** - Exportação de dados consolidados
- ✅ **Auditoria** - Histórico completo de consultas

## 🏗️ Produtos Suportados

| Produto | Código | Categoria |
|---------|--------|-----------|
| **DIESEL B S-10 ADITIVADO** | 554 | Ignorado |
| **ETANOL HIDRATADO COMUM ADITIVADO** | 689 | Premium |
| **GASOLINA C COMUM ADITIVADA** | 1 | Premium |
| **GASOLINA C COMUM** | 562 | Comum |

## 🚀 Instalação e Uso

### 📦 **Opção 1: Executável (Recomendado)**
1. Baixe `Mix-V-Power-Completo.zip` da seção [Releases](../../releases)
2. Extraia em qualquer pasta
3. Execute `Mix V-Power.exe`
4. Coloque o arquivo `relatorio.txt` na mesma pasta

### 🐍 **Opção 2: Código Fonte**
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/mix-v-power.git
cd mix-v-power

# Instale dependências
pip install -r requirements.txt

# Execute o programa
python bonus_calculator.py
```

### 🔨 **Opção 3: Build Personalizado**
```bash
# Execute o script de build
./build.bat

# Encontre o executável em:
# dist/Mix V-Power/Mix V-Power.exe
```

## 📊 Como Usar

### 1️⃣ **Login**
- Digite o código do funcionário
- Pressione **Enter** ou clique em "Entrar"

### 2️⃣ **Visualização**
- Veja mix de vendas, bonificações e detalhes
- Use **Ctrl+C** para copiar resultados
- Pressione **ESC** para voltar ao login

### 3️⃣ **Administração**
- Clique no ícone ⚙ para acessar configurações
- Senha: `Zam1234@`
- Configure times, veja histórico, exporte relatórios

## 📁 Estrutura do Projeto

```
mix-v-power/
├── bonus_calculator.py    # Aplicação principal
├── build.bat             # Script de build
├── requirements.txt      # Dependências Python
├── Logo_Vpower.png      # Logo da aplicação
├── icons/               # Ícones da interface
│   ├── iconV.ico        # Ícone principal
│   ├── cog.ico          # Ícone de configuração
│   └── atualizar.png    # Ícone de atualização
├── dist/                # Executáveis gerados
└── docs/                # Documentação adicional
```

## ⚙️ Configuração

### 🎛️ **Regras de Bonificação**
As regras são configuráveis via interface admin:

| Mix Range | Bonificação (Vencedor) | Bonificação (Perdedor) |
|-----------|----------------------|----------------------|
| 35% - 37.5% | R$ 0,00 | R$ 0,00 |
| 37.5% - 40% | R$ 0,0125 | R$ 0,0075 |
| 40% - 45% | R$ 0,015 | R$ 0,01 |
| 45% - 47.5% | R$ 0,0175 | R$ 0,015 |
| 47.5% - 50% | R$ 0,02 | R$ 0,0175 |
| 50%+ | R$ 0,0225 | R$ 0,02 |

### 👥 **Times Disponíveis**
- **Time A** / **Time B** - Funcionários diurnos
- **Noturno Time A** / **Noturno Time B** - Funcionários noturnos (70% da bonificação)
- **Troca de Óleo** - Sem bonificação
- **Desativado** - Funcionário inativo

## 🛠️ Desenvolvimento

### 📋 **Requisitos**
- Python 3.12+
- Windows 7+
- Dependências listadas em `requirements.txt`

### 🔧 **Dependências Principais**
```
pillow==10.2.0          # Processamento de imagens
pyinstaller==6.3.0      # Geração de executáveis
customtkinter==5.2.2    # Interface moderna (opcional)
```

### 🧪 **Testando**
```bash
# Execute o programa em modo desenvolvimento
python bonus_calculator.py

# Para debug, verifique os logs no console
```

## 📝 Changelog

### v2025.08.07 - Versão Atual
- ✅ Parser atualizado para novos nomes de produtos
- ✅ Histórico de consultas para administradores
- ✅ Timestamp baseado na modificação do arquivo
- ✅ Correção do efeito "flashing" nos botões
- ✅ Interface polida com tooltips
- ✅ Melhor organização de código
- ✅ Build automatizado com ZIP de distribuição

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- 📧 **Issues**: [GitHub Issues](../../issues)
- 📖 **Documentação**: [Wiki do Projeto](../../wiki)
- 🔧 **Releases**: [Página de Releases](../../releases)

---

<div align="center">

**Desenvolvido com ❤️ para Shell V-Power**

[![Shell V-Power](https://img.shields.io/badge/Shell-V--Power-red.svg)](https://shell.com.br)

</div> 
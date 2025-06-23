# Instalação da Calculadora de Bonificação

Este guia irá ajudá-lo a instalar a Calculadora de Bonificação em seu computador.

## Requisitos do Sistema

- Windows 10 ou superior
- 100MB de espaço em disco
- Resolução mínima de tela: 800x600

## Instalação

### Método 1: Instalação Direta (Recomendado)

1. Baixe o arquivo `Calculadora de Bonificação.exe` do diretório de distribuição
2. Crie uma nova pasta em seu computador (exemplo: `C:\Calculadora de Bonificação`)
3. Copie o arquivo executável para esta pasta
4. Execute o programa clicando duas vezes no arquivo `Calculadora de Bonificação.exe`

### Método 2: Instalação via Código Fonte

Se você precisar compilar o programa a partir do código fonte:

1. Instale o Python 3.8 ou superior
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o PyInstaller:
   ```
   pyinstaller bonus_calculator.spec
   ```
4. O executável será criado na pasta `dist`

## Primeira Execução

1. Na primeira execução, o programa criará automaticamente o arquivo de configuração
2. Clique no ícone de engrenagem no canto inferior direito para selecionar o arquivo de relatório
3. Digite seu nome de funcionário e senha (padrão: 123)
4. Clique em "Entrar" para acessar o sistema

## Solução de Problemas

Se você encontrar algum problema:

1. Verifique se o arquivo de relatório está no formato correto
2. Certifique-se de que você tem permissões de escrita na pasta do programa
3. Verifique se o arquivo `config.json` foi criado corretamente

## Suporte

Para suporte técnico, entre em contato com o administrador do sistema. 
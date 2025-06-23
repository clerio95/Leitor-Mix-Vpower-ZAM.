# Calculadora de Bonificação - Mix de Vendas

Esta aplicação processa relatórios de vendas de combustíveis e calcula bonificações para funcionários com base no mix de vendas de produtos específicos.

## Funcionalidades

- Leitura automática do arquivo "relatorio.txt"
- Autenticação de funcionários por nome e senha
- Cálculo automático do mix de vendas por funcionário
- Cálculo de bonificações baseado em regras configuráveis
- Interface gráfica amigável
- Visualização individual dos resultados por funcionário

## Requisitos

- Python 3.6 ou superior
- Tkinter (geralmente já incluído com Python)
- Arquivo "relatorio.txt" na mesma pasta do executável

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Coloque o arquivo "relatorio.txt" na mesma pasta do executável

## Como Usar

1. Execute o programa:
   ```
   python bonus_calculator.py
   ```

2. Na tela de login:
   - Digite seu primeiro nome (sem distinção de maiúsculas/minúsculas)
   - Digite sua senha (padrão inicial: 123)
   - Clique em "Entrar"

3. Após o login, você verá:
   - Seu nome
   - Seu percentual de mix de vendas
   - Sua bonificação por litro
   - O valor total da sua bonificação

4. Para sair, clique no botão "Sair"

## Formato do Arquivo de Entrada

O arquivo "relatorio.txt" deve estar no formato do relatório fornecido, contendo:
- Linhas com "Funcionário:" seguido do código e nome
- Linhas com códigos de produtos (562, 1, 689) e quantidades em litros

## Configuração

As regras de bonificação podem ser ajustadas no arquivo `config.json`. O arquivo é criado automaticamente na primeira execução com as regras padrão:

- Mix < 35%: R$ 0,00 por litro
- Mix ≥ 35% e < 37,5%: R$ 0,0125 por litro
- Mix ≥ 37,5% e < 40%: R$ 0,0125 por litro
- Mix ≥ 40% e < 45%: R$ 0,0125 por litro
- Mix ≥ 45% e < 47,5%: R$ 0,0175 por litro
- Mix ≥ 47,5% e < 50%: R$ 0,02 por litro
- Mix ≥ 50%: R$ 0,0225 por litro

## Segurança

- A senha padrão inicial é "123"
- Recomenda-se alterar a senha após o primeiro acesso
- Os dados são protegidos por autenticação individual

## Suporte

Para reportar problemas ou sugerir melhorias, por favor abra uma issue no repositório. 
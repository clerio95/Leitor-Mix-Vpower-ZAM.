# 🔧 Guia do Administrador - Mix V-Power

## 🔑 Acesso Administrativo

### Login
- **Localização**: Ícone ⚙ na tela de login
- **Senha**: `Zam1234@`
- **Funcionalidades**: Configurações avançadas do sistema

## 📋 Funcionalidades Administrativas

### 1️⃣ **Configurar Funcionários/Times**
Permite configurar a qual time cada funcionário pertence:

#### Times Disponíveis:
- **Time A** - Funcionários diurnos do time A
- **Time B** - Funcionários diurnos do time B  
- **Noturno Time A** - Funcionários noturnos do time A (70% da bonificação)
- **Noturno Time B** - Funcionários noturnos do time B (70% da bonificação)
- **Troca de Óleo** - Funcionários que não participam da bonificação
- **Funcionário Desativado** - Funcionários inativos

#### Como Configurar:
1. Acesse o painel administrativo
2. Clique em "Configurar Funcionários/Times"
3. Selecione o time para cada funcionário
4. Clique em "Salvar"

### 2️⃣ **Alterar Arquivo de Relatório**
Permite selecionar um arquivo de relatório diferente:

1. Clique em "Alterar arquivo de relatório"
2. Navegue até o arquivo desejado
3. Selecione o arquivo `.txt`
4. O sistema carregará automaticamente os novos dados

### 3️⃣ **Gerar Relatório de Mix**
Exporta um relatório consolidado com o mix de todos os funcionários:

#### Conteúdo do Relatório:
- Mix do Time A e Time B
- Lista de todos os funcionários com:
  - Código e nome
  - Time configurado
  - Percentual de mix
  - Total de litros vendidos

#### Como Gerar:
1. Clique em "Gerar relatório de mix"
2. Escolha o local para salvar
3. O arquivo será salvo em formato `.txt`

### 4️⃣ **Histórico de Consultas**
Sistema de auditoria que registra todas as consultas realizadas:

#### Informações Registradas:
- **Data/Hora**: Quando a consulta foi realizada
- **Código**: Código do funcionário consultado
- **Nome**: Nome do funcionário consultado

#### Funcionalidades:
- **Visualizar**: Lista completa de consultas
- **Exportar**: Salvar histórico em arquivo
- **Limpar**: Remover todo o histórico (irreversível)

## ⚙️ Configurações Avançadas

### 📊 **Regras de Bonificação**
As regras são aplicadas automaticamente baseadas no mix do time:

| Mix do Time | Vencedor | Perdedor |
|-------------|----------|----------|
| 35% - 37.5% | R$ 0,00 | R$ 0,00 |
| 37.5% - 40% | R$ 0,0125 | R$ 0,0075 |
| 40% - 45% | R$ 0,015 | R$ 0,01 |
| 45% - 47.5% | R$ 0,0175 | R$ 0,015 |
| 47.5% - 50% | R$ 0,02 | R$ 0,0175 |
| 50%+ | R$ 0,0225 | R$ 0,02 |

### 🌙 **Funcionários Noturnos**
- Recebem 70% da bonificação calculada
- Identificados pelos times "Noturno Time A" e "Noturno Time B"

### 🔧 **Funcionários de Troca de Óleo**
- Não participam do cálculo de bonificação
- Exibem mensagem especial na tela de resultados

## 📁 Arquivos de Configuração

### `config.json`
Arquivo principal de configuração que armazena:
- Configurações de times por funcionário
- Histórico de consultas
- Última atualização do relatório
- Diretório padrão de arquivos

**⚠️ Importante**: Não edite este arquivo manualmente. Use sempre a interface administrativa.

## 🛡️ Segurança

### Controle de Acesso
- Histórico de consultas visível apenas para administradores
- Senha de administrador necessária para configurações
- Logs de auditoria para rastreabilidade

### Backup de Dados
- Recomenda-se backup regular do arquivo `config.json`
- Histórico de consultas é mantido indefinidamente até limpeza manual

## 🚨 Solução de Problemas

### Funcionário Não Aparece
1. Verifique se o relatório foi carregado corretamente
2. Confirme se o funcionário está no arquivo `relatorio.txt`
3. Recarregue o relatório usando o botão 🔄

### Configurações Não Salvam
1. Verifique permissões de escrita na pasta
2. Certifique-se de clicar em "Salvar" após as alterações
3. Reinicie o programa se necessário

### Histórico Não Aparece
1. Confirme que há consultas realizadas
2. Verifique se está acessando como administrador
3. O histórico é criado apenas após a primeira consulta

## 📞 Suporte Técnico

Para problemas técnicos:
1. Verifique os logs no console (se executando via Python)
2. Confirme que todos os arquivos estão na pasta correta
3. Documente o erro e entre em contato com o suporte
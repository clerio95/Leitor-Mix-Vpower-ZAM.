# 👤 Guia do Usuário - Mix V-Power

## 🚀 Primeiros Passos

### Instalação
1. Extraia o arquivo `Mix-V-Power-Completo.zip`
2. Mantenha todos os arquivos na mesma pasta
3. Coloque o arquivo `relatorio.txt` na pasta do programa
4. Execute `Mix V-Power.exe`

### Primeiro Acesso
1. Digite seu código de funcionário
2. Pressione **Enter** ou clique em "Entrar"
3. Visualize seus resultados

## 🖥️ Interface do Usuário

### Tela de Login
- **Campo de Código**: Digite seu código de funcionário
- **Botão Entrar**: Confirma o login
- **Botão 🔄**: Recarrega o relatório
- **Status**: Mostra quantos funcionários foram carregados e quando

### Tela de Resultados
Exibe informações completas sobre seu desempenho:

#### 📊 **Informações Básicas**
- **Nome**: Seu nome completo
- **Time**: Qual time você pertence (A, B, Noturno, etc.)
- **Última Atualização**: Quando o relatório foi gerado

#### ⛽ **Vendas por Produto**
- **Gasolina C Comum**: Quantidade vendida em litros
- **Gasolina C Comum Aditivada**: Quantidade vendida em litros
- **Etanol Hidratado Comum Aditivado**: Quantidade vendida em litros

#### 📈 **Métricas de Performance**
- **Mix de Vendas**: Seu percentual de produtos premium
- **Mix do Time**: Percentual do seu time
- **Total de Litros**: Sua venda total
- **Média do Time**: Média de vendas do seu time

#### 💰 **Bonificação**
- **Valor por Litro**: Quanto você recebe por litro premium
- **Bonificação Total**: Valor estimado da sua bonificação

## ⌨️ Atalhos de Teclado

### Tela de Login
- **Enter**: Fazer login
- **Tab**: Navegar entre campos

### Tela de Resultados
- **ESC**: Voltar ao login
- **Ctrl+C**: Copiar resultados para área de transferência

## 🎯 Como Funciona o Mix

### Cálculo do Mix
```
Mix = (Produtos Premium / Total de Vendas) × 100

Produtos Premium:
- Gasolina C Comum Aditivada
- Etanol Hidratado Comum Aditivado

Total de Vendas:
- Gasolina C Comum
- Gasolina C Comum Aditivada  
- Etanol Hidratado Comum Aditivado
```

### Exemplo Prático
Se você vendeu:
- 1000L de Gasolina C Comum
- 500L de Gasolina C Comum Aditivada
- 200L de Etanol Hidratado Comum Aditivado

**Cálculo:**
- Premium: 500L + 200L = 700L
- Total: 1000L + 500L + 200L = 1700L
- Mix: (700 ÷ 1700) × 100 = 41,18%

## 💰 Sistema de Bonificação

### Times
O sistema divide funcionários em times que competem entre si:
- **Time A** vs **Time B**
- O time com maior mix ganha bonificação maior

### Funcionários Noturnos
- Recebem 70% da bonificação do time
- Identificados como "Noturno" na tela

### Regras de Bonificação
A bonificação varia conforme o mix do time:

| Mix do Time | Status | Bonificação |
|-------------|--------|-------------|
| Abaixo de 35% | Sem bonificação | R$ 0,00 |
| 35% - 37,5% | Mínimo | R$ 0,00 |
| 37,5% - 40% | Básico | R$ 0,0125 (vencedor) |
| 40% - 45% | Bom | R$ 0,015 (vencedor) |
| 45% - 47,5% | Muito Bom | R$ 0,0175 (vencedor) |
| 47,5% - 50% | Excelente | R$ 0,02 (vencedor) |
| Acima de 50% | Excepcional | R$ 0,0225 (vencedor) |

## 📋 Tipos de Funcionário

### 🏆 **Funcionários Ativos**
- Participam da competição entre times
- Recebem bonificação baseada no mix
- Podem ser diurnos ou noturnos

### 🔧 **Troca de Óleo**
- Não participam da bonificação de mix
- Exibem mensagem especial
- Focam em serviços, não em vendas de combustível

### ⏸️ **Desativados**
- Funcionários temporariamente inativos
- Não recebem bonificação
- Dados mantidos para histórico

## 🔍 Interpretando Seus Resultados

### Mix Alto (45%+)
- **Excelente performance** em produtos premium
- **Bonificação máxima** se o time vencer
- Continue focando em produtos aditivados

### Mix Médio (35-45%)
- **Performance adequada** mas com potencial
- **Bonificação moderada** dependendo do time
- Oportunidade de crescimento

### Mix Baixo (<35%)
- **Foque mais** em produtos premium
- **Sem bonificação** neste período
- Treinamento pode ser necessário

## ❓ Perguntas Frequentes

### **P: Não consigo fazer login**
**R:** Verifique se:
- Digitou o código correto
- O relatório foi carregado (veja o status na tela)
- Seu código está no relatório atual

### **P: Meus dados não aparecem**
**R:** Possíveis causas:
- Relatório desatualizado
- Código incorreto
- Arquivo `relatorio.txt` não está na pasta

### **P: Como copio meus resultados?**
**R:** Use **Ctrl+C** na tela de resultados ou clique no botão "Copiar"

### **P: O que significa "Time Noturno"?**
**R:** Funcionários do turno da noite que recebem 70% da bonificação padrão

### **P: Por que não tenho bonificação?**
**R:** Possíveis motivos:
- Mix do time abaixo de 35%
- Funcionário configurado como "Troca de Óleo"
- Time perdeu a competição mensal

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se o arquivo `relatorio.txt` está atualizado
2. Confirme seu código de funcionário
3. Entre em contato com o administrador do sistema

---

**💡 Dica**: Foque na venda de produtos aditivados para aumentar seu mix e bonificação!
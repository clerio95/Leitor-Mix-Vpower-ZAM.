# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2025.08.07] - 2025-08-07

### ✨ Adicionado
- **Parser Atualizado**: Suporte aos novos nomes de produtos Shell V-Power
  - DIESEL B S-10 ADITIVADO (anteriormente DIESEL S-10 EVOLUX)
  - ETANOL HIDRATADO COMUM ADITIVADO (anteriormente ETANOL ADITIVADO SHELL V-POWER)
  - GASOLINA C COMUM ADITIVADA (anteriormente GASOLINA ADITIVADA V-POWER)
  - GASOLINA C COMUM (anteriormente GASOLINA COMUM)

- **Histórico de Consultas**: Sistema de auditoria para administradores
  - Rastreamento de todas as consultas realizadas
  - Exportação de histórico em formato texto
  - Limpeza de histórico via interface admin
  - Acesso restrito apenas para administradores

- **Timestamp de Arquivo**: Exibição da data/hora real do relatório
  - Baseado na modificação do arquivo `relatorio.txt`
  - Exibido na tela de login e resultados
  - Formato brasileiro (DD/MM/AAAA às HH:MM)

- **Interface Polida**: Melhorias significativas na experiência do usuário
  - Tooltips informativos em todos os botões
  - Atalhos de teclado (Enter, ESC, Ctrl+C)
  - Validação visual em tempo real
  - Estados de carregamento com indicadores
  - Cópia de resultados para área de transferência

- **Build Automatizado**: Script completo de distribuição
  - Limpeza automática de builds anteriores
  - Criação de pacote ZIP com todos os arquivos necessários
  - Guia de instalação incluído
  - Estrutura organizada para distribuição

### 🔧 Corrigido
- **Efeito "Flashing"**: Eliminado o efeito de piscar nos botões
  - Hover effects removidos para estabilidade visual
  - Cores consistentes em todos os estados
  - Experiência mais profissional

- **Persistência de Configurações**: Times de funcionários agora salvam corretamente
  - Correção na migração de dados antigos
  - Mapeamento correto entre valores e labels
  - Configurações mantidas entre sessões

- **Parser Robusto**: Melhor tratamento de variações nos nomes de produtos
  - Suporte a formatos antigos e novos
  - Matching flexível por palavras-chave
  - Logs de debug para produtos não reconhecidos

### 🚀 Melhorado
- **Segurança**: Histórico de consultas restrito a administradores
- **Performance**: Carregamento otimizado de relatórios
- **UX**: Interface mais intuitiva e responsiva
- **Documentação**: README completo e profissional
- **Distribuição**: Pacote ZIP pronto para deploy

### 🗑️ Removido
- **"Nova Consulta"**: Feature removida por questões de segurança
  - Usuários devem retornar ao login para nova consulta
  - Fluxo mais controlado e seguro

## [Versões Anteriores]

### [1.0.0] - Data Anterior
- Versão inicial do sistema
- Parser básico para produtos Shell V-Power
- Interface gráfica com Tkinter
- Cálculo de bonificações por mix de vendas
- Configuração de times A e B
- Sistema de login por código de funcionário

---

## Tipos de Mudanças
- `✨ Adicionado` para novas funcionalidades
- `🔧 Corrigido` para correções de bugs
- `🚀 Melhorado` para mudanças em funcionalidades existentes
- `🗑️ Removido` para funcionalidades removidas
- `🔒 Segurança` para correções de vulnerabilidades
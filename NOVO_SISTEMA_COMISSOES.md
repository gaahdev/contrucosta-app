# 🎯 Sistema de Comissões - Novo (Março 2026+)

## Visão Geral

A partir do mês de **MARÇO de 2026**, o sistema de comissões da Construcosta será modificado de:

### ❌ **ANTIGA (Fevereiro - antigo)**
- **Método**: Comissão por Nota Fiscal
- **Cálculo**: Valor fixo por nota de cada caminhão
- **Exemplo**: Nota = Caminhão BKO (R$ 3,50), Caminhão GKY (R$ 7,50)

### ✅ **NOVA (Março 2026+)**
- **Método**: Comissão por Valor Entregue
- **Base**: **1% do valor total de mercadorias entregues no mês**
- **Ajuste**: Percentual varia (0.8%, 0.9%, 1.0%) conforme ocorrências do funcionário

---

## 📊 Cálculo de Comissão (Novo Sistema)

### Fórmula Básica:
```
Comissão = Valor Total Entregue × Percentual
```

### Exemplos:

#### Funcionário com **POUCAS ocorrências** (Bottom 33%)
```
Valor Entregue: R$ 10.000,00
Percentual: 1.0% (menos ocorrências = maior %)
Comissão: R$ 10.000,00 × 1.0% = R$ 100,00
```

#### Funcionário com **OCORRÊNCIAS MEDIANAS** (Middle 33%)
```
Valor Entregue: R$ 10.000,00
Percentual: 0.9%
Comissão: R$ 10.000,00 × 0.9% = R$ 90,00
```

#### Funcionário com **MUITAS ocorrências** (Top 33%)
```
Valor Entregue: R$ 10.000,00
Percentual: 0.8% (mais ocorrências = menor %)
Comissão: R$ 10.000,00 × 0.8% = R$ 80,00
```

---

## 🚨 Sistema de Ocorrências

### O que é uma Ocorrência?
Qualquer problema ou desvio no cumprimento de tarefas:
- ⏰ **Atraso de entrega** (ex: entrega fora do horário)
- 💔 **Dano de mercadoria** (ex: produto quebrado)
- 🔧 **Outro problema** (ex: falta em compromisso)

### Como Lançar Ocorrências?

1. **Acesse**: Menu Admin → **Comissões** → Aba "Lançar Ocorrências"
2. **Preencha**:
   - 📝 **Número da Nota**: Ex "NOTE001" (identificador único)
   - 👤 **ID do Funcionário**: Ex "emp_123"
   - 👥 **Tipo de Funcionário**: "driver" ou "helper"
   - ⚠️ **Tipo de Ocorrência**: "atraso", "dano" ou "outro"
   - 📄 **Descrição**: Detalhe breve do ocorrido (ex: "Atraso 2h na rota de Juiz de Fora")

3. **Clique**: "Lançar Ocorrência"
4. **Confirmação**: Sistema confirmará recebimento

### Período de Ocorrências
- Ocorrências são **registradas mensalmente**
- Sistema agrupa por **mês/ano**
- Cada mês tem cálculo independente de percentuais

---

## 💰 Cálculo e Lançamento de Comissão

### Passo a Passo:

#### **1. Acessar Calculadora**
- Menu Admin → **Comissões** → Aba "Calcular Comissão"

#### **2. Informar Dados**
```
Funcionário ID:          [emp_123]
Valor Total Entregue:    [R$ 10.500,00]
Mês:                     [2] (Fevereiro)
Ano:                     [2026]
```

#### **3. Sistema Calcula**
- ✓ Busca todas as ocorrências do mês
- ✓ Agrupa por funcionário
- ✓ Ordena por quantidade de ocorrências
- ✓ Divide em 3 grupos iguais:
  - **Top 33%** (mais ocorrências): **0.8%**
  - **Middle 33%** (medianas): **0.9%**
  - **Bottom 33%** (menos ocorrências): **1.0%**

#### **4. Resultado Exibido**
```
📊 Cálculo de Comissão

Funcionário: João (ID: emp_123)
Valor Entregue: R$ 10.500,00
Ocorrências: 5 (Classificação: 🟡 Medianas)
Percentual: 0.9%
-----------------------------------------
Comissão: R$ 10.500,00 × 0.9% = R$ 94,50
```

#### **5. Lançar Comissão**
- Clique no botão **"Lançar Comissão"**
- Sistema envia notificação automática para o funcionário
- Comissão fica registrada no histórico

---

## 🔔 Notificações

### Quando o Funcionário é Notificado?
✅ **Quando sua comissão é lançada no sistema**

### Como Recebe Notificação?
1. **Na Web**: Notificação aparece em tempo real (topo da tela)
2. **No Windows (EXE)**: Janela de notificação do sistema
3. **No Android (APK)**: Push notification na app

### Conteúdo da Notificação:
```
💰 Nova Comissão Lançada

Sua comissão de R$ 94,50 (0.9%) foi registrada no sistema.
Período: Fevereiro/2026
```

---

## 📈 Dashboard de Estatísticas

### Informações Disponíveis:
```
Mês/Ano: Fevereiro/2026

📊 Distribuição por Tier:
  🟢 Poucas Ocorrências (1.0%): 5 funcionários
  🟡 Ocorrências Medianas (0.9%): 5 funcionários
  🔴 Muitas Ocorrências (0.8%): 4 funcionários

💰 Resumo Financeiro:
  Total de Comissões: 14 funcionários
  Valor Total Pago: R$ 1.243,50
  Média por Funcionário: R$ 88,82

📝 Ocorrências:
  Total Lançado: 52 ocorrências
  Funcionário com Mais: João (8 ocorrências)
```

---

## ⚙️ Configuração Técnica

### Banco de Dados

#### Coleção: `occurrences` (Ocorrências)
```javascript
{
  "_id": ObjectId,
  "id": "unique-uuid",
  "note_number": "NOTE001",
  "employee_id": "emp_123",
  "employee_type": "driver",
  "occurrence_type": "atraso",
  "description": "Atraso na entrega de 2 horas",
  "created_at": "2026-02-15T14:30:00Z",
  "month": 2,
  "year": 2026
}
```

#### Coleção: `commissions` (Comissões Lançadas)
```javascript
{
  "_id": ObjectId,
  "id": "unique-uuid",
  "employee_id": "emp_123",
  "employee_name": "João Silva",
  "month": 2,
  "year": 2026,
  "total_delivered_value": 10500.00,
  "percentage": 0.9,
  "commission_amount": 94.50,
  "occurrence_count": 5,
  "tier": "median",
  "posted_at": "2026-02-28T18:00:00Z"
}
```

#### Coleção: `notifications` (Notificações)
```javascript
{
  "_id": ObjectId,
  "id": "unique-uuid",
  "employee_id": "emp_123",
  "employee_name": "João Silva",
  "type": "commission_posted",
  "title": "💰 Nova Comissão Lançada",
  "message": "Sua comissão de R$ 94,50 (0.9%) foi registrada no sistema",
  "timestamp": "2026-02-28T18:00:00Z",
  "read": false,
  "data": {
    "commission_amount": 94.50,
    "percentage": 0.9
  }
}
```

### Endpoints da API

#### Lançar Ocorrência
```
POST /api/commission/occurrences

Body:
{
  "note_number": "NOTE001",
  "employee_id": "emp_123",
  "employee_type": "driver",
  "occurrence_type": "atraso",
  "description": "Atraso 2h",
  "month": 2,
  "year": 2026
}

Response:
{
  "message": "Occurrence logged successfully",
  "occurrence_id": "uuid",
  "occurrence": { ... }
}
```

#### Calcular Comissão
```
POST /api/commission/calculate

Body:
{
  "employee_id": "emp_123",
  "total_delivered_value": 10500.00,
  "month": 2,
  "year": 2026
}

Response:
{
  "employee_id": "emp_123",
  "total_delivered_value": 10500.00,
  "occurrence_count": 5,
  "percentage": 0.9,
  "commission_amount": 94.50,
  "tier": "median",
  "calculation_breakdown": { ... }
}
```

#### Lançar Comissão
```
POST /api/commission/post

Body:
{
  "employee_id": "emp_123",
  "employee_name": "João Silva",
  "month": 2,
  "year": 2026,
  "total_delivered_value": 10500.00,
  "percentage": 0.9,
  "commission_amount": 94.50,
  "occurrence_count": 5,
  "tier": "median"
}

Response:
{
  "message": "Commission posted successfully",
  "commission_id": "uuid",
  "notification_sent": true
}
```

#### Obter Estatísticas
```
GET /api/commission/statistics?month=2&year=2026

Response:
{
  "month": 2,
  "year": 2026,
  "total_commissions_posted": 14,
  "total_occurrences_logged": 52,
  "tier_distribution": {
    "high": 4,
    "median": 5,
    "low": 5
  },
  "average_commission": 88.82,
  "total_commission_amount": 1243.50
}
```

---

## 🔄 Compatibilidade com Sistema Antigo

### ⚠️ IMPORTANTE:
- **Fevereiro 2026**: Sistema ANTIGO por nota continua funcionando
- **Março 2026+**: Sistema NOVO por valor

### Ambos Funcionam em Paralelo?
```
❌ NÃO - Serão mutuamente exclusivos
  - Primeiro período usa sistema antigo
  - Próximos períodos usam sistema novo
  - Mudança é definitiva em Março
```

---

## 👥 Permissões

| Ação | Admin | Driver | Helper |
|------|-------|--------|--------|
| Lançar Ocorrência | ✅ | ❌ | ❌ |
| Calcular Comissão | ✅ | ❌ | ❌ |
| Lançar Comissão | ✅ | ❌ | ❌ |
| Ver Própria Comissão | ✅ | ✅* | ✅* |
| Ver Todas Comissões | ✅ | ❌ | ❌ |
| Ver Estatísticas | ✅ | ❌ | ❌ |

*Apenas histórico pessoal não a decisão de lançamento

---

## 🗓️ Cronograma

```
DATA: 28 de Fevereiro de 2026
├─ Último mês com sistema ANTIGO
├─ Ocorrências começam a ser registradas
└─ Sistema novo preparado em segundo plano

DATA: 01 de Março de 2026
├─ Sistema NOVO ativado
├─ Comissões calculadas com novo percentual
└─ Notificações automáticas ativadas
```

---

## 📝 Notas Importantes

1. ✅ **Dados Sincronizados**: Todas as mudanças sincronizam automaticamente entre Web, Windows e Android
2. ✅ **Histórico Mantido**: Ocorrências anteriores ficam registradas indefinidamente
3. ✅ **Cálculo Automático**: Percentuais são calculados automaticamente, sem intervenção manual
4. ✅ **Notificações em Tempo Real**: Funcionários recebem notificação imediatamente ao lançar comissão
5. 🔒 **Segurança**: Apenas admin pode lançar ocorrências e comissões

---

## ❓ Dúvidas Frequentes

### P: Posso mudar ocorrência após lançá-la?
**R**: No código atual, não. Ocorrências são imutáveis. Para correção, lançar nova ocorrência com descrição corrigida.

### P: E se o funcionário não tiver ocorrências?
**R**: Fica no tier "low" (bottom 33%), recebendo 1.0%.

### P: Quanto tempo demora a notificação chegar?
**R**: Imediato. A notificação é lançada junto ao lançamento da comissão.

### P: Pode ter retroatividade?
**R**: Sim. Você pode lançar comissões de meses anteriores informando o mês/ano.

### P: Como saber em qual tier o funcionário está?
**R**: O sistema mostra automaticamente na tela de cálculo (🔴🟡🟢).

---

## 🔧 Troubleshooting

### Problema: Comissão não está calculando corretamente
**Solução**: Verificar se ocorrências foram lançadas para aquele mês/ano no banco de dados

### Problema: Notificação não chegou
**Solução**: Verificar se conexão com banco está ativa, e se funcionário está recebendo dados

### Problema: Percentual mostrando incorreto
**Solução**: Aguardar sincronização (30-60 segundos) ou fazer refresh da página

---

## 📞 Suporte

Para dúvidas técnicas ou problemas:
1. Verificar este documento
2. Consultar o código em `/frontend/src/services/commissionService.js`
3. Revisar logs do backend em `/backend/commission_routes.py`

---

**Última atualização**: 26 de Fevereiro de 2026
**Status**: Pronto para Produção - Ativação em Março 2026

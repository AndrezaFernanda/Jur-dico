"""
Base de conhecimento semântico da Minuta Padrão CINCATARINA.
O LLM deve ENTENDER esta minuta, não comparar textos.
"""

CONTEXTO_MINUTA = """
Você conhece profundamente a MINUTA PADRÃO do CINCATARINA (Consórcio Interfederativo Santa Catarina)
para contratação de serviços de gerenciamento de frota/combustíveis com a empresa MaxiFrota.

Abaixo está o conhecimento estruturado desta minuta padrão que você deve usar como referência:

=== PARTES DO CONTRATO ===
- CONTRATANTE: Município (Órgão Participante)
- CONTRATADA: MAXIFROTA SERVIÇOS DE MANUTENÇÃO DE FROTA LTDA. (CNPJ 27.284.516/0001-61)
- INTERVENIENTE: CINCATARINA (CNPJ 12.075.748/0001-32), representado pelo Diretor Executivo

=== CLÁUSULA 1 — OBJETO ===
- Gerenciamento de fornecimento de Combustíveis, Aditivos, Lubrificantes e Filtros de Óleo
- Uso de cartão magnético OU etiqueta autoadesiva RFID/NFC ou similar
- Rede credenciada de postos de combustíveis
- Inclui: controle de despesas, equipamentos de processamento, cartões/etiquetas gratuitos,
  sistema de BI, relatórios gerenciais, ferramenta CKAN de dados abertos
- Combustíveis: Gasolina (comum/aditivada), Etanol (comum/aditivado), Diesel (comum/aditivado),
  Diesel S-10, GNV
- Nota Fiscal por Centro de Custo, com relatório mensal detalhado

=== CLÁUSULA 2 — ENTREGAS/EXECUÇÃO ===
- Decorrente de SRP (Sistema de Registro de Preços)
- Regime: EMPREITADA POR PREÇO UNITÁRIO
- Preço da bomba na data do abastecimento (não pode superar preço máximo ANP)
- Menor preço entre postos credenciados em cada local
- Todas as despesas de entrega por conta da CONTRATADA

=== CLÁUSULA 3 — PREÇOS ===
- Taxa de Administração: percentual FIXO (pode ser negativo, ex: -4,92%)
- Valor contratado é ESTIMATIVO (depende do consumo real)
- CONTRATADA é única responsável pelo pagamento aos estabelecimentos credenciados
- CONTRATANTE não responde solidária ou subsidiariamente
- Glosa possível se valores acima da média de mercado

=== CLÁUSULA 4 — PAGAMENTO ===
- Prazo: até o 20º (vigésimo) dia do mês subsequente ao serviço prestado
- Forma: TED, DOC, depósito ou PIX / boleto
- Exige: Nota Fiscal Eletrônica + arquivo XML
- CNPJ da conta deve ser idêntico ao da proposta
- NF deve conter: CNPJ, número da Licitação e da Ata de Registro de Preços
- Nenhum pagamento enquanto houver pendência da CONTRATADA
- Atraso no pagamento: correção monetária pelos mesmos critérios de obrigações tributárias
- Pagamento de combustíveis: preço de bomba, na data do abastecimento, limitado ao máximo ANP
- Pagamento de aditivos/lubrificantes/filtros: valor de mercado na data do abastecimento
- Somente gastos realizados junto à rede credenciada

=== CLÁUSULA 5 — REAJUSTE ===
- Taxa de Administração: FIXA e IRREAJUSTÁVEL durante toda a vigência e prorrogações
- Revisão de preços: possível por álea econômica extraordinária (art. 124, II, d, Lei 14.133/2021)

=== CLÁUSULA 6 — VIGÊNCIA ===
- 12 (doze) meses contados da data de publicação no PNCP
- Pode ser prorrogada por até 10 anos (art. 107, Lei 14.133/2021)
- Prorrogação exige: interesse das partes, preços compatíveis, condições de habilitação

=== CLÁUSULA 7 — DOTAÇÃO ORÇAMENTÁRIA ===
- Indicação da dotação orçamentária do CONTRATANTE
- Referência: art. 150, Lei 14.133/2021

=== CLÁUSULA 8 — OBRIGAÇÕES DA CONTRATADA ===
- Manter equipe de implantação (30 dias)
- Suporte: 0800 (fora do horário comercial) + consultor dedicado (horário comercial)
- Rede credenciada: todos os postos disponíveis no município e no mínimo 20 por estado
- Cartões/etiquetas em até 5 dias úteis após solicitação
- Implantação completa em 30 dias corridos da assinatura
- Relatórios gerenciais em até 5 dias úteis após solicitação
- Correção de vícios em até 15 dias da notificação
- Backup de dados: 10 anos
- CKAN operacional durante toda a vigência

=== CLÁUSULA 9 — OBRIGAÇÕES DO CONTRATANTE ===
- Designar gestor e fiscal do contrato
- Fornecer informações necessárias (cadastro da frota)
- Facilitar acesso para implantação
- Pagamento dentro do prazo

=== CLÁUSULA 10 — OBRIGAÇÕES DO INTERVENIENTE (CINCATARINA) ===
- Gestão corporativa dos contratos
- Coordenar e acompanhar a implantação
- Fiscalizar a qualidade dos serviços
- Atendimento 24 horas

=== CLÁUSULA 11 — ALTERAÇÕES ===
- Acréscimos ou supressões: até 25% do valor atualizado
- Supressões por acordo: qualquer percentual
- Fundamentação: art. 124, I, Lei 14.133/2021

=== CLÁUSULA 12 — RESCISÃO ===
- Rescisão possível nas hipóteses legais (Lei 14.133/2021)
- Procedimento: notificação com prazo de defesa

=== CLÁUSULA 13 — SANÇÕES ===
- Multa por atraso: 0,5% por dia sobre o valor mensal, a partir do 6º dia útil
- Multa por inexecução parcial: 10% do valor mensal do contrato
- Multa por inexecução total: 15% do valor global do contrato
- Advertência, impedimento de licitar, declaração de inidoneidade: art. 156, IV, Lei 14.133/2021
- Infrações: art. 155, Lei 14.133/2021
- Procedimento: arts. 156 a 163, Lei 14.133/2021
- Multa: recolhimento no prazo da decisão, sob pena de cobrança judicial

=== CLÁUSULA 14 — FISCALIZAÇÃO ===
- Fiscalização ampla e irrestrita pelo CONTRATANTE
- Irregularidades: comunicação escrita ao CINCATARINA
- Fiscalização não exclui responsabilidade da CONTRATADA
- CONTRATADA deve regularizar após notificação sem ônus adicional

=== CLÁUSULAS 15-17 — REQUISITOS TÉCNICOS DO SISTEMA ===
- Integração por arquivos eletrônicos (.csv, .xls ou mais atual)
- CKAN para dados abertos
- Dados disponíveis em tempo real via WEB (24h, apenas navegador)
- Suporte 24h; consultor dedicado em horário comercial; 0800 fora do horário
- Restrições de uso dos cartões: dia/semana, km, tipo de combustível, horário, valor, cota
- Rastreamento de acesso por data/hora
- Dados de transação: data, horário, estabelecimento, autorização, motorista, veículo,
  tipo de combustível, quantidade, valor unitário, hodômetro
- Relatórios exportáveis: .xls, .csv, .odt
- Sem limite de intervalo temporal para exportação
- Alerta de troca de lubrificante: 1.000 km de antecedência OU 1 semana antes do vencimento
- Mapa de postos com zoom, identificação, preços e elaboração de rotas

=== CLÁUSULA 19 — ATRIBUIÇÕES DO INTERVENIENTE (CINCATARINA) ===
- Gestão corporativa centralizada
- Processar e aprovar contratos administrativos
- Coordenar implantação
- Fiscalizar qualidade
- Aprovar/acompanhar penalizações (CONTRATANTE deve notificar antes)

=== CLÁUSULA 20 — VINCULAÇÃO LICITATÓRIA ===
- Processo Administrativo Licitatório Eletrônico n° 0072/2023-e
- Pregão Eletrônico nº 0076/2023
- Órgão Gerenciador e Interveniente: CINCATARINA

=== CLÁUSULA 21 — FORO ===
- Foro EXCLUSIVO: Comarca da Capital do Estado de Santa Catarina (Florianópolis/SC)

=== PONTOS CRÍTICOS DE VERIFICAÇÃO ===
1. Prazo de pagamento: deve ser até o 20º dia do mês subsequente
2. Taxa de Administração: deve ser fixa e irreajustável
3. Prazo de vigência: deve ser 12 meses contados da publicação no PNCP
4. Multas: 0,5%/dia (a partir do 6º), 10% parcial, 15% total
5. Foro: deve ser Florianópolis/SC (Capital do Estado de SC)
6. Acréscimos/supressões: limite de 25%
7. Dados: guarda por 10 anos
8. Atendimento CINCATARINA: 24 horas
9. Correção de vícios: 15 dias
10. Relatórios: 5 dias úteis
11. Partes: deve haver CONTRATANTE, CONTRATADA e INTERVENIENTE (CINCATARINA)
12. Suporte técnico: 24h + consultor dedicado + 0800
"""

# =========================================================================
# PROMPT para análise de Minuta Padrão — agora inclui mapeamento cláusula a cláusula
# =========================================================================
PROMPT_ANALISE = """
{contexto_minuta}

=== CONTRATO RECEBIDO PARA ANÁLISE ===
Município: {municipio}
Número do Contrato: {numero_contrato}
Data: {data_contrato}

Texto completo do contrato:
{texto_contrato}

=== INSTRUÇÕES DE ANÁLISE ===
Analise o contrato acima com base no seu conhecimento da MINUTA PADRÃO do CINCATARINA.
NÃO faça comparação textual palavra por palavra.
ENTENDA o conteúdo jurídico e verifique se as DISPOSIÇÕES estão em conformidade.

IMPORTANTE: Mapeie TODAS as cláusulas do contrato, uma a uma, indicando o conteúdo resumido
e se está conforme com a minuta padrão. Inclua tanto cláusulas com problema quanto as OK.

Retorne sua análise OBRIGATORIAMENTE no seguinte formato JSON:
{{
  "status_geral": "CONFORME" | "COM DIVERGÊNCIAS" | "COM DIVERGÊNCIAS CRÍTICAS",
  "municipio": "{municipio}",
  "numero_contrato": "{numero_contrato}",
  "data_analise": "{data_hoje}",
  "resumo_executivo": "texto resumido de 2-3 frases",
  "mapeamento_clausulas": [
    {{
      "clausula": "CLÁUSULA 1ª — DO OBJETO",
      "resumo_contrato": "breve resumo do que o contrato diz nesta cláusula",
      "resumo_minuta": "breve resumo do que a minuta padrão prevê",
      "status": "CONFORME" | "DIVERGENTE" | "PARCIALMENTE CONFORME" | "NÃO LOCALIZADA",
      "observacao": "detalhes da comparação ou divergência"
    }}
  ],
  "apontamentos": [
    {{
      "clausula": "número/nome da cláusula",
      "tipo": "DIVERGÊNCIA CRÍTICA" | "DIVERGÊNCIA" | "CLÁUSULA EXTRA" | "CLÁUSULA FALTANTE" | "ALERTA",
      "descricao": "descrição clara do problema",
      "previsto_minuta": "o que a minuta padrão determina",
      "encontrado_contrato": "o que consta no contrato analisado"
    }}
  ],
  "prazos_verificados": {{
    "prazo_pagamento": {{"previsto": "até o 20º dia do mês subsequente", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
    "prazo_vigencia": {{"previsto": "12 meses a partir do PNCP", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
    "prazo_correcao_vicios": {{"previsto": "15 dias", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
    "prazo_relatorios": {{"previsto": "5 dias úteis", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}}
  }},
  "valores_verificados": {{
    "taxa_administracao": {{"encontrado": "...", "status": "INFORMADO" | "NÃO LOCALIZADO"}},
    "valor_estimado": {{"encontrado": "...", "status": "INFORMADO" | "NÃO LOCALIZADO"}}
  }},
  "multas_verificadas": {{
    "multa_atraso_diaria": {{"previsto": "0,5%/dia a partir do 6º dia", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
    "multa_inexecucao_parcial": {{"previsto": "10%", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
    "multa_inexecucao_total": {{"previsto": "15%", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}}
  }},
  "foro_verificado": {{"previsto": "Comarca da Capital do Estado de SC", "encontrado": "...", "status": "OK" | "DIVERGENTE" | "NÃO LOCALIZADO"}},
  "partes_verificadas": {{
    "contratante": {{"encontrado": "...", "status": "OK" | "AUSENTE"}},
    "contratada": {{"encontrado": "...", "status": "OK" | "AUSENTE"}},
    "interveniente_cincatarina": {{"encontrado": "...", "status": "OK" | "AUSENTE"}}
  }},
  "clausulas_extras": ["lista de cláusulas presentes no contrato que NÃO existem na minuta padrão"],
  "clausulas_faltantes": ["lista de cláusulas da minuta padrão que estão AUSENTES no contrato"]
}}

Responda APENAS com o JSON válido, sem markdown, sem texto fora do JSON.
"""

# =========================================================================
# PROMPT para análise de Termos Aditivos
# =========================================================================
PROMPT_TERMOS_ADITIVOS = """Você é um analista jurídico especializado em contratos públicos brasileiros e termos aditivos.
Analise os documentos abaixo e identifique TODAS as divergências, alterações e inconsistências
entre o contrato original, os termos aditivos anteriores (em ORDEM CRONOLÓGICA) e o NOVO termo aditivo.

=== CONTRATO ORIGINAL ===
{texto_original}

=== TERMOS ADITIVOS ANTERIORES (ORDEM CRONOLÓGICA) ===
{termos_anteriores}

=== NOVO TERMO ADITIVO (para análise) ===
{texto_novo}

IMPORTANTE: Mapeie TODAS as cláusulas tanto do contrato original quanto do novo termo,
indicando o conteúdo resumido e se houve alteração ao longo dos aditivos.

Analise minuciosamente e responda APENAS com JSON válido sem markdown, seguindo EXATAMENTE esta estrutura:
{{
  "status_geral": "CONFORME" | "COM DIVERGÊNCIAS" | "COM DIVERGÊNCIAS CRÍTICAS",
  "numero_contrato": "número identificado ou vazio",
  "objeto_contrato": "descrição do objeto",
  "partes": {{
    "contratante": "nome identificado",
    "contratada": "nome identificado",
    "outros": []
  }},
  "assinantes_novo_termo": [
    {{"nome": "", "cargo": "", "presente_em_anteriores": true | false, "observacao": ""}}
  ],
  "resumo_executivo": "Parágrafo descritivo resumindo o resultado da análise",
  "mapeamento_clausulas": [
    {{
      "clausula": "CLÁUSULA 1ª — DO OBJETO",
      "resumo_original": "breve resumo do contrato original",
      "resumo_anteriores": "alterações feitas nos termos anteriores (ou N/A)",
      "resumo_novo_termo": "o que o novo termo diz",
      "status": "MANTIDA" | "ALTERADA" | "NOVA" | "REMOVIDA",
      "observacao": "detalhes"
    }}
  ],
  "divergencias": [
    {{
      "tipo": "DIVERGÊNCIA CRÍTICA" | "DIVERGÊNCIA" | "ALERTA" | "CLÁUSULA EXTRA" | "CLÁUSULA FALTANTE",
      "categoria": "PRAZO" | "VALOR" | "DATA" | "ASSINANTE" | "RESPONSÁVEL" | "CLÁUSULA" | "OBJETO" | "OUTRO",
      "clausula": "identificação da cláusula/seção",
      "previsto": "o que estava previsto no contrato original ou termo anterior",
      "encontrado": "o que foi encontrado no novo termo",
      "descricao": "explicação detalhada da divergência e seu impacto jurídico"
    }}
  ],
  "prazos": [
    {{"item": "nome do prazo", "contrato_original": "valor", "termos_anteriores": "valor ou N/A", "novo_termo": "valor", "status": "OK" | "ALTERADO" | "DIVERGENTE" | "NÃO LOCALIZADO"}}
  ],
  "valores": [
    {{"item": "descrição do valor", "contrato_original": "R$ X", "termos_anteriores": "R$ X ou N/A", "novo_termo": "R$ X", "status": "OK" | "ALTERADO" | "DIVERGENTE" | "NÃO LOCALIZADO"}}
  ],
  "datas": [
    {{"item": "descrição da data", "contrato_original": "data", "termos_anteriores": "data ou N/A", "novo_termo": "data", "status": "OK" | "ALTERADO" | "DIVERGENTE" | "NÃO LOCALIZADO"}}
  ],
  "clausulas_extras": ["lista de cláusulas presentes no novo termo mas não previstas anteriormente"],
  "clausulas_faltantes": ["lista de cláusulas previstas mas ausentes no novo termo"],
  "data_analise": "{data_hoje}"
}}
Responda APENAS com o JSON. Sem texto fora do JSON."""

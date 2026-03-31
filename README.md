# 📊 INDEI Dashboard: Inteligência de Ecossistemas de Impacto

![Status do Projeto](https://img.shields.io/badge/status-em_desenvolvimento-orange)
![Versão](https://img.shields.io/badge/versão-2.0.0--beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)

O **INDEI (Índice de Ecossistemas de Impacto)** é uma ferramenta analítica de vanguarda projetada para diagnosticar a maturidade sistêmica dos 5.570 municípios brasileiros. Diferente de índices tradicionais, o INDEI utiliza uma abordagem holística e decolonial, integrando as dimensões econômica, sociocultural e ambiental para mapear o desenvolvimento territorial real.

Esta dashboard é a evolução tecnológica do relatório lançado no **Museu do Amanhã (2025/2026)**, automatizando a coleta, o processamento e a visualização dos dados.

---

## 🧭 Visão Geral e Metodologia

O INDEI é sustentado por uma arquitetura de **3 Eixos** e **20 Subgrupos** de indicadores:

* **🟢 Econômico-Empresarial (EC):** Densidade, conectividade, diversidade e geração de economia de impacto.
* **🟡 Sociocultural (SOC):** Talento, infraestrutura cultural, qualidade de vida e saúde coletiva.
* **🔵 Ambiental (MED):** Resiliência urbana, economia verde, saneamento e consumo responsável.

### A "Engrenagem" Matemática
* **Normalização:** Todos os dados são normalizados na escala **0 a 10** com base no líder do indicador (*Benchmarking*).
* **Peso Unitário:** Adotamos o peso unitário para todos os eixos, reforçando que o equilíbrio ecossistêmico é o que define o sucesso a longo prazo.

---

## 🛠️ Stack Tecnológica

Este projeto utiliza ferramentas de ponta para garantir escalabilidade e reprodutibilidade:

* **Linguagem:** [Python 3.10+](https://www.python.org/)
* **Frontend/Dashboard:** [Streamlit](https://streamlit.io/) / [Plotly](https://plotly.com/python/) (ou sua escolha: Dash/PowerBI/Shiny)
* **Manipulação de Dados:** Pandas, NumPy
* **Geospatial:** Geopandas, Folium
* **Automação (ETL):** Integração via API (SIDRA/IBGE, DATASUS)

---

## 🚀 Funcionalidades Planejadas

- [ ] **Mapa Interativo:** Visualização de calor por eixo em todos os municípios brasileiros.
- [ ] **Comparador de Cidades:** Análise lado a lado (Gráfico de Radar) para identificar "Gaps de Conversão".
- [ ] **Filtros Avançados:** Segmentação por porte populacional, estado e bioma.
- [ ] **Relatórios Automatizados:** Exportação de PDFs com diagnósticos específicos por município.
- [ ] **API de Dados:** Acesso público aos dados normalizados do INDEI.

---

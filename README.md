Quality Performance Dashboard

 Acesse o projeto

**Dashboard online:** https://apresentacaoolegrand.streamlit.app/

## Sobre o projeto

O **Quality Performance Dashboard** é um protótipo desenvolvido em Python e Streamlit para demonstrar como a análise de dados pode contribuir para o acompanhamento da qualidade em um ambiente industrial.

A aplicação centraliza informações de planilhas Excel em um painel interativo, facilitando a visualização de indicadores, a análise de defeitos e o acompanhamento de não conformidades.

Este projeto foi desenvolvido por iniciativa própria, com o objetivo de aplicar conhecimentos de programação, análise de dados e melhoria contínua em uma situação prática.

**Importante:** todos os dados utilizados são fictícios e servem exclusivamente para fins demonstrativos. Não representam dados reais da LEGRAND.

## Funcionalidades

- **Indicadores de qualidade:** acompanhamento de PPM, custos da não qualidade e não conformidades.
- **Análise da produção:** comparação entre volume produzido e quantidade de itens defeituosos.
- **Análise de defeitos:** visualização das ocorrências por categoria e setor, com análise de Pareto.
- **Acompanhamento de não conformidades:** consulta de status, responsáveis e ações corretivas registradas.
- **Validação de dados:** identificação de possíveis inconsistências, campos vazios, datas inválidas e identificadores duplicados.
- **Exploração de planilhas:** consulta às informações utilizadas para alimentar os indicadores.

## Tecnologias utilizadas

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Excel
- GitHub
- Streamlit Community Cloud

## Como funciona

1. Os dados são disponibilizados em uma planilha Excel estruturada.
2. A aplicação utiliza Pandas para ler, organizar e processar as informações.
3. Os indicadores são calculados e apresentados em gráficos, tabelas e cartões interativos.
4. As validações ajudam a identificar registros que precisam de revisão.
5. O usuário pode explorar os dados e analisar os resultados disponíveis no painel.

## Como executar localmente

### 1. Clone o repositório

```bash
(https://github.com/alissonneckel13-sys?tab=repositories)
```



### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
streamlit run app.py
```

O Streamlit disponibilizará um endereço local para abrir o dashboard no navegador.

## Possíveis melhorias futuras

- Atualização automatizada dos dados.
- Definição de metas por setor ou processo.
- Relatórios periódicos de desempenho.
- Acompanhamento de prazos das ações corretivas.
- Integração com fontes oficiais de dados, conforme os requisitos da empresa.

## Objetivo profissional

Este projeto demonstra iniciativa, aprendizado prático e interesse em utilizar tecnologia e análise de dados para apoiar a qualidade industrial, identificar oportunidades de melhoria e facilitar a tomada de decisão.

Desenvolvido como protótipo demonstrativo, com foco em análise de dados, visualização de indicadores e melhoria contínua.

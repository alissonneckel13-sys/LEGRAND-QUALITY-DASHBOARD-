import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Quality Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# -------------------- VISUAL --------------------
st.markdown("""
<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {
    background-color:#F4F7FB !important; color:#183153 !important;
}
[data-testid="stSidebar"] {background:#FFFFFF !important;}
h1,h2,h3,p,label {color:#183153;}
[data-testid="stMetric"] {
    background:#FFFFFF; border:1px solid #D7E3F2; border-radius:12px;
    padding:16px; box-shadow:0 3px 12px rgba(18,74,140,.06);
}
[data-testid="stDataFrame"],[data-testid="stTable"] {
    background:#FFFFFF; border:1px solid #D7E3F2; border-radius:10px;
}
.block-container {padding-top:1.5rem; padding-bottom:2rem; max-width:1600px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Quality Performance Dashboard")
st.caption("Indicadores de qualidade, validação de dados e apoio à decisão")
st.info("DEMONSTRAÇÃO — os dados da planilha fornecida são fictícios e não representam dados reais da Legrand.")

# -------------------- LOAD WORKBOOK --------------------
st.sidebar.header("📁 Fonte dos dados")
st.sidebar.write("Envie um arquivo Excel para analisar, ou use a base de demonstração.")
uploaded = st.sidebar.file_uploader("Carregar arquivo Excel (.xlsx)", type=["xlsx"])
app_folder = Path(__file__).resolve().parent
# Procura primeiro os nomes esperados e depois qualquer .xlsx na pasta do app.
possible_names = ["base_qualidade.xlsx", "base_qualidade_melhorada.xlsx"]
default_path = next((app_folder / name for name in possible_names if (app_folder / name).is_file()), None)
if default_path is None:
    excel_candidates = sorted(
        p for p in app_folder.glob("*.xlsx")
        if p.is_file() and not p.name.startswith("~$")
    )
    if excel_candidates:
        default_path = excel_candidates[0]

@st.cache_data(show_spinner=False)
def get_sheet_names(file_bytes):
    # Retorne uma lista simples, serializável pelo cache do Streamlit.
    return pd.ExcelFile(BytesIO(file_bytes)).sheet_names

@st.cache_data(show_spinner=False)
def read_sheet(file_bytes, sheet_name):
    # Bytes são usados como entrada para funcionar tanto com upload quanto com arquivo local.
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

source = uploaded if uploaded is not None else default_path
if source is None:
    st.warning("Não encontrei nenhum arquivo .xlsx na pasta do app. Na barra lateral, clique em 'Carregar arquivo Excel (.xlsx)' e selecione sua planilha.")
    st.stop()

try:
    file_bytes = source.getvalue() if uploaded is not None else default_path.read_bytes()
    sheet_names = get_sheet_names(file_bytes)
    sheets = {name: read_sheet(file_bytes, name) for name in sheet_names}
except Exception as e:
    st.error(f"Não foi possível ler o arquivo. Confirme se é um Excel .xlsx válido. Detalhe: {e}")
    st.stop()

# -------------------- DATA VALIDATION --------------------
st.sidebar.divider()
st.sidebar.subheader("Validação")
st.sidebar.caption("As verificações sinalizam possíveis problemas; confirme antes de corrigir a planilha original.")

required_sheets = {
    "Producao": ["Mes", "Produzido", "Defeituosos", "Refugo_R$"],
    "Defeitos": ["Data", "Tipo_Defeito", "Setor", "Ocorrencias"],
    "CNQ": ["Data", "Categoria", "Descricao", "Valor_R$"],
    "Nao_Conformidades": ["ID", "Data", "Descricao", "Setor", "Responsavel", "Status", "Acao_Corretiva"],
}
issues = []

for sheet, required_cols in required_sheets.items():
    if sheet not in sheet_names:
        issues.append({"Aba": sheet, "Linha Excel": "—", "Coluna/campo": "Aba inteira", "Problema": "Aba obrigatória ausente", "Detalhe": f"Esperada a aba '{sheet}'."})
        continue
    df = sheets[sheet]
    for col in required_cols:
        if col not in df.columns:
            issues.append({"Aba": sheet, "Linha Excel": "—", "Coluna/campo": col, "Problema": "Coluna obrigatória ausente", "Detalhe": f"A coluna '{col}' não foi encontrada."})
        else:
            blank = df[col].isna()
            if df[col].dtype == "object":
                blank = blank | df[col].astype("string").str.strip().eq("").fillna(False)
            for idx in df.index[blank]:
                issues.append({"Aba": sheet, "Linha Excel": int(idx) + 2, "Coluna/campo": col, "Problema": "Campo vazio", "Detalhe": "Preencha ou confirme se o campo pode ficar vazio."})

if "Nao_Conformidades" in sheets and "ID" in sheets["Nao_Conformidades"].columns:
    df = sheets["Nao_Conformidades"]
    ids = df["ID"].astype("string").str.strip()
    duplicated = ids.notna() & ids.ne("") & ids.duplicated(keep=False)
    for idx in df.index[duplicated]:
        issues.append({"Aba": "Nao_Conformidades", "Linha Excel": int(idx) + 2, "Coluna/campo": "ID", "Problema": "ID duplicado", "Detalhe": f"ID '{ids.loc[idx]}' aparece em mais de uma linha."})

date_cols = {"Defeitos": ["Data"], "CNQ": ["Data"], "Nao_Conformidades": ["Data"]}
for sheet, cols in date_cols.items():
    if sheet not in sheets:
        continue
    df = sheets[sheet]
    for col in cols:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid = df[col].notna() & parsed.isna()
            for idx in df.index[invalid]:
                issues.append({"Aba": sheet, "Linha Excel": int(idx) + 2, "Coluna/campo": col, "Problema": "Data inválida", "Detalhe": f"Valor recebido: {df.loc[idx, col]}"})

numeric_rules = {
    "Producao": {"Produzido": "positive", "Defeituosos": "nonnegative", "Refugo_R$": "nonnegative"},
    "Defeitos": {"Ocorrencias": "nonnegative"},
    "CNQ": {"Valor_R$": "nonnegative"},
}
for sheet, rules in numeric_rules.items():
    if sheet not in sheets:
        continue
    df = sheets[sheet]
    for col, rule in rules.items():
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        bad_numeric = df[col].notna() & values.isna()
        bad_range = values.le(0) if rule == "positive" else values.lt(0)
        bad_range = bad_range.fillna(False)
        for idx in df.index[bad_numeric]:
            issues.append({"Aba": sheet, "Linha Excel": int(idx) + 2, "Coluna/campo": col, "Problema": "Valor não numérico", "Detalhe": f"Valor recebido: {df.loc[idx, col]}"})
        for idx in df.index[bad_range]:
            issues.append({"Aba": sheet, "Linha Excel": int(idx) + 2, "Coluna/campo": col, "Problema": "Valor fora da regra", "Detalhe": "Produzido deve ser maior que zero; os demais valores não podem ser negativos."})

issues_df = pd.DataFrame(issues, columns=["Aba", "Linha Excel", "Coluna/campo", "Problema", "Detalhe"])

tab_dashboard, tab_validation, tab_data = st.tabs(["📈 Painel gerencial", "🔎 Qualidade dos dados", "📂 Explorar planilhas"])

with tab_validation:
    st.subheader("Validação automática da base")
    c1, c2, c3 = st.columns(3)
    c1.metric("Abas encontradas", len(sheet_names))
    c2.metric("Problemas sinalizados", len(issues_df))
    c3.metric("Status", "Revisar" if len(issues_df) else "Sem alertas")
    if issues_df.empty:
        st.success("Nenhum dos problemas verificados foi encontrado. Isso não garante que todos os dados estejam corretos; revise também as regras do processo.")
    else:
        st.warning("Foram encontrados possíveis problemas. Verifique as linhas indicadas antes de alterar a base original.")
        st.dataframe(issues_df, use_container_width=True, hide_index=True)
        csv = issues_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Baixar relatório de validação (CSV)", data=csv, file_name="relatorio_validacao_qualidade.csv", mime="text/csv")
    st.caption("Número de linha informado considera a primeira linha como cabeçalho do Excel. A ferramenta identifica sinais de inconsistência, mas não corrige o arquivo automaticamente.")

with tab_data:
    st.subheader("Explorar abas e registros")
    chosen_sheet = st.selectbox("Selecione uma aba", sheet_names)
    selected_df = sheets[chosen_sheet]
    st.caption(f"{len(selected_df)} linhas · {len(selected_df.columns)} colunas")
    st.dataframe(selected_df, use_container_width=True, hide_index=True)
    csv = selected_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Baixar esta aba em CSV", data=csv, file_name=f"{chosen_sheet}.csv", mime="text/csv")

with tab_dashboard:
    if "Producao" not in sheets:
        st.error("A aba Producao é necessária para montar o painel.")
        st.stop()
    producao = sheets["Producao"].copy()
    required_prod = ["Mes", "Produzido", "Defeituosos", "Refugo_R$"]
    if not all(col in producao.columns for col in required_prod):
        st.error("A aba Producao precisa conter: Mes, Produzido, Defeituosos e Refugo_R$. Veja a aba Qualidade dos dados.")
        st.stop()

    for col in ["Produzido", "Defeituosos", "Refugo_R$"]:
        producao[col] = pd.to_numeric(producao[col], errors="coerce")
    producao = producao.dropna(subset=["Mes", "Produzido", "Defeituosos"])
    producao = producao[producao["Produzido"] > 0].copy()
    if producao.empty:
        st.warning("Não há dados válidos de produção para os indicadores.")
        st.stop()

    producao["PPM"] = producao["Defeituosos"] / producao["Produzido"] * 1_000_000
    meses = producao["Mes"].astype(str).tolist()
    periodo = st.selectbox("Período de produção", ["Todos os meses"] + meses, key="periodo_prod")
    filtro = producao.copy() if periodo == "Todos os meses" else producao[producao["Mes"].astype(str) == periodo].copy()
    meta_ppm = st.number_input("Meta de PPM (demonstrativa)", min_value=0, value=15000, step=500)
    ppm_atual = float(filtro.iloc[-1]["PPM"])
    if ppm_atual <= meta_ppm:
        st.success(f"PPM do período selecionado está dentro da meta ({meta_ppm:,.0f}).".replace(",", "."))
    else:
        st.error(f"PPM do período selecionado está acima da meta ({meta_ppm:,.0f}).".replace(",", "."))

    cnq = sheets.get("CNQ", pd.DataFrame())
    nc = sheets.get("Nao_Conformidades", pd.DataFrame())
    defeitos = sheets.get("Defeitos", pd.DataFrame())
    cnq_total = pd.to_numeric(cnq["Valor_R$"], errors="coerce").fillna(0).sum() if "Valor_R$" in cnq.columns else 0
    total_nc = len(nc)
    abertas = int(nc["Status"].astype("string").str.lower().str.strip().isin(["aberta", "em andamento", "pendente"]).sum()) if "Status" in nc.columns else 0

    a, b, c, d = st.columns(4)
    a.metric(f"PPM — {filtro.iloc[-1]['Mes']}", f"{ppm_atual:,.0f}".replace(",", "."))
    b.metric("CNQ acumulado", f"R$ {cnq_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c.metric("Não conformidades", total_nc)
    d.metric("NC abertas / em andamento", abertas)

    left, right = st.columns(2)
    with left:
        st.subheader("Evolução mensal do PPM")
        fig = px.line(filtro, x="Mes", y="PPM", markers=True, text="PPM", template="plotly_white")
        fig.update_traces(line=dict(color="#2F80ED", width=3), marker=dict(size=9), texttemplate="%{text:.0f}", textposition="top center")
        fig.add_hline(y=meta_ppm, line_dash="dash", line_color="#E67E22", annotation_text=f"Meta: {meta_ppm:,.0f}".replace(",", "."))
        fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#183153", margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Produção x defeituosos")
        fig2 = px.bar(filtro, x="Mes", y=["Produzido", "Defeituosos"], barmode="group", template="plotly_white")
        fig2.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#183153", margin=dict(l=20,r=20,t=40,b=20), legend_title_text="")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Pareto — principais tipos de defeito")
    if {"Tipo_Defeito", "Ocorrencias"}.issubset(defeitos.columns) and not defeitos.empty:
        defeitos["Ocorrencias"] = pd.to_numeric(defeitos["Ocorrencias"], errors="coerce").fillna(0)
        pareto = defeitos.groupby("Tipo_Defeito", as_index=False)["Ocorrencias"].sum().sort_values("Ocorrencias", ascending=False)
        total = pareto["Ocorrencias"].sum()
        if total > 0:
            pareto["Percentual acumulado"] = pareto["Ocorrencias"].cumsum() / total * 100
            fig3 = px.bar(pareto, x="Tipo_Defeito", y="Ocorrencias", text="Ocorrencias", template="plotly_white")
            fig3.update_traces(marker_color="#2F80ED", textposition="outside")
            fig3.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#183153", margin=dict(l=20,r=20,t=30,b=50))
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(pareto, use_container_width=True, hide_index=True)
        else:
            st.info("Não há ocorrências positivas para calcular o Pareto.")
    else:
        st.info("A aba Defeitos precisa conter Tipo_Defeito e Ocorrencias.")

    st.subheader("Detalhamento de não conformidades")
    if not nc.empty:
        status_filter = "Todos"
        if "Status" in nc.columns:
            statuses = ["Todos"] + sorted(nc["Status"].fillna("Sem status").astype(str).unique().tolist())
            status_filter = st.selectbox("Filtrar por status", statuses, key="status_nc")
        nc_view = nc.copy() if status_filter == "Todos" or "Status" not in nc.columns else nc[nc["Status"].fillna("Sem status").astype(str) == status_filter]
        st.dataframe(nc_view, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma não conformidade registrada.")

    st.subheader("Detalhamento do custo da não qualidade")
    if not cnq.empty:
        st.dataframe(cnq, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de CNQ encontrado.")

st.divider()
st.caption("Quality Performance Dashboard | Protótipo demonstrativo. Confirme os dados e as regras de negócio antes de usar em ambiente real.")

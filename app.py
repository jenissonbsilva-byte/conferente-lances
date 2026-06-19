import streamlit as st
import pandas as pd
import os
from fpdf import FPDF

# Configuração da página
st.set_page_config(page_title="Conferente de Lances", page_icon="📊", layout="wide")

# Inicializa a variável de controle para o botão "Nova Conferência"
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

def resetar_app():
    """Função para limpar o arquivo enviado e iniciar nova conferência."""
    st.session_state["file_uploader_key"] += 1

def gerar_pdf(alertas, info_pregao, info_emissao):
    """Gera um arquivo PDF com a tabela de inconsistências."""
    pdf = FPDF(orientation="L", unit="mm", format="A4") # Formato Paisagem
    pdf.add_page()
    
    # Título do Relatório
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Relatório de Conferência de Lances - Drogafonte", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Informações do Pregão
    pdf.set_font("helvetica", "", 10)
    safe_pregao = info_pregao.encode('latin-1', 'replace').decode('latin-1')
    safe_emissao = info_emissao.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, safe_pregao, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, safe_emissao, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Cabeçalho da Tabela
    pdf.set_font("helvetica", "B", 9)
    col_widths = [15, 35, 105, 25, 25, 25, 40]
    headers = ["Item", "Alerta", "Descrição", "Vlr Inicial", "Lim. 40%", "Lance", "Diferença"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln()
    
    # Linhas da Tabela
    pdf.set_font("helvetica", "", 8)
    for alerta in alertas:
        desc = alerta["Descrição"]
        desc = (desc[:60] + "...") if len(desc) > 60 else desc
        desc = desc.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(col_widths[0], 8, str(alerta["Item"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, alerta["Tipo de Alerta"], border=1, align="C")
        pdf.cell(col_widths[2], 8, desc, border=1)
        pdf.cell(col_widths[3], 8, f"R$ {alerta['Valor Inicial (R$)']}", border=1, align="C")
        pdf.cell(col_widths[4], 8, f"R$ {alerta['Limite 40% (R$)']}", border=1, align="C")
        pdf.cell(col_widths[5], 8, f"R$ {alerta['Lance (R$)']}", border=1, align="C")
        
        dif = str(alerta['Diferença / Desconto']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_widths[6], 8, dif, border=1, align="C")
        pdf.ln()
        
    return bytes(pdf.output())

# --- CABEÇALHO COM LOGO ---
if os.path.exists("logo_drogafonte (1).png"):
    st.image("logo_drogafonte (1).png", width=250)
else:
    st.info("💡 Dica: Suba o arquivo 'logo_drogafonte (1).png' no seu GitHub para exibir a logo aqui.")

st.title("📊 Conferente de Lances de Pregão")
st.write("Identifique automaticamente lances com descontos excessivos ou valores acima do Valor Inicial.")

col_titulo, col_botao = st.columns([4, 1])
with col_botao:
    st.button("🔄 Nova Conferência", on_click=resetar_app, use_container_width=True)

uploaded_file = st.file_uploader(
    "Selecione o relatório (.xls, .xlsx ou .csv)", 
    type=["csv", "xls", "xlsx"], 
    key=str(st.session_state["file_uploader_key"])
)

if uploaded_file is not None:
    try:
        # --- 1. IDENTIFICAÇÃO DO CABEÇALHO ---
        if uploaded_file.name.endswith('.csv'):
            df_cabecalho = pd.read_csv(uploaded_file, nrows=5, header=None, encoding='utf-8')
        else:
            df_cabecalho = pd.read_excel(uploaded_file, nrows=5, header=None)
        
        info_pregao = str(df_cabecalho.iloc[3, 0]) if len(df_cabecalho) > 3 else "Informação do pregão não encontrada"
        info_emissao = str(df_cabecalho.iloc[4, 0]) if len(df_cabecalho) > 4 else "Informação de emissão não encontrada"
        
        st.info(f"**Identificação do Relatório:**\n\n📌 {info_pregao}\n\n⏱️ {info_emissao}")
        
        uploaded_file.seek(0)
        
        # --- 2. PROCESSAMENTO DOS DADOS ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=6)
        else:
            df = pd.read_excel(uploaded_file, skiprows=6)
            
        df.columns = df.columns.str.strip()
        
        lances_acima = []
        descontos_excessivos = []
        todos_alertas = []
        
        coluna_desc = '--------------------------------- D i s c r i m i n a ç ã o ---------------------------------'
        
        for index, row in df.iterrows():
            try:
                vlr_unit = float(row['Vlr. Unit.'])
                lance = float(row['Lance'])
                item = row['Item']
                limite_minimo = vlr_unit * 0.60 # Calcula o limite de 40%
                
                descricao = str(row[coluna_desc])[:80].replace('\n', ' ') + "..." if coluna_desc in row else "Sem descrição"
                
                # Regra 1: Lance MAIOR que o Valor Inicial
                if lance > vlr_unit:
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": "ACIMA DO VALOR",
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Limite 40% (R$)": round(limite_minimo, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"R$ {(lance - vlr_unit):.4f} a mais"
                    }
                    lances_acima.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                    continue
                    
                # Regra 2: Desconto de MAIS DE 40%
                if lance < limite_minimo:
                    desconto_perc = ((vlr_unit - lance) / vlr_unit) * 100
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": "DESCONTO > 40%",
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Limite 40% (R$)": round(limite_minimo, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"{desconto_perc:.1f}% de desconto"
                    }
                    descontos_excessivos.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                    
            except (ValueError, TypeError):
                continue
            except KeyError as e:
                st.error(f"Erro: Coluna {e} não encontrada. O arquivo não está no padrão esperado.")
                st.stop()
                
        # --- 3. EXIBIÇÃO E DOWNLOAD ---
        st.divider()
        st.subheader("Resultados da Conferência")
        
        col1, col2 = st.columns(2)
        col1.metric("Lances ACIMA do Valor Inicial", len(lances_acima))
        col2.metric("Lances com Desconto > 40%", len(descontos_excessivos))
        
        # Área de Botões de Download
        if todos_alertas:
            col_down1, col_down2 = st.columns(2)
            
            # Botão CSV
            df_export = pd.DataFrame(todos_alertas)
            csv_export = df_export.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
            with col_down1:
                st.download_button(
                    label="📥 Baixar em Excel (CSV)",
                    data=csv_export,
                    file_name="alertas_conferencia.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Botão PDF
            with col_down2:
                pdf_data = gerar_pdf(todos_alertas, info_pregao, info_emissao)
                st.download_button(
                    label="📄 Baixar Relatório em PDF",
                    data=pdf_data,
                    file_name="alertas_conferencia.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            st.write("")
        
        if lances_acima:
            st.error("🚨 Itens com Lance MAIOR que o Valor Inicial:")
            st.dataframe(pd.DataFrame(lances_acima).drop(columns=["Tipo de Alerta"]), use_container_width=True)
            
        if descontos_excessivos:
            st.warning("⚠️ Itens com Desconto EXCESSIVO (Maior que 40% em relação ao Valor Inicial):")
            st.dataframe(pd.DataFrame(descontos_excessivos).drop(columns=["Tipo de Alerta"]), use_container_width=True)
            
        if not todos_alertas:
            st.success("✅ Tudo certo! Nenhum alerta de valor ou desconto encontrado neste arquivo.")
            st.balloons()
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao tentar processar o arquivo: {e}")

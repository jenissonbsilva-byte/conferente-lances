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
    """Gera um arquivo PDF formatado com destaques visuais ou mensagem de sucesso."""
    pdf = FPDF(orientation="L", unit="mm", format="A4") # Formato Paisagem
    pdf.add_page()
    
    # 1. Adiciona a Logo no PDF se ela existir
    if os.path.exists("logo_drogafonte (1).png"):
        pdf.image("logo_drogafonte (1).png", x=10, y=10, w=40)
        pdf.ln(14)
    else:
        pdf.ln(5)
        
    # Título do Relatório
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Relatório de Conferência de Lances", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Informações do Pregão
    pdf.set_font("helvetica", "", 10)
    safe_pregao = info_pregao.encode('latin-1', 'replace').decode('latin-1')
    safe_emissao = info_emissao.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, safe_pregao, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, safe_emissao, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Se não houver alertas, imprime a mensagem de sucesso
    if not alertas:
        pdf.ln(15)
        pdf.set_font("helvetica", "B", 12)
        # Emojis não são suportados nativamente no helvetica do fpdf, então usamos um texto formal
        msg_sucesso = "STATUS: Tudo certo! Nenhum alerta de valor ou desconto encontrado neste arquivo."
        pdf.cell(0, 10, msg_sucesso, align="C", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    # --- Se houver alertas, gera a tabela ---
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    
    col_widths = [15, 35, 105, 25, 25, 25, 40]
    headers = ["Item", "Alerta", "Descrição", "Vlr Inicial", "Lim. 40%", "Lance", "Diferença"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C", fill=True)
    pdf.ln()
    
    bg_vermelho_linha = (255, 214, 214)
    bg_amarelo_lance = (255, 243, 205)
    
    for alerta in alertas:
        is_acima = alerta["Tipo de Alerta"] == "ACIMA DO VALOR"
        fill_row = True if is_acima else False
            
        pdf.set_font("helvetica", "", 8)
        
        if is_acima:
            pdf.set_fill_color(*bg_vermelho_linha)
            
        pdf.cell(col_widths[0], 8, str(alerta["Item"]), border=1, align="C", fill=fill_row)
        
        tipo_alerta_safe = alerta["Tipo de Alerta"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_widths[1], 8, tipo_alerta_safe, border=1, align="C", fill=fill_row)
        
        desc = alerta["Descrição"]
        desc = (desc[:60] + "...") if len(desc) > 60 else desc
        desc = desc.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_widths[2], 8, desc, border=1, fill=fill_row)
        
        pdf.cell(col_widths[3], 8, f"R$ {alerta['Valor Inicial (R$)']}", border=1, align="C", fill=fill_row)
        pdf.cell(col_widths[4], 8, f"R$ {alerta['Limite 40% (R$)']}", border=1, align="C", fill=fill_row)
        
        # Destaque do Lance
        pdf.set_font("helvetica", "B", 10)
        if is_acima:
            pdf.set_fill_color(*bg_vermelho_linha)
        else:
            pdf.set_fill_color(*bg_amarelo_lance)
            
        pdf.cell(col_widths[5], 8, f"R$ {alerta['Lance (R$)']}", border=1, align="C", fill=True)
            
        # Restaura a fonte
        pdf.set_font("helvetica", "", 8)
        if is_acima:
            pdf.set_fill_color(*bg_vermelho_linha)
            
        dif = str(alerta['Diferença / Desconto']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_widths[6], 8, dif, border=1, align="C", fill=fill_row)
        pdf.ln()
        
    return bytes(pdf.output())

# --- CABEÇALHO DA TELA COM LOGO ---
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
        conferencia_geral = [] # Nova lista para armazenar TODOS os itens
        
        coluna_desc = '--------------------------------- D i s c r i m i n a ç ã o ---------------------------------'
        
        for index, row in df.iterrows():
            try:
                vlr_unit = float(row['Vlr. Unit.'])
                lance = float(row['Lance'])
                item = row['Item']
                limite_minimo = vlr_unit * 0.60
                
                descricao = str(row[coluna_desc])[:80].replace('\n', ' ') + "..." if coluna_desc in row else "Sem descrição"
                
                status_item = "OK"
                desconto_perc = ((vlr_unit - lance) / vlr_unit) * 100 if vlr_unit > 0 else 0
                
                # Regra 1: Lance MAIOR que o Valor Inicial
                if lance > vlr_unit:
                    status_item = "ACIMA DO VALOR"
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": status_item,
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Limite 40% (R$)": round(limite_minimo, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"R$ {(lance - vlr_unit):.4f} a mais"
                    }
                    lances_acima.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                    
                # Regra 2: Desconto de MAIS DE 40%
                elif lance < limite_minimo:
                    status_item = "DESCONTO > 40%"
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": status_item,
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Limite 40% (R$)": round(limite_minimo, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"{desconto_perc:.1f}% de desconto"
                    }
                    descontos_excessivos.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                
                # Adiciona na lista geral independentemente de ter alerta ou não
                conferencia_geral.append({
                    "Item": item,
                    "Status": status_item,
                    "Descrição": descricao,
                    "Valor Inicial (R$)": round(vlr_unit, 4),
                    "Limite 40% (R$)": round(limite_minimo, 4),
                    "Lance (R$)": round(lance, 4),
                    "Desconto Aplicado (%)": f"{desconto_perc:.1f}%"
                })
                    
            except (ValueError, TypeError):
                continue
            except KeyError as e:
                st.error(f"Erro: Coluna {e} não encontrada. O arquivo não está no padrão esperado.")
                st.stop()
                
        # --- 3. EXIBIÇÃO EM ABAS E DOWNLOAD ---
        st.divider()
        
        # Cria as duas abas
        aba_alertas, aba_geral = st.tabs(["🚨 Alertas Encontrados", "📋 Conferência Geral (Todos os Itens)"])
        
        with aba_alertas:
            col1, col2 = st.columns(2)
            col1.metric("Lances ACIMA do Valor Inicial", len(lances_acima))
            col2.metric("Lances com Desconto > 40%", len(descontos_excessivos))
            
            # Se existirem alertas
            if todos_alertas:
                col_down1, col_down2 = st.columns(2)
                df_export = pd.DataFrame(todos_alertas)
                csv_export = df_export.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                
                with col_down1:
                    st.download_button(
                        label="📥 Baixar Alertas em Excel (CSV)",
                        data=csv_export,
                        file_name="alertas_conferencia.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_down2:
                    pdf_data = gerar_pdf(todos_alertas, info_pregao, info_emissao)
                    st.download_button(
                        label="📄 Baixar Relatório de Alertas em PDF",
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
            
            # Se estiver TUDO CERTO
            else:
                st.success("✅ Tudo certo! Nenhum alerta de valor ou desconto encontrado neste arquivo.")
                st.balloons()
                
                # Novo botão de PDF para quando está tudo OK
                pdf_ok_data = gerar_pdf([], info_pregao, info_emissao)
                st.download_button(
                    label="📄 Baixar Relatório de Aprovação (PDF)",
                    data=pdf_ok_data,
                    file_name="relatorio_aprovado.pdf",
                    mime="application/pdf",
                    type="primary"
                )

        with aba_geral:
            st.subheader("Análise de Todos os Itens do Arquivo")
            st.write(f"Total de itens processados: **{len(conferencia_geral)}**")
            
            df_geral = pd.DataFrame(conferencia_geral)
            st.dataframe(df_geral, use_container_width=True)
            
            # Botão extra para baixar a tabela completa em CSV
            csv_geral_export = df_geral.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Tabela Completa (Excel/CSV)",
                data=csv_geral_export,
                file_name="conferencia_completa.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao tentar processar o arquivo: {e}")

import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(page_title="Conferente de Lances", page_icon="📊", layout="wide")

st.title("📊 Conferente de Lances de Pregão")
st.write("Faça o upload do relatório em Excel (.xls ou .xlsx) para identificar automaticamente lances com descontos acima de 40% ou que ultrapassaram o valor unitário estimado.")

# Widget para upload do arquivo (AGORA PARA EXCEL)
uploaded_file = st.file_uploader("Selecione o arquivo Excel do relatório", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Lê o Excel pulando as 6 primeiras linhas de cabeçalho
        df = pd.read_excel(uploaded_file, skiprows=6)
        df.columns = df.columns.str.strip()
        
        # Listas para armazenar as inconsistências encontradas
        lances_acima = []
        descontos_excessivos = []
        
        # Nome exato da coluna de descrição baseado no seu arquivo
        coluna_desc = '--------------------------------- D i s c r i m i n a ç ã o ---------------------------------'
        
        for index, row in df.iterrows():
            try:
                # Extraindo valores
                vlr_unit = float(row['Vlr. Unit.'])
                lance = float(row['Lance'])
                item = row['Item']
                
                # Tratando a descrição para não quebrar a tabela (pegando os primeiros 80 caracteres)
                if coluna_desc in row:
                    descricao = str(row[coluna_desc])[:80].replace('\n', ' ') + "..."
                else:
                    descricao = "Descrição indisponível"
                
                # Regra 1: Lance MAIOR que o Vlr. Unit.
                if lance > vlr_unit:
                    lances_acima.append({
                        "Item": item,
                        "Descrição": descricao,
                        "Vlr. Unit. (R$)": f"{vlr_unit:.4f}",
                        "Lance (R$)": f"{lance:.4f}",
                        "Diferença (R$)": f"{(lance - vlr_unit):.4f} a mais"
                    })
                    continue # Vai para o próximo item
                    
                # Regra 2: Desconto de MAIS DE 40%
                limite_minimo = vlr_unit * 0.60
                
                if lance < limite_minimo:
                    desconto_perc = ((vlr_unit - lance) / vlr_unit) * 100
                    descontos_excessivos.append({
                        "Item": item,
                        "Descrição": descricao,
                        "Vlr. Unit. (R$)": f"{vlr_unit:.4f}",
                        "Lance (R$)": f"{lance:.4f}",
                        "Mínimo Permitido (R$)": f"{limite_minimo:.4f}",
                        "Desconto Aplicado": f"{desconto_perc:.1f}%"
                    })
                    
            except (ValueError, TypeError):
                # Ignora linhas de rodapé ou vazias que não contêm números
                continue
            except KeyError as e:
                st.error(f"Erro de formatação: A coluna {e} não foi encontrada no arquivo. Verifique se o arquivo segue o padrão de colunas.")
                st.stop()
                
        # --- EXIBIÇÃO DOS RESULTADOS NA TELA ---
        st.divider()
        st.subheader("Resultados da Conferência")
        
        # Cria duas colunas para os indicadores numéricos
        col1, col2 = st.columns(2)
        col1.metric("Lances ACIMA do Vlr. Unitário", len(lances_acima))
        col2.metric("Lances com Desconto > 40%", len(descontos_excessivos))
        
        # Exibe a tabela de Lances Acima do Valor
        if lances_acima:
            st.error("🚨 Itens com Lance MAIOR que o Valor Unitário estimado:")
            st.dataframe(pd.DataFrame(lances_acima), use_container_width=True)
            
        # Exibe a tabela de Descontos Excessivos
        if descontos_excessivos:
            st.warning("⚠️ Itens com Desconto EXCESSIVO (Maior que 40%):")
            st.dataframe(pd.DataFrame(descontos_excessivos), use_container_width=True)
            
        # Mensagem de sucesso caso o arquivo passe ileso
        if not lances_acima and not descontos_excessivos:
            st.success("✅ Tudo certo! Nenhum alerta de valor ou desconto encontrado neste arquivo.")
            st.balloons()
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao tentar processar o arquivo: {e}")
        st.info("Verifique se você enviou o arquivo correto (.xls ou .xlsx) e se ele segue o modelo de cabeçalho.")

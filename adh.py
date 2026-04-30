import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- FUNÇÕES DE APOIO ---
def calcular_tempo(inicio):
    """Calcula a diferença entre agora e o início do status"""
    if not inicio: return "00:00"
    diff = datetime.now() - inicio
    minutos, segundos = divmod(diff.seconds, 60)
    return f"{minutos:02d}:{segundos:02d}"

# --- VISÃO DO AGENTE ---
def tela_agente():
    st.title(f"Painel do Expert: {st.session_state.usuario_nome}")
    
    # Simulação de dados vindo do banco
    status_atual = st.session_state.get('status', 'Disponível')
    inicio_status = st.session_state.get('inicio_status', datetime.now())

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status Atual", status_atual)
    with col2:
        # Cronômetro de tempo no status atual
        tempo_decorrido = calcular_tempo(inicio_status)
        st.metric("Tempo no Status", tempo_decorrido)
    with col3:
        st.metric("Sua Próxima Pausa", "21:30")

    # Botões de Ação
    c1, c2 = st.columns(2)
    if status_atual != "Em Pausa":
        if c1.button("☕ INICIAR PAUSA", use_container_width=True):
            st.session_state.status = "Em Pausa"
            st.session_state.inicio_status = datetime.now()
            # AQUI: Comando para salvar na planilha: status='Em Pausa'
            st.rerun()
    else:
        if c1.button("🟢 VOLTAR PARA ATENDIMENTO", use_container_width=True):
            st.session_state.status = "Em Atendimento"
            st.session_state.inicio_status = datetime.now()
            st.rerun()

    st.divider()
    exibir_esteira_geral()

# --- A ESTEIRA (VISÃO PARA TODOS) ---
def exibir_esteira_geral():
    st.subheader("📋 Esteira de Operação em Tempo Real")
    
    # Simulação de dados de todos os agentes (Isso virá do seu Sheets)
    dados_esteira = [
        {"Agente": "Francielle", "Status": "Em Atendimento", "Início": datetime.now() - timedelta(minutes=45), "Pausa": "21:00"},
        {"Agente": "Lucas Ryann", "Status": "Em Pausa", "Início": datetime.now() - timedelta(minutes=5), "Pausa": "21:00"},
        {"Agente": "Gabriele", "Status": "Disponível", "Início": datetime.now() - timedelta(minutes=2), "Pausa": "21:10"},
    ]
    
    df_esteira = pd.DataFrame(dados_esteira)
    df_esteira['Tempo no Status'] = df_esteira['Início'].apply(calcular_tempo)

    # Estilização da Tabela
    def color_status(val):
        color = '#00d1b2' if val == 'Em Atendimento' else '#ff4b4b' if val == 'Em Pausa' else '#fdfd96'
        return f'color: {color}; font-weight: bold'

    st.table(df_esteira[['Agente', 'Status', 'Tempo no Status', 'Pausa']].style.applymap(color_status, subset=['Status']))

# --- ATUALIZAÇÃO AUTOMÁTICA ---
# Isso faz o site atualizar sozinho a cada 30 segundos para mostrar o tempo correndo
if st.session_state.autenticado:
    time.sleep(30)
    st.rerun()

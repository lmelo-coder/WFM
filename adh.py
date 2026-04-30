import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Configurações da Página
st.set_page_config(page_title="WFM ConvertaX", page_icon="⏳", layout="wide")

# Estilização Profissional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .cronometro { font-size: 80px; font-weight: bold; text-align: center; color: #00d1b2; font-family: 'Courier New', monospace; }
    .incidente-box { background-color: #3e1212; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; }
    .expert-card { background-color: #1e1e1e; padding: 20px; border-radius: 15px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# Título
st.title("🚀 Portal WFM ConvertaX")

# Sidebar para Login e Status
with st.sidebar:
    st.header("👤 Área do Expert")
    expert = st.selectbox("Selecione seu nome:", ["Francielle", "Lucas Ryann", "Gabriele", "Ana Antuane"])
    st.success(f"Logado como: {expert}")
    st.divider()
    st.info("💡 Lembre-se de limpar o cache se o sistema apresentar lentidão.")

# Layout principal
col_esq, col_dir = st.columns([2, 1])

with col_esq:
    st.markdown("<div class='expert-card'>", unsafe_allow_html=True)
    st.write(f"### Bem-vinda, {expert}! 👋")
    
    # Horário planejado (exemplo fixo enquanto não conectamos a planilha)
    hora_pausa = "21:30"
    st.write(f"📅 Sua próxima pausa está agendada para: **{hora_pausa}**")
    
    # Simulação de Cronômetro
    st.markdown("<div class='cronometro'>00:03:00</div>", unsafe_allow_html=True)
    
    if st.button("▶️ REGISTRAR INÍCIO DE PAUSA"):
        st.balloons()
        st.success("Pausa registrada! Aderência salva no banco de dados.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_dir:
    # SEÇÃO DE INCIDENTES (O que você acabou de formatar)
    st.subheader("🚨 Incidentes Ativos")
    st.markdown(f"""
    <div class='incidente-box'>
        <b>Lentidão Backoffice (CASSINO/VERA)</b><br>
        <small>Identificado: 29/04/2026 às 23:41</small><br><br>
        <i>Status: Impacto direto nas análises operacionais. Time técnico já notificado.</i>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📅 Grupo de Pausa")
    # Tabela simples simulando sua planilha de grupos
    st.table(pd.DataFrame({
        "Expert": ["Francielle", "Lucas Ryann", "Esteffanny"],
        "Pausa": ["19:00", "19:00", "19:10"]
    }))

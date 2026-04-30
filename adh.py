import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# URLs das Planilhas
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- INICIALIZAÇÃO DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False,
        'perfil': None,
        'usuario_nome': "",
        'status': "Disponível",
        'inicio_status': datetime.now()
    })

# --- FUNÇÕES DE APOIO ---
def carregar_dados(url):
    try:
        df = pd.read_csv(url + f"&cache={time.time()}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

def formatar_tempo(inicio):
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def calcular_atraso_aderencia(horario_planejado):
    """Calcula se o agente já deveria ter iniciado a pausa"""
    try:
        agora = datetime.now()
        hp = datetime.strptime(horario_planejado, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        atraso = (agora - hp).total_seconds() / 60
        if atraso > 0 and st.session_state.status == "Disponível":
            return f"⚠️ {int(atraso)} min atrasado"
        return "✅ OK"
    except: return "---"

# --- TELA DO AGENTE (DESIGN TURBINADO) ---
def tela_agente():
    # 1. Carregar escala individual
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2, inicio_t = "00:00", "00:00", "00:00"
    
    if not df_escala.empty:
        user_data = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_data.empty:
            p1 = user_data.iloc[0]['pausa_1']
            p2 = user_data.iloc[0]['pausa_2']
            inicio_t = user_data.iloc[0]['inicio_turno']

    # --- CABEÇALHO ---
    st.markdown(f"### 🚀 Expert: {st.session_state.usuario_nome} | <span style='color:#00d1b2'>Turno: {inicio_t}</span>", unsafe_allow_html=True)
    
    # --- MÉTRICAS DE ADERÊNCIA ---
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Pausa 1 (Lanche)", p1, delta=calcular_atraso_aderencia(p1), delta_color="inverse")
    with col_m2:
        st.metric("Pausa 2 (Descanso)", p2, delta=calcular_atraso_aderencia(p2), delta_color="inverse")
    with col_m3:
        st.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    # --- CORPO PRINCIPAL ---
    c_status, c_botoes = st.columns([1.5, 1])

    with c_status:
        st.markdown(f"<div style='text-align:center; background-color:#1e1e1e; padding:30px; border-radius:15px; border: 1px solid #333;'>", unsafe_allow_html=True)
        st.write(f"Status Atual: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='font-size:100px; color:#00d1b2; font-family:monospace; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Notificação de 3 minutos via Toast
        agora_str = datetime.now().strftime("%H:%M")
        try:
            alerta_p1 = (datetime.strptime(p1, "%H:%M") - timedelta(minutes=3)).strftime("%H:%M")
            if agora_str == alerta_p1:
                st.toast(f"⏰ {st.session_state.usuario_nome}, faltam 3 min para sua Pausa 1!", icon="⚠️")
        except: pass

    with c_botoes:
        st.write("### Selecione o Status")
        if st.session_state.status == "Disponível":
            if st.button("☕ INICIAR PAUSA ESCALA", use_container_width=True, type="primary"):
                st.session_state.update({'status': "Pausa Programada", 'inicio_status': datetime.now()}); st.rerun()
            
            if st.button("🚻 BANHEIRO / PARTICULAR", use_container_width=True):
                st.session_state.update({'status': "Pausa Particular", 'inicio_status': datetime.now()}); st.rerun()

            if st.button("🏥 MÉDICO / FEEDBACK", use_container_width=True):
                st.session_state.update({'status': "Médico / Feedback", 'inicio_status': datetime.now()}); st.rerun()
        else:
            if st.button("🟢 FINALIZAR E VOLTAR DISPONÍVEL", use_container_width=True, type="primary"):
                st.session_state.update({'status': "Disponível", 'inicio_status': datetime.now()}); st.rerun()

    # --- ESTEIRA DE COLEGAS (CONSCIÊNCIA DE TIME) ---
    st.divider()
    st.subheader("👥 Time no mesmo horário")
    if not df_escala.empty:
        colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
        if not colegas.empty:
            cols = st.columns(len(colegas) if len(colegas) < 5 else 5)
            for idx, row in colegas.iterrows():
                with cols[idx % 5]:
                    st.markdown(f"<div style='padding:10px; border:1px solid #444; border-radius:5px; text-align:center;'><b>{row['nome']}</b><br><small>P1: {row['pausa_1']}</small></div>", unsafe_allow_html=True)
        else:
            st.info("Você é o único expert mapeado para este horário de pausa.")

# --- TELA ADMIN (BÁSICA POR ENQUANTO) ---
def tela_admin():
    st.title("🛡️ Admin WFM - Visão Geral")
    df_escala = carregar_dados(URL_ESCALA)
    st.dataframe(df_escala, use_container_width=True, hide_index=True)

# --- NAVEGAÇÃO ---
# [Aqui continua sua tela de login e lógica de sessão igual ao anterior]

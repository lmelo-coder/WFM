import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #00FF41 !important; }
    .status-box { text-align:center; background:#161b22; padding:20px; border-radius:15px; border:2px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES CORE ---
def get_now():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)

def carregar_dados(url):
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

# --- 3. INICIALIZAÇÃO (BLINDAGEM CONTRA ERROS) ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False, 'usuario_nome': "", 'perfil': None,
        'status': "Offline", 'inicio_status': None, 'aderencia': 100.0,
        'historico_pausas': [], 'alertado': False
    })

URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 4. LÓGICA DE NEGÓCIO (ADERÊNCIA) ---
def processar_aderencia(horario_escala):
    if st.session_state.status in ["Disponível", "Offline"]:
        agora = get_now()
        try:
            planejado = datetime.strptime(horario_escala, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            if agora > planejado:
                atraso_seg = (agora - planejado).total_seconds()
                # Perda de 0.05% por segundo de atraso (ajustável)
                st.session_state.aderencia = max(0.0, 100.0 - (atraso_seg * 0.005))
                if atraso_seg > 0 and not st.session_state.alertado:
                    st.toast(f"🚨 ATRASO NA PAUSA: Sua escala previa saída às {horario_escala}!", icon="⚠️")
                    st.session_state.alertado = True
        except: pass

# --- 5. INTERFACE DO AGENTE ---
def tela_agente():
    agora = get_now()
    df_escala = carregar_dados(URL_ESCALA)
    
    # Busca dados específicos do agente
    minha_escala = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
    p1 = minha_escala.iloc[0]['pausa_1'] if not minha_escala.empty else "00:00"
    p2 = minha_escala.iloc[0]['pausa_2'] if not minha_escala.empty else "00:00"
    
    processar_aderencia(p1)

    # HEADER
    st.title(f"🚀 Painel Expert: {st.session_state.usuario_nome}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sua Pausa 1", p1)
    c2.metric("Sua Pausa 2", p2)
    c3.metric("Aderência Real", f"{round(st.session_state.aderencia, 2)}%")
    
    tempo_str = "00:00:00"
    if st.session_state.inicio_status:
        diff = agora - st.session_state.inicio_status
        tempo_str = str(timedelta(seconds=int(diff.total_seconds())))
    c4.metric("Tempo no Status", tempo_str)

    st.divider()

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown(f"""
            <div class="status-box">
                <p style="color:#8b949e; margin:0;">ESTADO ATUAL: <b>{st.session_state.status.upper()}</b></p>
                <h1 style="font-size:80px; color:#00FF41; margin:10px 0;">{tempo_str}</h1>
            </div>
        """, unsafe_allow_html=True)

        st.write("")
        if st.session_state.status == "Offline":
            if st.button("🏁 FICAR DISPONÍVEL (INICIAR TURNO)", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora})
                st.rerun()
        else:
            b1, b2, b3 = st.columns(3)
            if b1.button("☕ Iniciar Pausa 1"):
                st.session_state.update({'status': "Em Pausa 1", 'inicio_status': agora, 'alertado': False})
                st.rerun()
            if b2.button("🚻 Banheiro"):
                st.session_state.update({'status': "Banheiro", 'inicio_status': agora})
                st.rerun()
            if b3.button("🟢 Retornar"):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora})
                st.rerun()

    with col_side:
        st.subheader("👥 Time na Janela")
        st.caption(f"Colegas com Pausa às {p1}")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
            for _, r in colegas.iterrows():
                st.markdown(f"""
                    <div style="background:#161b22; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #00FF41;">
                        <b>{r['nome']}</b><br><small style="color:#8b949e;">Status: Monitorado pelo WFM</small>
                    </div>
                """, unsafe_allow_html=True)

# --- 6. LOGIN E NAVEGAÇÃO ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_u = carregar_dados(URL_ACESSOS)
    with st.form("login"):
        email = st.text_input("E-mail").strip().lower()
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Turno"):
            user = df_u[df_u['email'] == email]
            if not user.empty and str(user.iloc[0]['senha']) == senha:
                st.session_state.update({
                    'autenticado': True, 'usuario_nome': user.iloc[0]['nome'],
                    'perfil': user.iloc[0]['perfil']
                })
                st.rerun()
            else: st.error("Erro nas credenciais.")

if not st.session_state.autenticado:
    tela_login()
else:
    if st.sidebar.button("Logoff"):
        st.session_state.autenticado = False; st.rerun()
    tela_agente()
    time.sleep(1)
    st.rerun()

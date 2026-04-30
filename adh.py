import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO E ESTILO (NÃO ALTERAR) ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #00FF41 !important; font-family: 'monospace'; }
    .status-box { text-align:center; background:#161b22; padding:20px; border-radius:15px; border:2px solid #00FF41; margin-bottom: 20px; }
    .colega-card { background:#161b22; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURAÇÕES DE DADOS (LINKS) ---
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 3. FUNÇÕES DE LÓGICA PURA ---
def get_now():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)

def carregar_dados(url):
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

def processar_aderencia(horario_escala):
    """Calcula perda de aderência baseada em atraso real"""
    if st.session_state.status in ["Disponível", "Offline"]:
        agora = get_now()
        try:
            planejado = datetime.strptime(horario_escala, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            if agora > planejado:
                atraso_seg = (agora - planejado).total_seconds()
                # Reduz 0.01% por segundo de atraso
                st.session_state.aderencia = max(0.0, 100.0 - (atraso_seg * 0.01))
        except: pass

def formatar_tempo_display(inicio):
    if not inicio: return "00:00:00"
    diff = get_now() - inicio
    return str(timedelta(seconds=int(diff.total_seconds())))

# --- 4. INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False,
        'usuario_nome': "",
        'perfil': None,
        'status': "Offline", # Status inicial crítico
        'inicio_status': None,
        'aderencia': 100.0,
        'historico_pausas': []
    })

# --- 5. INTERFACES (BLOCOS VISUAIS) ---

def tela_login():
    st.markdown("<h1 style='text-align: center; color: #00FF41;'>CONVERTAX WFM</h1>", unsafe_allow_html=True)
    df_u = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        with st.form("login"):
            email = st.text_input("E-mail Expert").strip().lower()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                user = df_u[df_u['email'] == email]
                if not user.empty and str(user.iloc[0]['senha']) == senha:
                    st.session_state.update({
                        'autenticado': True,
                        'usuario_nome': user.iloc[0]['nome'],
                        'perfil': user.iloc[0]['perfil']
                    })
                    st.rerun()
                else: st.error("Acesso negado.")

def tela_agente():
    agora = get_now()
    df_escala = carregar_dados(URL_ESCALA)
    
    # Extração de Escala do Agente
    minha_escala = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
    p1 = minha_escala.iloc[0]['pausa_1'] if not minha_escala.empty else "00:00"
    p2 = minha_escala.iloc[0]['pausa_2'] if not minha_escala.empty else "00:00"
    
    # Executa lógica de aderência em tempo real
    processar_aderencia(p1)

    # CABEÇALHO DE MÉTRICAS
    st.subheader(f"Expert: {st.session_state.usuario_nome}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Escala Pausa 1", p1)
    m2.metric("Escala Pausa 2", p2)
    m3.metric("Aderência Atual", f"{round(st.session_state.aderencia, 1)}%")
    m4.metric("Status Atual", st.session_state.status)

    st.divider()

    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Bloco do Cronômetro
        tempo_str = formatar_tempo_display(st.session_state.inicio_status)
        st.markdown(f"""
            <div class="status-box">
                <p style="color:#8b949e; margin:0; font-size:14px;">TEMPO EM {st.session_state.status.upper()}</p>
                <h1 style="font-size:90px; color:#00FF41; margin:10px 0; font-family: monospace;">{tempo_str}</h1>
            </div>
        """, unsafe_allow_html=True)

        # BLOCO DE BOTÕES (DINÂMICO)
        if st.session_state.status == "Offline":
            st.warning("Você está em modo Offline. Inicie o turno para começar a contagem.")
            if st.button("🏁 FICAR DISPONÍVEL (INICIAR TURNO)", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora})
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            if c1.button("☕ Iniciar Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Em Pausa 1", 'inicio_status': agora})
                st.rerun()
            if c2.button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': agora})
                st.rerun()
            if c3.button("🟢 Retornar / Disponível", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora})
                st.rerun()

    with col_side:
        st.subheader("👥 Time na Janela")
        st.caption(f"Colegas com escala às {p1}")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
            if colegas.empty: st.write("Você é o único nesta janela.")
            for _, r in colegas.iterrows():
                st.markdown(f"<div class='colega-card'><b>{r['nome']}</b><br><small>Escala: {r['pausa_1']}</small></div>", unsafe_allow_html=True)

# --- 6. CONTROLE DE FLUXO ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.clear()
        st.rerun()
    
    tela_agente()
    
    # Refresh de 1 segundo para o cronômetro funcionar
    time.sleep(1)
    st.rerun()

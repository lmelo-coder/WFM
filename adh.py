import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO (DEVE SER A PRIMEIRA LINHA) ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# --- 2. INICIALIZAÇÃO DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False,
        'perfil': None,
        'usuario_nome': "",
        'status': "Offline",
        'inicio_status': None,
        'hora_login': None,
        'historico_pausas': []
    })

# --- 3. FUNÇÕES DE APOIO ---
def get_brasilia_time():
    try:
        return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)
    except:
        return datetime.now() - timedelta(hours=3)

def carregar_dados(url):
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def formatar_tempo(inicio):
    if inicio is None: return "00:00:00"
    diff = get_brasilia_time() - inicio
    ts = int(diff.total_seconds())
    h, r = divmod(ts, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def verificar_aderencia(horario_planejado):
    try:
        agora = get_brasilia_time()
        hp = datetime.strptime(horario_planejado, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        if agora > hp and st.session_state.status in ["Disponível", "Offline"]:
            atraso = int((agora - hp).total_seconds() / 60)
            return f"⚠️ ATRASADO ({atraso} min)"
        return "✅ EM DIA"
    except: return "---"

def registrar_log(tipo_evento):
    hora = get_brasilia_time().strftime("%H:%M:%S")
    st.session_state.historico_pausas.append({"Evento": tipo_evento, "Horário": hora})

# URLs das Planilhas
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 4. TELAS ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>🚀 ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_u = carregar_dados(URL_ACESSOS)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.form("login"):
            email = st.text_input("E-mail").strip().lower()
            senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR", use_container_width=True):
                if not df_u.empty:
                    user = df_u[df_u['email'] == email]
                    if not user.empty and str(user.iloc[0]['senha']) == senha:
                        st.session_state.update({
                            'autenticado': True, 'perfil': user.iloc[0]['perfil'],
                            'usuario_nome': user.iloc[0]['nome'],
                            'hora_login': get_brasilia_time().strftime("%H:%M:%S")
                        })
                        registrar_log("Login")
                        st.rerun()
                st.error("Falha no login.")

def tela_agente():
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🕒 {get_brasilia_time().strftime('%H:%M:%S')}")
    df_e = carregar_dados(URL_ESCALA)
    p1 = df_e[df_e['nome'].str.lower()==st.session_state.usuario_nome.lower()]['pausa_1'].values[0] if not df_e.empty else "00:00"

    m1, m2, m3 = st.columns(3)
    m1.metric("Minha Pausa 1", p1, delta=verificar_aderencia(p1), delta_color="inverse")
    m2.metric("Login Realizado", st.session_state.hora_login)
    m3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("🕹️ Meu Controle")
        cor = "#ff4b4b" if "ATRASADO" in verificar_aderencia(p1) else "#00d1b2"
        st.markdown(f"<div style='text-align:center; background:#1e1e1e; padding:25px; border-radius:15px; border:2px solid {cor};'>", unsafe_allow_html=True)
        st.write(f"STATUS: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='color:{cor}; font-size:75px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        if st.session_state.status == "Offline":
            if st.button("🏁 FICAR DISPONÍVEL", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Turno"); st.rerun()
        elif st.session_state.status == "Disponível":
            c_b = st.columns(3)
            if c_b[0].button("☕ Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Pausa 1", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Pausa 1"); st.rerun()
            if c_b[1].button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Banheiro"); st.rerun()
            if c_b[2].button("🏥 Feedback", use_container_width=True):
                st.session_state.update({'status': "Feedback", 'inicio_status': get_brasilia_time()})
                registrar_log("Início FB"); st.rerun()
        else:
            if st.button("🟢 RETORNAR (VOLTAR DISPONÍVEL)", type="primary", use_container_width=True):
                registrar_log(f"Fim {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                st.rerun()

    with col2:
        st.subheader("👥 Monitor de Colegas")
        if not df_e.empty:
            colegas = df_e[(df_e['pausa_1'] == p1) & (df_e['nome'] != st.session_state.usuario_nome)]
            for _, r in colegas.iterrows():
                st.markdown(f"<div style='background:#262730; padding:10px; border-radius:5px; margin-bottom:5px; border-left:3px solid #555;'><b>{r['nome']}</b><br><small>Pausa às {r['pausa_1']}</small></div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("📝 Histórico"):
        st.table(pd.DataFrame(st.session_state.historico_pausas))

# --- 5. NAVEGAÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.sidebar.button("Log

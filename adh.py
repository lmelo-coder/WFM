import streamlit as st
import pandas as pd
from datetime import datetime
import time
import pytz

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# URLs das Planilhas
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 2. FUNÇÕES DE SUPORTE ---

def get_brasilia_time():
    """Retorna o horário atual de Brasília"""
    try:
        return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)
    except:
        # Fallback caso pytz falhe (ajuste manual de -3h sobre o UTC comum em servers)
        return datetime.utcnow() - timedelta(hours=3)

def carregar_dados(url):
    """Lê dados da planilha com cache buster para evitar dados obsoletos"""
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def formatar_tempo(inicio):
    """Calcula a duração entre 'inicio' e agora"""
    if inicio is None: return "00:00:00"
    diff = get_brasilia_time() - inicio
    total_segundos = int(diff.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def verificar_aderencia(horario_planejado):
    """Calcula atraso em relação à escala"""
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
    """Salva evento no histórico da sessão"""
    hora_atual = get_brasilia_time().strftime("%H:%M:%S")
    st.session_state.historico_pausas.append({
        "Evento": tipo_evento,
        "Horário": hora_atual
    })

# --- 3. INICIALIZAÇÃO DO ESTADO ---
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

# --- 4. TELAS DO SISTEMA ---

def tela_login():
    st.markdown("<h1 style='text-align: center;'>🚀 ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail Corporativo").strip().lower()
            senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR PORTAL", use_container_width=True):
                if not df_users.empty:
                    user_match = df_users[df_users['email'].str.lower() == email]
                    if not user_match.empty and str(user_match.iloc[0]['senha']) == senha:
                        st.session_state.update({
                            'autenticado': True,
                            'perfil': user_match.iloc[0]['perfil'],
                            'usuario_nome': user_match.iloc[0]['nome'],
                            'hora_login': get_brasilia_time().strftime("%H:%M:%S")
                        })
                        registrar_log("Acesso ao Portal")
                        st.rerun()
                st.error("Credenciais inválidas ou erro de conexão.")

def tela_agente():
    agora_br = get_brasilia_time()
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🕒 {agora_br.strftime('%H:%M:%S')}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    # Indicadores de Aderência
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Sua Pausa 1", p1, delta=verificar_aderencia(p1), delta_color="inverse")
    with m2: st.metric("Sua Pausa 2", p2, delta=verificar_aderencia(p2), delta_color="inverse")
    with m3: st.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    col_ctrl, col_team = st.columns([1.3, 1])

    with col_ctrl:
        st.subheader("🕹️ Meu Status")
        # Estilo dinâmico baseado em aderência
        inaderente = "ATRASADO" in verificar_aderencia(p1) or "ATRASADO" in verificar_aderencia(p2)
        cor_foco = "#ff4b4b" if inaderente else "#00d1b2"
        
        st.markdown(f"""
            <div style='text-align:center; background-color:#1e1e1e; padding:25px; border-radius:15px; border:2px solid {cor_foco};'>
                <p style='margin:0; color:#aaa; font-size:14px;'>VOCÊ ESTÁ ATUALMENTE EM:</p>
                <h2 style='margin:0; color:white; letter-spacing: 2px;'>{st.session_state.status.upper()}</h2>
                <h1 style='color:{cor_foco}; font-family:monospace; font-size:75px; margin:10px 0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.status == "Offline":
            if st.button("🏁 FICAR DISPONÍVEL (INICIAR TURNO)", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                registrar_log("Início de Turno"); st.rerun()
        
        elif st.session_state.status == "Disponível":
            btn_cols = st.columns(3)
            if btn_cols[0].button("☕ Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Pausa 1", 'inicio_status': get_brasilia_time()})
                registrar_log("Iniciou Pausa 1"); st.rerun()
            if btn_cols[1].button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': get_brasilia_time()})
                registrar_log("Iniciou Banheiro"); st.rerun()
            if btn_cols[2].button("🏥 Outros/FB", use_container_width=True):
                st.session_state.update({'status': "Feedback/Médico", 'inicio_status': get_brasilia_time()})
                registrar_log("Iniciou Feedback/Médico"); st.rerun()

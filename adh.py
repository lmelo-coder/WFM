import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO INICIAL (Obrigatório ser a primeira linha) ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# --- 2. FUNÇÕES DE SUPORTE (Definidas no topo para evitar NameError) ---

def get_brasilia_time():
    """Retorna o horário atual de Brasília ajustado"""
    try:
        return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)
    except:
        # Fallback caso a biblioteca pytz não esteja instalada
        return datetime.now() - timedelta(hours=3)

def formatar_tempo(inicio):
    """Calcula a duração do status atual"""
    if inicio is None: return "00:00:00"
    diff = get_brasilia_time() - inicio
    total_segundos = int(diff.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def carregar_dados(url):
    """Carrega dados das planilhas Google"""
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def verificar_aderencia(horario_planejado):
    """Verifica se o agente está atrasado para a pausa conforme escala"""
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
    """Registra ações no histórico da sessão"""
    hora_atual = get_brasilia_time().strftime("%H:%M:%S")
    if 'historico_pausas' in st.session_state:
        st.session_state.historico_pausas.append({
            "Evento": tipo_evento,
            "Horário": hora_atual
        })

# --- 3. INICIALIZAÇÃO DO ESTADO (Evita AttributeError) ---
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

# URLs
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 4. INTERFACES ---

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
                    user_match = df_users[df_users['email'] == email]
                    if not user_match.empty and str(user_match.iloc[0]['senha']) == senha:
                        st.session_state.update({
                            'autenticado': True,
                            'perfil': user_match.iloc[0]['perfil'],
                            'usuario_nome': user_match.iloc[0]['nome'],
                            'hora_login': get_brasilia_time().strftime("%H:%M:%S")
                        })
                        registrar_log("Acesso ao Portal")
                        st.rerun()
                st.error("Dados inválidos.")

def tela_agente():
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🕒 {get_brasilia_time().strftime('%H:%M:%S')}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1 = "00:00"
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        p1 = user_row.iloc[0]['pausa_1'] if not user_row.empty else "00:00"

    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Minha Pausa 1", p1, delta=verificar_aderencia(p1), delta_color="inverse")
    m2.metric("Login Realizado", st.session_state.hora_login)
    m3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    col_ctrl, col_team = st.columns([1.3, 1])

    with col_ctrl:
        st.subheader("🕹️ Meu Controle")
        cor = "#ff4b4b" if "ATRASADO" in verificar_aderencia(p1) else "#00d1b2"
        st.markdown(f"""
            <div style='text-align:center; background-color:#1e1e1e; padding:25px; border-radius:15px; border:2px solid {cor};'>
                <p style='margin:0; color:#aaa;'>STATUS ATUAL</p>
                <h2 style='margin:0; color:white;'>{st.session_state.status.upper()}</h2>
                <h1 style='color:{cor}; font-family:monospace; font-size:75px; margin:10px 0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.status == "Offline":
            if st.button("🏁 FICAR DISPONÍVEL (INICIAR TURNO)", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                registrar_log("Início de Turno"); st.rerun()
        elif st.session_state.status == "Disponível":
            c = st.columns(3)
            if c[0].button("☕ Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Pausa 1", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Pausa 1"); st.rerun()
            if c[1].button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Banheiro"); st.rerun()
            if c[2].button("🏥 Outros/FB", use_container_width=True):
                st.session_state.update({'status': "Feedback", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Feedback"); st.rerun()
        else:
            if st.button("🟢 RETORNEI PARA DISPONÍVEL", type="primary", use_container_width=True):
                registrar_log(f"Retorno de {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                st.rerun()

    with col_team:
        st.subheader("👥 Autonomia do Time")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'] != st.session_state.usuario_nome)]
            for _, r in colegas.iterrows():
                st.markdown(f"<div style='background:#262730; padding:10px; border-radius:5px; margin-bottom:5px; border-left:3px solid #555;'><b>{r['nome']}</b><br><small>Pausa: {r['pausa_1']}</small></div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("📝 Histórico"):
        st.table(pd.DataFrame(st.session_state.historico_pausas))

# --- 5. NAVEGAÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.sidebar.button("Logoff"):
        st.session_state.autenticado = False
        st.rerun()
    
    if st.session_state.perfil == "Admin":
        st.title("Admin")
        st.dataframe(carregar_dados(URL_ESCALA))
    else:
        tela_agente()
    
    # Refresh para o cronômetro
    time.sleep(1)
    st.rerun()

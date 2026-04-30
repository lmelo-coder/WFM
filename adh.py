import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO DE UI E IDENTIDADE VISUAL ---
st.set_page_config(page_title="WFM ConvertaX | Expert Panel", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00FF41 !important; font-family: 'monospace'; font-size: 1.8rem; }
    .status-box { 
        text-align:center; background:#161b22; padding:30px; 
        border-radius:20px; border: 2px solid #00FF41; box-shadow: 0 0 15px rgba(0,255,65,0.2);
    }
    .stButton>button { 
        border: 1px solid #00FF41; color: #00FF41; background: transparent; 
        font-weight: bold; height: 3em; transition: 0.3s;
    }
    .stButton>button:hover { background: #00FF41; color: black; }
    .colega-card { 
        background: #1c2128; border-left: 5px solid #00FF41; 
        padding: 12px; margin-bottom: 10px; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURAÇÕES DE DADOS ---
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 3. MOTOR DE LÓGICA (TEMPO E ADERÊNCIA) ---
def get_now():
    """Retorna horário de Brasília (UTC-3)"""
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)

def formatar_tempo_display(inicio):
    """Calcula duração exata sem bugs de contagem"""
    if not inicio: return "00:00:00"
    diff = get_now() - inicio
    return str(timedelta(seconds=int(diff.total_seconds())))

def processar_aderencia(horario_escala):
    """Cálculo punitivo de aderência em tempo real"""
    if st.session_state.status in ["Disponível", "Offline"]:
        agora = get_now()
        try:
            planejado = datetime.strptime(horario_escala, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            if agora > planejado:
                atraso_seg = (agora - planejado).total_seconds()
                # Penalidade de 0.01% por segundo de atraso
                st.session_state.aderencia = max(0.0, 100.0 - (atraso_seg * 0.01))
                if not st.session_state.alertado:
                    st.toast(f"🚨 HORA DA PAUSA PASSOU! ({horario_escala})", icon="⚠️")
                    st.session_state.alertado = True
        except: pass

def carregar_dados(url):
    """Leitura de dados com bypass de cache"""
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

# --- 4. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False, 'usuario_nome': "", 'perfil': None,
        'status': "Offline", 'inicio_status': None, 'aderencia': 100.0,
        'historico_logs': [], 'alertado': False
    })

# --- 5. COMPONENTES DE INTERFACE ---

def tela_login():
    st.markdown("<h1 style='text-align:center; color:#00FF41;'>CONVERTAX WFM</h1>", unsafe_allow_html=True)
    df_u = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail Expert").strip().lower()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                user = df_u[df_u['email'] == email]
                if not user.empty and str(user.iloc[0]['senha']) == senha:
                    st.session_state.update({
                        'autenticado': True, 'usuario_nome': user.iloc[0]['nome'],
                        'perfil': user.iloc[0]['perfil']
                    })
                    st.rerun()
                else: st.error("Credenciais inválidas.")

def tela_agente():
    agora = get_now()
    df_escala = carregar_dados(URL_ESCALA)
    
    # Dados da Escala do Agente
    minha_escala = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
    p1 = minha_escala.iloc[0]['pausa_1'] if not minha_escala.empty else "00:00"
    p2 = minha_escala.iloc[0]['pausa_2'] if not minha_escala.empty else "00:00"
    
    processar_aderencia(p1)

    # Dashboard de Métricas Superior
    st.markdown(f"### Bem-vindo, {st.session_state.usuario_nome} | 🕒 {agora.strftime('%H:%M:%S')}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Escala Pausa 1", p1)
    m2.metric("Escala Pausa 2", p2)
    m3.metric("Aderência Real", f"{round(st.session_state.aderencia, 1)}%")
    m4.metric("Status", st.session_state.status)

    st.divider()

    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Bloco Central de Status e Tempo
        tempo_str = formatar_tempo_display(st.session_state.inicio_status)
        st.markdown(f"""
            <div class="status-box">
                <p style="color:#8b949e; margin:0; font-size:14px; letter-spacing:2px;">TEMPO ATUAL EM {st.session_state.status.upper()}</p>
                <h1 style="font-size:100px; color:#00FF41; margin:10px 0; font-family: 'Courier New';">{tempo_str}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Controles de Status
        st.write("")
        if st.session_state.status == "Offline":
            if st.button("🏁 INICIAR TURNO", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora, 'alertado': False})
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            if c1.button("☕ Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Em Pausa 1", 'inicio_status': agora})
                st.rerun()
            if c2.button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': agora})
                st.rerun()
            if c3.button("🟢 Retornar", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': agora, 'alertado': False})
                st.rerun()

    with col_side:
        st.subheader("👥 Autonomia do Time")
        st.caption(f"Colegas na mesma janela de pausa ({p1})")
        if not df_escala.empty:
            # Filtro real por horário de escala
            time_janela = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
            if time_janela.empty:
                st.info("Ninguém escalado com você agora.")
            else:
                for _, r in time_janela.iterrows():
                    st.markdown(f"""
                        <div class="colega-card">
                            <b>{r['nome']}</b><br>
                            <small style="color:#8b949e;">Escala: {r['pausa_1']}</small>
                        </div>
                    """, unsafe_allow_html=True)

# --- 6. GESTÃO DE EXECUÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    with st.sidebar:
        st.image("https://www.convertax.com.br/wp-content/uploads/2022/07/logo-convertax.png", width=150)
        st.write(f"**Usuário:** {st.session_state.usuario_nome}")
        if st.button("Sair do Sistema"):
            st.session_state.clear()
            st.rerun()
    
    tela_agente()
    
    # O "Coração" do Cronômetro: Refresh a cada 1 segundo
    time.sleep(1)
    st.rerun()

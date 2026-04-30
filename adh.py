import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

# --- 1. CONFIGURAÇÃO VISUAL (CONVERTAX STYLE) ---
st.set_page_config(page_title="WFM ConvertaX | Expert Panel", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { color: #00FF41; font-family: 'Courier New', monospace; }
    .stButton>button { 
        background-color: #1a1a1a; color: #00FF41; border: 1px solid #00FF41;
        border-radius: 5px; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #00FF41; color: black; border: 1px solid #00FF41; }
    .status-card {
        background: #161b22; border: 1px solid #30363d; padding: 20px;
        border-radius: 10px; text-align: center; margin-bottom: 10px;
    }
    .aderencia-high { color: #00FF41; font-weight: bold; }
    .aderencia-low { color: #FF4B4B; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA DE TEMPO E BRASÍLIA ---
def get_now():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)

# --- 3. INICIALIZAÇÃO DE ESTADO (BLINDAGEM DE ERROS) ---
if 'init' not in st.session_state:
    st.session_state.update({
        'init': True,
        'autenticado': False,
        'status': "Offline",
        'inicio_status': None,
        'aderencia': 100.0,
        'total_atraso_segundos': 0,
        'historico': [],
        'alertado': False
    })

# --- 4. CÁLCULO DE ADERÊNCIA EM TEMPO REAL ---
def calcular_aderencia(pausa_planejada):
    if st.session_state.status == "Offline": return 100.0
    
    agora = get_now()
    try:
        # Converte string "19:00" para objeto datetime hoje
        planejado = datetime.strptime(pausa_planejada, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        
        if agora > planejado and st.session_state.status == "Disponível":
            atraso = (agora - planejado).total_seconds()
            # Penalidade: 0.1% a cada 10 segundos de atraso (exemplo)
            penalidade = (atraso / 10) * 0.1
            st.session_state.aderencia = max(0.0, 100.0 - penalidade)
            
            # Alerta visual (Windows Toast simulação)
            if atraso > 0 and not st.session_state.alertado:
                st.toast(f"🚨 HORA DA PAUSA! Você está {int(atraso/60)}min atrasado!", icon="⏰")
                st.session_state.alertado = True
    except:
        pass
    return round(st.session_state.aderencia, 2)

# --- 5. COMPONENTES DE INTERFACE ---
def tela_agente():
    # Header Corporativo
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.title("🚀 Painel do Expert")
    c2.metric("Sua Aderência", f"{st.session_state.aderencia}%")
    c3.write(f"**Expert:** {st.session_state.usuario_nome}\n\n**Status:** {st.session_state.status}")

    st.divider()

    # Layout Principal
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Central de Status
        st.markdown(f"""
            <div class="status-card">
                <p style="color: #8b949e; margin-bottom: 0;">TEMPO EM {st.session_state.status.upper()}</p>
                <h1 style="font-size: 80px; margin: 0; color: #00FF41;">
                    {formatar_tempo_display(st.session_state.inicio_status)}
                </h1>
            </div>
        """, unsafe_allow_html=True)

        # Botões de Ação
        if st.session_state.status == "Offline":
            if st.button("🏁 INICIAR TURNO (FICAR DISPONÍVEL)"):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_now()})
                st.rerun()
        else:
            cols = st.columns(3)
            if cols[0].button("☕ Pausa Lanche"):
                mudar_status("Pausa 1")
            if cols[1].button("🚻 Banheiro"):
                mudar_status("Pausa 2")
            if cols[2].button("🟢 Retornar"):
                mudar_status("Disponível")

    with col_side:
        st.subheader("👥 Próximos de Você")
        # Simulação de Time (Autonomia)
        monitor_time_mock()

    # Tabela de Aderência do Dia
    st.subheader("📊 Jornada de Aderência")
    st.caption("O cálculo considera o horário de saída e retorno exatos da escala.")
    # Gráfico simples ou métrica de progresso
    st.progress(st.session_state.aderencia / 100)

def mudar_status(novo_status):
    st.session_state.update({'status': novo_status, 'inicio_status': get_now(), 'alertado': False})
    st.rerun()

def formatar_tempo_display(inicio):
    if not inicio: return "00:00:00"
    diff = get_now() - inicio
    return str(timedelta(seconds=int(diff.total_seconds())))

def monitor_time_mock():
    # Simula colegas próximos
    colegas = [
        {"nome": "Ana Silva", "status": "Em Pausa", "tempo": "00:12:05", "cor": "#FFB800"},
        {"nome": "Bruno Costa", "status": "Disponível", "tempo": "02:45:10", "cor": "#00FF41"},
        {"nome": "Carla Dias", "status": "Feedback", "tempo": "00:05:22", "cor": "#00A3FF"}
    ]
    for c in colegas:
        st.markdown(f"""
            <div style="background: #161b22; border-left: 4px solid {c['cor']}; padding: 10px; margin-bottom: 5px;">
                <small style="color: #8b949e;">{c['status']}</small><br>
                <b>{c['nome']}</b> • <span style="font-family: monospace;">{c['tempo']}</span>
            </div>
        """, unsafe_allow_html=True)

# --- 6. EXECUÇÃO ---
# (Simulação de Login para o exemplo)
st.session_state.usuario_nome = "Expert Agente"
st.session_state.autenticado = True

if st.session_state.autenticado:
    # Simula busca de escala na planilha
    pausa_exemplo = "19:00" # Isso viria do seu URL_ESCALA
    calcular_aderencia(pausa_exemplo)
    tela_agente()
    
    # Auto-refresh de 1s para o cronômetro e aderência
    time.sleep(1)
    st.rerun()

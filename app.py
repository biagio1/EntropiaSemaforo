# ==============================================================================
# >>>>>> BLOCK >>> A <<< (SETTINGS, TRAFFIC LIGHT UI & AUDIO)
# ==============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import re
import time
import threading
from datetime import datetime, timedelta

try:
    import winsound
except ImportError:
    winsound = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_DATABASE_CSV = os.path.join(BASE_DIR, "storico_semaforo_pulito.csv")

st.set_page_config(
    page_title="Entropia Universe - Dual Loot Predictor",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@keyframes blink-green {
    0% { box-shadow: 0 0 5px #00ff00; opacity: 1; }
    50% { box-shadow: 0 0 25px #00ff00; opacity: 0.4; }
    100% { box-shadow: 0 0 5px #00ff00; opacity: 1; }
}
@keyframes blink-yellow {
    0% { box-shadow: 0 0 5px #ffcc00; opacity: 1; }
    50% { box-shadow: 0 0 25px #ffcc00; opacity: 0.4; }
    100% { box-shadow: 0 0 5px #ffcc00; opacity: 1; }
}
@keyframes blink-red {
    0% { box-shadow: 0 0 5px #ff3333; opacity: 1; }
    50% { box-shadow: 0 0 30px #ff3333; opacity: 0.3; }
    100% { box-shadow: 0 0 5px #ff3333; opacity: 1; }
}
.semaforo-box {
    display: flex;
    align-items: center;
    padding: 16px;
    border-radius: 12px;
    background-color: #1e1e26;
    border: 1px solid #333;
    margin-bottom: 12px;
    min-height: 95px;
}
.luce {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    margin-right: 16px;
    flex-shrink: 0;
}
.luce-verde { background-color: #00e676; animation: blink-green 1.5s infinite; }
.luce-gialla { background-color: #ffea00; animation: blink-yellow 1.8s infinite; }
.luce-rossa { background-color: #ff1744; animation: blink-red 1.0s infinite; }
.testo-semaforo h2 { margin: 0; font-size: 18px; color: white; }
.testo-semaforo p { margin: 4px 0 0 0; font-size: 14px; color: #cccccc; }
</style>
""", unsafe_allow_html=True)

def _play_sound_thread(tipo):
    try:
        if winsound:
            if tipo == "VERDE":
                winsound.Beep(1000, 150)
                winsound.Beep(1800, 300)
            elif tipo == "GIALLO":
                winsound.Beep(1200, 150)
                time.sleep(0.08)
                winsound.Beep(1200, 150)
            elif tipo == "ROSSO":
                winsound.Beep(800, 200)
                winsound.Beep(600, 200)
                winsound.Beep(400, 400)
        else:
            print("\a", end="", flush=True)
    except Exception:
        pass

def attiva_allarme_sonoro(tipo):
    t = threading.Thread(target=_play_sound_thread, args=(tipo,), daemon=True)
    t.start()

# ==============================================================================
# >>>>>> BLOCK >>> B <<< (SIDEBAR & CREATURES BY PLANET)
# ==============================================================================

st.sidebar.title("🎯 Hunting Control")

MOBS_PER_PIANETA = {
    "Planet Calypso": [
        "Allophyl", "Ambulimax", "Argonaut", "Armax", "Atrax", "Atrox",
        "Berycled", "Caudatergus", "Combibo", "Cornundacauda", "Cornundos",
        "Daikiba", "Dire Weed", "Drone", "Estophyl", "Exarosaur", "Faucervix",
        "Feffoid", "Foul", "Fugabarba", "Gokibusagi", "Gradivore", "Hiryuu",
        "Itumatrox", "Kerberos", "Kreltin", "Longu", "Mang Chang", "Merp",
        "Molisk", "Mourner", "Oculus", "Plumatergus", "Repesilex", "Rextelum",
        "Rhino Beetle", "Rippersnapper", "Sabakuma", "Sea Wraith", "Snablesnot",
        "Snarksnot", "Starving Atrax", "Tantardion", "Tantillion", "Tripudion",
        "Vrex", "Zombie"
    ],
    "Planet Arkadia": [
        "Beladoth", "Bokol", "Carabok", "Feran", "Gallard", "Halix",
        "Hornet", "Huon", "Jori", "Kadra", "Kamaldon", "Nusul",
        "Oratan Prospector", "Oro", "Tiarak", "Ubo", "Yuka", "Zadul"
    ],
    "Planet Cyrene": [
        "Drill Bot", "Empis", "Imperium", "Paneleon", "Pleader",
        "Scout Bot", "Tide Claw", "Tree Dragon", "Zeladoth"
    ],
    "Monria": [
        "Crystal Pede"
    ]
}

pianeta_scelto = st.sidebar.selectbox(
    "🪐 Select Planet:",
    ["All Planets", "Planet Calypso", "Planet Arkadia", "Planet Cyrene", "Monria"]
)

if pianeta_scelto == "All Planets":
    lista_mob_default = sorted([m for mobs in MOBS_PER_PIANETA.values() for m in mobs])
else:
    lista_mob_default = sorted(MOBS_PER_PIANETA[pianeta_scelto])

nuovo_mob = st.sidebar.text_input("Add another mob (e.g. Hogglo):", "")
if nuovo_mob and nuovo_mob.strip().title() not in lista_mob_default:
    lista_mob_default.append(nuovo_mob.strip().title())
    lista_mob_default = sorted(lista_mob_default)

mob_selezionato = st.sidebar.selectbox("Creature to monitor (Lv. 1-20+):", lista_mob_default)

st.sidebar.markdown("---")
st.sidebar.subheader("🔫 Budget & Crafter Rule")
ped_ammo_run = st.sidebar.number_input(
    "Ammo Budget per Run (PED):",
    min_value=5, max_value=500, value=15, step=5
)

if "run_consecutive_vuote" not in st.session_state:
    st.session_state.run_consecutive_vuote = 0
if "run_totali_sessione" not in st.session_state:
    st.session_state.run_totali_sessione = 0
if "ped_spesi_vuoti" not in st.session_state:
    st.session_state.ped_spesi_vuoti = 0

c_run1, c_run2 = st.sidebar.columns(2)
if c_run1.button(f"❌ Empty Run (-{ped_ammo_run})"):
    st.session_state.run_consecutive_vuote += 1
    st.session_state.run_totali_sessione += 1
    st.session_state.ped_spesi_vuoti += ped_ammo_run
if c_run2.button("💰 Global Hit!"):
    st.session_state.run_consecutive_vuote = 0
    st.session_state.run_totali_sessione += 1

c_rst1, c_rst2 = st.sidebar.columns(2)
if c_rst1.button("🔁 Change Area"):
    st.session_state.run_consecutive_vuote = 0
if c_rst2.button("🗑️ Reset All"):
    st.session_state.run_consecutive_vuote = 0
    st.session_state.run_totali_sessione = 0
    st.session_state.ped_spesi_vuoti = 0

if st.session_state.run_consecutive_vuote >= 1:
    st.sidebar.error(f"🚨 STOP AREA! {st.session_state.run_consecutive_vuote} empty run(s) of {ped_ammo_run} PED here. Change spawn or mob!")
else:
    st.sidebar.success(f"✅ Area OK | Runs: {st.session_state.run_totali_sessione} | Dry: -{st.session_state.ped_spesi_vuoti} PED")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Pool Calibration & Filter")
target_manuale_ped = st.sidebar.number_input(
    "Base Daily PED Target:",
    min_value=100, max_value=50000, value=1000, step=100
)
soglia_hof_stop = st.sidebar.number_input(
    "HoF Drain Threshold (PED):",
    min_value=100, max_value=10000, value=250, step=50
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔊 Audio Alert Test")
c_btn1, c_btn2, c_btn3 = st.sidebar.columns(3)
if c_btn1.button("🟢 Green"):
    attiva_allarme_sonoro("VERDE")
if c_btn2.button("🟡 Yellow"):
    attiva_allarme_sonoro("GIALLO")
if c_btn3.button("🔴 Red"):
    attiva_allarme_sonoro("ROSSO")
# ==============================================================================
# >>>>>> BLOCK >>> C <<< (CHAT LOG READER, PLAYER TRACKER & CSV UPDATER)
# ==============================================================================

def trova_chat_log_automatico():
    user_home = os.path.expanduser("~")
    percorsi_possibili = [
        os.path.join(user_home, "Documents", "Entropia Universe", "chat.log"),
        os.path.join(user_home, "OneDrive", "Documents", "Entropia Universe", "chat.log"),
        os.path.join(user_home, "OneDrive", "Documenti", "Entropia Universe", "chat.log"),
        r"D:\OneDrive\Documents\Entropia Universe\chat.log",
        r"D:\Entropia\public_users_data\chat.log",
        r"D:\Entropia\chat.log",
        r"C:\Entropia\chat.log"
    ]
    for p in percorsi_possibili:
        if os.path.exists(p):
            return p
    return os.path.join(user_home, "Documents", "Entropia Universe", "chat.log")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Chat Log File")
percorso_raw = st.sidebar.text_input(
    "Path to chat.log:",
    value=trova_chat_log_automatico()
)
percorso_log_scelto = percorso_raw.strip().strip('"').strip("'")

def aggiorna_database_da_chatlog(percorso_file):
    primo_avvio = not os.path.exists(PATH_DATABASE_CSV) or os.path.getsize(PATH_DATABASE_CSV) == 0
    if not primo_avvio:
        try:
            df_storico = pd.read_csv(PATH_DATABASE_CSV)
            df_storico['Timestamp'] = pd.to_datetime(df_storico['Timestamp'], errors='coerce')
            if 'Player' not in df_storico.columns:
                df_storico['Player'] = "Unknown"
        except Exception:
            df_storico = pd.DataFrame(columns=['Timestamp', 'Player', 'Mob', 'PED'])
    else:
        df_storico = pd.DataFrame(columns=['Timestamp', 'Player', 'Mob', 'PED'])

    log_trovato = bool(percorso_file and os.path.exists(percorso_file))
    nuovi_record = []

    if log_trovato:
        pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(?:Globals|System)\]\s*(?:\[\])?\s*(.*?)\s+(?:killed a creature|ha ucciso una creatura|ucciso una creatura)\s+\((.*?)\)\s+(?:with a value of|con un valore di)\s+(\d+)\s*PED",
            re.IGNORECASE
        )
        try:
            dimensione_file = os.path.getsize(percorso_file)
            with open(percorso_file, "r", encoding="utf-8", errors="ignore") as f:
                if "scansione_iniziale_fatta" not in st.session_state:
                    st.session_state["scansione_iniziale_fatta"] = True
                    limite_lettura = 10000000
                else:
                    limite_lettura = 500000
                if dimensione_file > limite_lettura:
                    f.seek(dimensione_file - limite_lettura)
                    f.readline()
                for linea in f:
                    if ("killed a creature" in linea or "ucciso una creatura" in linea) and "PED" in linea:
                        match = pattern.search(linea)
                        if match:
                            ts_str, player_nome, mob_nome, ped_val = match.groups()
                            ts = pd.to_datetime(ts_str, errors='coerce')
                            if pd.notna(ts):
                                player_pulito = player_nome.replace("&quot;", '"').strip() if player_nome.strip() else "Unknown"
                                nuovi_record.append({
                                    'Timestamp': ts,
                                    'Player': player_pulito,
                                    'Mob': mob_nome.strip().title(),
                                    'PED': int(ped_val)
                                })
        except Exception:
            pass

    if nuovi_record:
        df_nuovi = pd.DataFrame(nuovi_record)
        df_totale = pd.concat([df_storico, df_nuovi], ignore_index=True)
        df_totale = df_totale.dropna(subset=['Timestamp', 'Mob', 'PED'])
        df_totale['Mob'] = df_totale['Mob'].astype(str).str.strip().str.title()
        df_totale['Player'] = df_totale['Player'].fillna("Unknown").astype(str).str.replace("&quot;", '"', regex=False).str.strip()
        df_totale['Ts_Minuto'] = df_totale['Timestamp'].dt.floor('min')
        df_totale['Ha_Player'] = (df_totale['Player'] != "Unknown").astype(int)
        df_totale = df_totale.sort_values(['Timestamp', 'Ha_Player'], ascending=[True, True])
        df_totale = df_totale.drop_duplicates(subset=['Ts_Minuto', 'Mob', 'PED'], keep='last')
        df_totale = df_totale.drop(columns=['Ts_Minuto', 'Ha_Player']).sort_values('Timestamp', ascending=True)
        df_totale.to_csv(PATH_DATABASE_CSV, index=False)
        return df_totale, log_trovato

    return df_storico, log_trovato

df_globale, log_ok = aggiorna_database_da_chatlog(percorso_log_scelto)

if log_ok:
    st.sidebar.success(f"✅ Log connected! ({len(df_globale)} total Globals)")
else:
    st.sidebar.warning(f"⚠️ chat.log not found (using CSV history: {len(df_globale)} Globals).")
# ==============================================================================
# >>>>>> BLOCK >>> D <<< (PLANET MOB DATABASE PART 1: A - K)
# ==============================================================================

INFO_MOB = {
    "Drill Bot": ("Planet Cyrene", "Lv. 4-9 (Small Robot)", "135400, 76800 (A.R.C. Staging / Robot Area)", "Electronic Comps, Motion Sensors, Kinsite Ore (115-135% MU)", "/wp [Cyrene, 135400, 76800, 110, Drill Bot]"),
    "Oratan Prospector": ("Planet Arkadia", "Lv. 8-16 (Young/Mature)", "21500, 19800 (IFN Outposts / Arkadia)", "Oratan Axe, Arkadian Oils, Weapons (115-135% MU)", "/wp [Arkadia, 21500, 19800, 115, Oratan Prospector]"),
    "Scout Bot": ("Planet Cyrene", "Lv. 3-7 (Small Robot)", "136100, 77400 (Cyrene Robot Outpost)", "Basic Targeting Chip, Electronic Comps (115-130% MU)", "/wp [Cyrene, 136100, 77400, 110, Scout Bot]"),
    "Starving Atrax": ("Planet Calypso", "Lv. 8-12 (Low HP Atrax)", "76400, 68500 (Ithaca / Fort Fury)", "Atrax Bone, Animal Muscle Oil (115-130% MU)", "/wp [Calypso, 76400, 68500, 130, Starving Atrax]"),

    "Allophyl": ("Planet Calypso", "Lv. 12-19 (Young/Mature)", "68400, 82100 (Zychion / Fort Fury)", "Allophyl Skin, Muscle Oil, Jaguar Parts (115-135% MU)", "/wp [Calypso, 68400, 82100, 120, Allophyl]"),
    "Ambulimax": ("Planet Calypso", "Lv. 16-24 (Young/Mature)", "63500, 86200 (Nea's Place)", "Ambulimax Hide, Thyroid Oil, Martial Parts (118-135% MU)", "/wp [Calypso, 63500, 86200, 120, Ambulimax]"),
    "Argonaut": ("Planet Calypso", "Lv. 5-12 (Young/Scout)", "77200, 77900 (Twin Peaks / Fort Argus)", "Iron Stone, Muscle Oil, Soft Hide (110-120% MU)", "/wp [Calypso, 77200, 77900, 120, Argonaut]"),
    "Armax": ("Planet Calypso", "Lv. 12-20 (Cow/Bull Young)", "71800, 83400 (Fort Pandora / North)", "Armax Skull, Horn, Hide, Muscle Oil (115-130% MU)", "/wp [Calypso, 71800, 83400, 125, Armax]"),
    "Atrax": ("Planet Calypso", "Lv. 11-18 (Young/Mature)", "76400, 68500 (Ithaca / Fort Fury)", "Atrax Bone, Animal Muscle Oil (115-130% MU)", "/wp [Calypso, 76400, 68500, 130, Atrax]"),
    "Atrox": ("Planet Calypso", "Lv. 16-28 (Young/Old)", "75300, 69100 (Ithaca / North)", "Atrox Bone, Thyroid Oil, Jaguar Parts (120-140% MU)", "/wp [Calypso, 75300, 69100, 130, Atrox]"),
    "Beladoth": ("Planet Arkadia", "Lv. 12-19 (Young/Mature)", "19800, 21400 (Relentless Firebase)", "Beladoth Hide, Pancreas Oil (115-130% MU)", "/wp [Arkadia, 19800, 21400, 115, Beladoth]"),
    "Berycled": ("Planet Calypso", "Lv. 3-7 (Young/Mature)", "61500, 75200 (Camp Icarus / Port Atlantis)", "Berycled Claw, Fine Hide (105-115% MU)", "/wp [Calypso, 61500, 75200, 110, Berycled]"),
    "Bokol": ("Planet Arkadia", "Lv. 9-16 (Young/Mature)", "20900, 18500 (Celeste South)", "Bokol Hide, Muscle Oil (112-125% MU)", "/wp [Arkadia, 20900, 18500, 115, Bokol]"),
    "Carabok": ("Planet Arkadia", "Lv. 1-4 (Punies/Young)", "28500, 18200 (Celeste Quarry)", "Carabok Hide, Animal Eye Oil (110-125% MU)", "/wp [Arkadia, 28500, 18200, 110, Carabok]"),
    "Caudatergus": ("Planet Calypso", "Lv. 4-9 (Young/Mature)", "63200, 76800 (Half Moon Cove)", "Caudatergus Horn, Wool (108-118% MU)", "/wp [Calypso, 63200, 76800, 110, Caudatergus]"),
    "Combibo": ("Planet Calypso", "Lv. 3-8 (Young/Mature)", "65400, 76100 (Port Atlantis / Swamp)", "Combibo Skin, Soft Hide, Eye Oil (108-118% MU)", "/wp [Calypso, 65400, 76100, 110, Combibo]"),
    "Cornundacauda": ("Planet Calypso", "Lv. 5-11 (Young/Mature)", "66800, 78400 (Swamp Camp / PA)", "Cornundacauda Tentacle, Soft Hide (110-122% MU)", "/wp [Calypso, 66800, 78400, 115, Cornundacauda]"),
    "Cornundos": ("Planet Calypso", "Lv. 4-9 (Young/Mature)", "67900, 79100 (North of Swamp Camp)", "Cornundos Skin, Fine Hide (108-118% MU)", "/wp [Calypso, 67900, 79100, 115, Cornundos]"),
    "Crystal Pede": ("Monria", "Lv. 12-22 (Young/Mature)", "38200, 21500 (DSEC Forensics / Caves)", "Shrapnel, Monria Plating, Eye Oil (115-135% MU)", "/wp [Monria, 38200, 21500, 100, Crystal Pede]"),
    "Daikiba": ("Planet Calypso", "Lv. 2-6 (Young/Mature)", "62100, 75900 (Camp Icarus)", "Daikiba Wool, Soft Hide (108-120% MU)", "/wp [Calypso, 62100, 75900, 110, Daikiba]"),
    "Dire Weed": ("Planet Calypso", "Lv. 6-12 (Young/Mature)", "70500, 73200 (Chug's Hideout)", "Adaptive Fire Rate, Muscle Oil (112-125% MU)", "/wp [Calypso, 70500, 73200, 115, Dire Weed]"),
    "Drone": ("Planet Calypso", "Lv. 12-24 (Gen 01-06)", "82400, 77100 (Jason Centre)", "Robot Components, Gaze Unit, Tier Comps (120-150% MU)", "/wp [Calypso, 82400, 77100, 130, Drone]"),
    "Empis": ("Planet Cyrene", "Lv. 6-13 (Young/Mature)", "134900, 78200 (Cyrene Plains)", "Empis Wing, Cyrene Oils (110-125% MU)", "/wp [Cyrene, 134900, 78200, 110, Empis]"),
    "Estophyl": ("Planet Calypso", "Lv. 13-20 (Young/Mature)", "66200, 83900 (Fort Pandora West)", "Estophyl Skin, Thyroid Oil (115-130% MU)", "/wp [Calypso, 66200, 83900, 120, Estophyl]"),
    "Exarosaur": ("Planet Calypso", "Lv. 2-6 (Young/Mature)", "61800, 76400 (Swamp Camp)", "Exarosaur Tooth, Wool, Soft Hide (110-125% MU)", "/wp [Calypso, 61800, 76400, 110, Exarosaur]"),
    "Faucervix": ("Planet Calypso", "Lv. 6-12 (Young/Mature)", "73100, 81200 (Fort Troy)", "Faucervix Horn, Fine Hide (110-120% MU)", "/wp [Calypso, 73100, 81200, 120, Faucervix]"),
    "Feffoid": ("Planet Calypso", "Lv. 10-18 (Outcast/Bandit)", "78900, 84200 (Fort Fury / Boreas)", "Feffoid Blood, Cold Resistance, Korss H400 (115-135% MU)", "/wp [Calypso, 78900, 84200, 125, Feffoid]"),
    "Feran": ("Planet Arkadia", "Lv. 8-15 (Young/Mature)", "24100, 15900 (Resolute Firebase)", "Feran Hide, Animal Pancreas Oil (112-128% MU)", "/wp [Arkadia, 24100, 15900, 115, Feran]"),
    "Foul": ("Planet Calypso", "Lv. 6-13 (Young/Adult)", "74500, 78100 (Fort Argus / Boreas)", "Foul Bone, Button, Muscle Oil (115-130% MU)", "/wp [Calypso, 74500, 78100, 125, Foul]"),
    "Fugabarba": ("Planet Calypso", "Lv. 1-3 (Punies/Young)", "61900, 75400 (Camp Icarus)", "Fugabarba Hide, Eye Oil (105-115% MU)", "/wp [Calypso, 61900, 75400, 110, Fugabarba]"),
    "Gallard": ("Planet Arkadia", "Lv. 1-4 (Punies/Young)", "29100, 17800 (Celeste Harbour)", "Gallard Hide, Eye Oil (108-118% MU)", "/wp [Arkadia, 29100, 17800, 110, Gallard]"),
    "Gokibusagi": ("Planet Calypso", "Lv. 9-16 (Young/Mature)", "72400, 74900 (Chimera Canyons)", "Gokibusagi Skin, Muscle Oil (112-125% MU)", "/wp [Calypso, 72400, 74900, 120, Gokibusagi]"),
    "Gradivore": ("Planet Calypso", "Lv. 5-10 (Young/Mature)", "64100, 77900 (Swamp Camp North)", "Gradivore Wool, Soft Hide (108-118% MU)", "/wp [Calypso, 64100, 77900, 110, Gradivore]"),
    "Halix": ("Planet Arkadia", "Lv. 4-9 (Young/Mature)", "26800, 16500 (Sanctuary Cove)", "Halix Tail, Fine Hide (110-122% MU)", "/wp [Arkadia, 26800, 16500, 115, Halix]"),
    "Hiryuu": ("Planet Calypso", "Lv. 7-14 (Young/Mature)", "75800, 76200 (Twin Peaks South)", "Hiryuu Skin, Fine Hide (112-124% MU)", "/wp [Calypso, 75800, 76200, 125, Hiryuu]"),
    "Hornet": ("Planet Arkadia", "Lv. 6-12 (Young/Mature)", "22500, 19400 (Courageous Firebase)", "Hornet Wing, Thyroid Oil (112-125% MU)", "/wp [Arkadia, 22500, 19400, 115, Hornet]"),
    "Huon": ("Planet Arkadia", "Lv. 11-18 (Young/Mature)", "21200, 20800 (Defiant Firebase)", "Huon Hide, Thyroid Oil (114-128% MU)", "/wp [Arkadia, 21200, 20800, 115, Huon]"),
    "Imperium": ("Planet Cyrene", "Lv. 10-20 (Scout/Soldier)", "138500, 77200 (Imperium Outpost)", "Imperium Tokens, Components (120-145% MU)", "/wp [Cyrene, 138500, 77200, 110, Imperium]"),
    "Itumatrox": ("Planet Calypso", "Lv. 14-21 (Young/Mature)", "81200, 81500 (Fort Zeus)", "Itumatrox Skin, Thyroid Oil (115-130% MU)", "/wp [Calypso, 81200, 81500, 125, Itumatrox]"),
    "Jori": ("Planet Arkadia", "Lv. 3-7 (Young/Mature)", "27400, 18900 (Celeste Outpost)", "Jori Hide, Soft Hide (108-118% MU)", "/wp [Arkadia, 27400, 18900, 110, Jori]"),
    "Kadra": ("Planet Arkadia", "Lv. 13-20 (Young/Mature)", "18900, 19600 (Relentless North)", "Kadra Hide, Pancreas Oil (115-130% MU)", "/wp [Arkadia, 18900, 19600, 115, Kadra]"),
    "Kamaldon": ("Planet Arkadia", "Lv. 15-22 (Young/Mature)", "17500, 22100 (Arkadia Deep Wilds)", "Kamaldon Hide, Rare Oils (118-135% MU)", "/wp [Arkadia, 17500, 22100, 115, Kamaldon]"),
    "Kerberos": ("Planet Calypso", "Lv. 8-15 (Young/Mature)", "64900, 84500 (Fort Pandora)", "Kerberos Bone, Thyroid Oil (115-130% MU)", "/wp [Calypso, 64900, 84500, 120, Kerberos]"),
# ==============================================================================
# >>>>>> BLOCK >>> E <<< (PLANET MOB DATABASE PART 2: K - Z)
# ==============================================================================

     "Drill Bot": ("Planet Cyrene", "Lv. 4-9 (Small Robot)", "135400, 76800 (A.R.C. Staging / Robot Area)", "Electronic Comps, Motion Sensors, Kinsite Ore (115-135% MU)", "/wp [Cyrene, 135400, 76800, 110, Drill Bot]"),
    "Oratan Prospector": ("Planet Arkadia", "Lv. 8-16 (Young/Mature)", "21500, 19800 (IFN Outposts / Arkadia)", "Oratan Axe, Arkadian Oils, Weapons (115-135% MU)", "/wp [Arkadia, 21500, 19800, 115, Oratan Prospector]"),
    "Scout Bot": ("Planet Cyrene", "Lv. 3-7 (Small Robot)", "136100, 77400 (Cyrene Robot Outpost)", "Basic Targeting Chip, Electronic Comps (115-130% MU)", "/wp [Cyrene, 136100, 77400, 110, Scout Bot]"),
    "Starving Atrax": ("Planet Calypso", "Lv. 8-12 (Low HP Atrax)", "76400, 68500 (Ithaca / Fort Fury)", "Atrax Bone, Animal Muscle Oil (115-130% MU)", "/wp [Calypso, 76400, 68500, 130, Starving Atrax]"),
  
"Kreltin": ("Planet Calypso", "Lv. 15-23 (Young/Mature)", "84200, 86500 (Crystal Palace / North)", "Kreltin Soft Shell, Rare Loot (120-140% MU)", "/wp [Calypso, 84200, 86500, 125, Kreltin]"),
    "Longu": ("Planet Calypso", "Lv. 11-19 (Young/Mature)", "62400, 81500 (Longu Land / North)", "Longu Claw, Skin, Muscle Oil (115-130% MU)", "/wp [Calypso, 62400, 81500, 120, Longu]"),
    "Mang Chang": ("Planet Calypso", "Lv. 35-55 (Young/Mature)", "86500, 89200 (East Scylla)", "High-end Armor/Weapons, Rare Oils (125-160% MU)", "/wp [Calypso, 86500, 89200, 140, Mang Chang]"),
    "Merp": ("Planet Calypso", "Lv. 4-9 (Young/Mature)", "69200, 77500 (Billy's Spaceship)", "Merp Wool, Soft Hide (110-122% MU)", "/wp [Calypso, 69200, 77500, 115, Merp]"),
    "Molisk": ("Planet Calypso", "Lv. 7-14 (Young/Scout)", "67500, 74800 (Port Atlantis South)", "Molisk Tooth, Skin, Eye Oil (115-130% MU)", "/wp [Calypso, 67500, 74800, 115, Molisk]"),
    "Mourner": ("Planet Calypso", "Lv. 8-15 (Young/Mature)", "71200, 71800 (Fort Troy West)", "Mourner Skin, Muscle Oil (112-125% MU)", "/wp [Calypso, 71200, 71800, 120, Mourner]"),
    "Nusul": ("Planet Arkadia", "Lv. 5-10 (Young/Mature)", "25600, 14800 (Steadfast Firebase)", "Nusul Hide, Muscle Oil (110-120% MU)", "/wp [Arkadia, 25600, 14800, 115, Nusul]"),
    "Oculus": ("Planet Calypso", "Lv. 14-21 (Young/Mature)", "79400, 85100 (Fort Fury North)", "Oculus Skin, Thyroid Oil (115-130% MU)", "/wp [Calypso, 79400, 85100, 125, Oculus]"),
    "Oro": ("Planet Arkadia", "Lv. 7-14 (Young/Mature)", "21900, 16200 (Valiant Firebase)", "Oro Hide, Pancreas Oil (112-125% MU)", "/wp [Arkadia, 21900, 16200, 115, Oro]"),
    "Paneleon": ("Planet Cyrene", "Lv. 8-15 (Young/Mature)", "137400, 77800 (Cyrene Central)", "Paneleon Pelt, Cyrene Components (112-128% MU)", "/wp [Cyrene, 137400, 77800, 110, Paneleon]"),
    "Pleader": ("Planet Cyrene", "Lv. 5-11 (Young/Mature)", "135200, 79100 (0x101 Supply Depot)", "Pleader Pelt, Cyrene Components (112-128% MU)", "/wp [Cyrene, 135200, 79100, 110, Pleader]"),
    "Plumatergus": ("Planet Calypso", "Lv. 5-10 (Young/Mature)", "68100, 76900 (Bilton Towers)", "Plumatergus Wing, Soft Hide (108-120% MU)", "/wp [Calypso, 68100, 76900, 115, Plumatergus]"),
    "Repesilex": ("Planet Calypso", "Lv. 6-12 (Young/Mature)", "63900, 73500 (New Oxford Coast)", "Repesilex Skin, Fine Hide (110-122% MU)", "/wp [Calypso, 63900, 73500, 110, Repesilex]"),
    "Rextelum": ("Planet Calypso", "Lv. 16-24 (Weak/Hunter)", "83100, 79500 (Minopolis / North)", "Rextelum Chitin, Rare Parts (120-140% MU)", "/wp [Calypso, 83100, 79500, 125, Rextelum]"),
    "Rhino Beetle": ("Planet Calypso", "Lv. 9-16 (Young/Mature)", "79800, 72400 (Nymphtown)", "Rhino Carapace, Muscle Oil (115-128% MU)", "/wp [Calypso, 79800, 72400, 120, Rhino Beetle]"),
    "Rippersnapper": ("Planet Calypso", "Lv. 5-11 (Young/Mature)", "61000, 75000 (Rivers & Coasts)", "Rippersnapper Skin, Eye Oil (108-120% MU)", "/wp [Calypso, 61000, 75000, 100, Rippersnapper]"),
    "Sabakuma": ("Planet Calypso", "Lv. 2-6 (Young/Mature)", "62800, 75100 (Port Atlantis)", "Sabakuma Skin, Eye Oil (105-115% MU)", "/wp [Calypso, 62800, 75100, 110, Sabakuma]"),
    "Sea Wraith": ("Planet Calypso", "Lv. 14-24 (Young/Mature)", "60200, 88100 (North Coast)", "Sea Wraith Scale, Thyroid Oil (115-130% MU)", "/wp [Calypso, 60200, 88100, 100, Sea Wraith]"),
    "Snablesnot": ("Planet Calypso", "Lv. 1-4 (Male/Female)", "61200, 75600 (Port Atlantis / Icarus)", "Snablesnot Skin, Eye Oil (105-115% MU)", "/wp [Calypso, 61200, 75600, 110, Snablesnot]"),
    "Snarksnot": ("Planet Calypso", "Lv. 4-9 (Young/Mature)", "65900, 77200 (Swamp Camp East)", "Snarksnot Skin, Soft Hide (108-118% MU)", "/wp [Calypso, 65900, 77200, 110, Snarksnot]"),
    "Tantardion": ("Planet Calypso", "Lv. 11-18 (Young/Mature)", "74900, 82900 (Fort Pandora East)", "Tantardion Skin, Muscle Oil (114-128% MU)", "/wp [Calypso, 74900, 82900, 120, Tantardion]"),
    "Tantillion": ("Planet Calypso", "Lv. 5-10 (Young/Mature)", "72100, 78900 (Fort Argus West)", "Tantillion Skin, Fine Hide (110-120% MU)", "/wp [Calypso, 72100, 78900, 120, Tantillion]"),
    "Tiarak": ("Planet Arkadia", "Lv. 10-17 (Young/Mature)", "22800, 17900 (Courageous South)", "Tiarak Hide, Pancreas Oil (112-126% MU)", "/wp [Arkadia, 22800, 17900, 115, Tiarak]"),
    "Tide Claw": ("Planet Cyrene", "Lv. 4-9 (Young/Mature)", "136800, 76400 (Tide Claw Beach)", "Tide Claw Shell, Soft Hide (110-122% MU)", "/wp [Cyrene, 136800, 76400, 110, Tide Claw]"),
    "Tree Dragon": ("Planet Cyrene", "Lv. 7-14 (Young/Mature)", "135900, 77100 (Cyrene Forest)", "Tree Dragon Scale, Cyrene Oils (112-125% MU)", "/wp [Cyrene, 135900, 77100, 110, Tree Dragon]"),
    "Tripudion": ("Planet Calypso", "Lv. 6-12 (Young/Mature)", "71400, 76500 (Fort Troy North)", "Tripudion Skin, Fine Hide (110-122% MU)", "/wp [Calypso, 71400, 76500, 120, Tripudion]"),
    "Ubo": ("Planet Arkadia", "Lv. 8-15 (Young/Mature)", "24900, 19100 (Resolute East)", "Ubo Hide, Muscle Oil (112-125% MU)", "/wp [Arkadia, 24900, 19100, 115, Ubo]"),
    "Vrex": ("Planet Calypso", "Lv. 14-21 (Young/Mature)", "80500, 74200 (Nymphtown North)", "Vrex Skin, Thyroid Oil (115-130% MU)", "/wp [Calypso, 80500, 74200, 120, Vrex]"),
    "Yuka": ("Planet Arkadia", "Lv. 6-12 (Young/Mature)", "26100, 17400 (Sanctuary North)", "Yuka Hide, Fine Hide (110-122% MU)", "/wp [Arkadia, 26100, 17400, 115, Yuka]"),
    "Zadul": ("Planet Arkadia", "Lv. 5-10 (Young/Mature)", "23500, 17400 (Resolute / Steadfast)", "Zadul Hide, Animal Muscle Oil (112-125% MU)", "/wp [Arkadia, 23500, 17400, 115, Zadul]"),
    "Zeladoth": ("Planet Cyrene", "Lv. 12-20 (Young/Mature)", "139100, 78500 (Cyrene Wilds)", "Zeladoth Hide, Cyrene Components (115-132% MU)", "/wp [Cyrene, 139100, 78500, 110, Zeladoth]"),
    "Zombie": ("Planet Calypso", "Event (Gravefiend/Deathbringer)", "61800, 76400 (Event Spawns)", "Event Loot, Shrapnel, Oils (110-130% MU)", "/wp [Calypso, 61800, 76400, 110, Zombie]")
}

pianeta_mob, grado_mob, coord_mob, drop_mob, wp_mob = INFO_MOB.get(
    mob_selezionato,
    ("Check EntropiaWiki", "Variable", "Check local spawns", "Shrapnel, Oils, Hides (105-120% MU)", f"/wp [Calypso, 70000, 75000, 110, {mob_selezionato}]")
)
# ==============================================================================
# >>>>>> BLOCK >>> F <<< (PREDICTOR CALCULATIONS & SIDEBAR SUMMARY)
# ==============================================================================

ora_attuale = datetime.now()
inizio_oggi = ora_attuale.replace(hour=0, minute=0, second=0, microsecond=0)
sette_giorni_fa = ora_attuale - timedelta(days=7)

pattern_mob = r"\b" + re.escape(mob_selezionato.lower()) + r"\b"
df_mob = df_globale[df_globale['Mob'].str.lower().str.contains(pattern_mob, na=False, regex=True)].copy()
df_oggi = df_mob[df_mob['Timestamp'] >= inizio_oggi].copy()
df_7gg = df_mob[df_mob['Timestamp'] >= sette_giorni_fa].copy()

escludi_craft = ("shrapnel", "explosive", "basic", "simple", "component", "filter", "welding", "texture", "arkadian", "generic")
df_tutti_oggi = df_globale[df_globale['Timestamp'] >= inizio_oggi].copy()
df_creatures_oggi = df_tutti_oggi[~df_tutti_oggi['Mob'].str.lower().str.startswith(escludi_craft, na=False)]
if len(df_creatures_oggi) > 0:
    top_oggi = ", ".join([f"{m} ({c})" for m, c in df_creatures_oggi['Mob'].value_counts().head(5).items()])
    st.sidebar.info(f"📅 **Today Creatures ({len(df_creatures_oggi)}):** {top_oggi}")
else:
    ultima_data = df_globale['Timestamp'].max() if len(df_globale) > 0 else "No data"
    st.sidebar.warning(f"📅 **0 Creature Globals today.** Latest in CSV: `{ultima_data}`")

df_7gg_pulito = df_7gg[df_7gg['PED'] <= 400].copy()
if len(df_7gg_pulito) >= 5:
    giorni_attivi = max(1, df_7gg_pulito['Timestamp'].dt.date.nunique())
    media_ped_giornaliera = df_7gg_pulito['PED'].sum() / giorni_attivi
    fonte_statistica = f"Clean History ({giorni_attivi}d, No MegaHoF)"
else:
    giorni_attivi = max(1, df_7gg_pulito['Timestamp'].dt.date.nunique()) if len(df_7gg_pulito) > 0 else 0
    media_ped_giornaliera = float(target_manuale_ped)
    fonte_statistica = "Manual Base Target"

frazione_giornata = max(0.04, (ora_attuale.hour * 60 + ora_attuale.minute) / 1440.0)
attesi_entro_questa_ora = max(50.0, media_ped_giornaliera * frazione_giornata)

ped_totali_oggi = float(df_oggi['PED'].sum()) if len(df_oggi) > 0 else 0.0
qta_global_oggi = len(df_oggi)
ped_medio_singolo_oggi = (ped_totali_oggi / qta_global_oggi) if qta_global_oggi > 0 else 0.0
percentuale_budget_orario = (ped_totali_oggi / attesi_entro_questa_ora) * 100.0 if attesi_entro_questa_ora > 0 else 0.0

ped_accumulo_settimana = float(df_7gg_pulito['PED'].sum()) if len(df_7gg_pulito) > 0 else 0.0
qta_global_settimana = len(df_7gg)
ped_medio_settimana = (float(df_7gg['PED'].sum()) / qta_global_settimana) if qta_global_settimana > 0 else 0.0

if len(df_mob) > 0:
    ultimo_ts = df_mob['Timestamp'].max()
    minuti_dall_ultimo = max(0.0, (ora_attuale - ultimo_ts).total_seconds() / 60.0)
else:
    minuti_dall_ultimo = 999.0

if len(df_7gg) >= 3:
    df_7gg_sorted = df_7gg.sort_values('Timestamp')
    differenze_min = df_7gg_sorted['Timestamp'].diff().dt.total_seconds().dropna() / 60.0
    differenze_valide = differenze_min[(differenze_min > 0) & (differenze_min <= 480)]
    media_attesa_minuti = float(differenze_valide.median()) if len(differenze_valide) > 0 else 60.0
else:
    media_attesa_minuti = 60.0

quindici_min_fa = ora_attuale - timedelta(minutes=15)
venti_min_fa = ora_attuale - timedelta(minutes=20)
df_ultimi_15m = df_mob[df_mob['Timestamp'] >= quindici_min_fa]
df_ultimi_20m = df_mob[df_mob['Timestamp'] >= venti_min_fa]

qta_15m = len(df_ultimi_15m)
ped_15m = float(df_ultimi_15m['PED'].sum()) if qta_15m > 0 else 0.0
max_ped_20m = float(df_ultimi_20m['PED'].max()) if len(df_ultimi_20m) > 0 else 0.0
qta_20m = len(df_ultimi_20m)

onda_attiva = qta_15m >= 2 and max_ped_20m < soglia_hof_stop

punteggio_ritardo = min(40, int((minuti_dall_ultimo / max(15.0, media_attesa_minuti)) * 25)) if minuti_dall_ultimo < 900 else 20
punteggio_deficit = min(35, max(0, int((1.0 - (ped_totali_oggi / max(1.0, attesi_entro_questa_ora))) * 35)))
punteggio_onda = 25 if onda_attiva else (15 if qta_15m == 1 and max_ped_20m < soglia_hof_stop else 0)
indice_pressione_pool = min(100, max(5, punteggio_ritardo + punteggio_deficit + punteggio_onda))
# ==============================================================================
# >>>>>> BLOCK >>> G <<< (SECTION 1: LIVE REAL-TIME & DAILY HISTOGRAM)
# ==============================================================================

st.title(f"🚦 Loot & Timing Predictor: {mob_selezionato}")

c1, c2, c3, c4, c5 = st.columns([1.1, 1.2, 1.4, 1.6, 1.5])
with c1:
    st.info(f"🪐 **Planet:** {pianeta_mob}")
with c2:
    st.info(f"⚔️ **Maturity / HP:** {grado_mob}")
with c3:
    st.info(f"📍 **Coords (Lon / Lat):** {coord_mob}")
with c4:
    st.success(f"💰 **Drop & Markup:** {drop_mob}")
with c5:
    st.caption("📋 Copy Waypoint in game chat:")
    st.code(wp_mob, language="text")

st.markdown("---")
st.subheader("⚡ 1. Live Real-Time & Today's Activity")

# --- TRAFFIC LIGHT 1 (TOP): LIVE REACTIVE 15m ---
if max_ped_20m >= soglia_hof_stop:
    colore_l = "rossa"
    titolo_l = "LIVE 15m: STOP (HOF DRAIN)"
    desc_l = f"Recent HoF >= {soglia_hof_stop} PED detected. Do not chase right after a big hit."
    stato_audio_l = "ROSSO"
elif onda_attiva:
    colore_l = "verde"
    titolo_l = f"LIVE 15m: ACTIVE WAVE! ({qta_15m} Globals)"
    desc_l = f"{qta_15m} Globals ({ped_15m:.0f} PED) in the last 15m! Jump in now before others!"
    stato_audio_l = "VERDE"
elif qta_15m == 1:
    colore_l = "gialla"
    titolo_l = f"LIVE 15m: 1 GLOBAL ({ped_15m:.0f} PED)"
    desc_l = f"First signal detected in 15m. Watch for a 2nd Global or probe with {ped_ammo_run} PED."
    stato_audio_l = "GIALLO"
else:
    colore_l = "gialla"
    titolo_l = "LIVE 15m: WATCHING"
    desc_l = f"{qta_20m} Globals in the last 20 min. Wait for a trigger or probe with {ped_ammo_run} PED."
    stato_audio_l = "GIALLO"

st.markdown(f"""
<div class="semaforo-box">
    <div class="luce luce-{colore_l}"></div>
    <div class="testo-semaforo">
        <h2>{titolo_l}</h2>
        <p>{desc_l}</p>
    </div>
</div>
""", unsafe_allow_html=True)

d1, d2, d3, d4 = st.columns(4)
with d1:
    st.metric(
        label="Pool Pressure (Predictor)",
        value=f"{indice_pressione_pool}%",
        delta="🔥 WAVE ACTIVE" if onda_attiva else ("Loaded" if indice_pressione_pool >= 65 else "Normal"),
        help="0-100% index based on time delay, hourly deficit and recent bursts"
    )
with d2:
    st.metric(
        label="Total PED Today vs Now",
        value=f"{ped_totali_oggi:.0f} PED",
        delta=f"{ped_totali_oggi - attesi_entro_questa_ora:.0f} vs Expected Now"
    )
with d3:
    st.metric(
        label="Today Globals & Avg",
        value=f"{qta_global_oggi} ({ped_medio_singolo_oggi:.0f} PED)",
        help="Number of Globals today and their average PED value"
    )
with d4:
    st.metric(
        label="Time Since Last Global",
        value=f"{minuti_dall_ultimo:.0f} min" if minuti_dall_ultimo < 900 else "N/A",
        delta=f"Median: {media_attesa_minuti:.0f} min",
        delta_color="inverse"
    )

ore_giornata = list(range(24))
df_oggi['Timestamp'] = pd.to_datetime(df_oggi['Timestamp'], errors='coerce')
df_oggi['Ora'] = df_oggi['Timestamp'].dt.hour

riepilogo_orario = df_oggi.groupby('Ora').agg(
    Quantita=('PED', 'count'),
    Totale_PED=('PED', 'sum')
).reindex(ore_giornata, fill_value=0).reset_index()

riepilogo_orario['Etichetta_Ora'] = riepilogo_orario['Ora'].apply(lambda x: f"{x:02d}:00")

fig_oggi = go.Figure()
fig_oggi.add_trace(go.Bar(
    x=riepilogo_orario['Etichetta_Ora'],
    y=riepilogo_orario['Totale_PED'],
    name='Total PED Paid (Today)',
    marker_color='#00e676',
    yaxis='y1',
    text=riepilogo_orario['Totale_PED'].apply(lambda v: f"{v:.0f}" if v > 0 else ""),
    textposition='auto'
))
fig_oggi.add_trace(go.Bar(
    x=riepilogo_orario['Etichetta_Ora'],
    y=riepilogo_orario['Quantita'],
    name='Globals Count (#)',
    marker_color='#29b6f6',
    yaxis='y2',
    text=riepilogo_orario['Quantita'].apply(lambda v: f"{v}" if v > 0 else ""),
    textposition='auto'
))
fig_oggi.add_vline(x=ora_attuale.hour, line_dash="dash", line_color="#ffea00", annotation_text="Current Hour")
fig_oggi.update_layout(
    title=f"Daily Hourly Histogram ({ora_attuale.strftime('%Y-%m-%d')}) — Count & PED per Hour",
    barmode='group',
    xaxis=dict(title="Time Slot (00:00 - 23:00)", showgrid=False),
    yaxis=dict(title="Total Global PED", side="left", showgrid=True, gridcolor="#333"),
    yaxis2=dict(title="Globals Count", side="right", overlaying="y", showgrid=False, dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=50, b=20),
    hovermode="x unified",
    height=370
)
st.plotly_chart(fig_oggi, use_container_width=True)
# ==============================================================================
# >>>>>> BLOCK >>> H <<< (SECTION 2: WEEKLY TREND, 7-DAY CHART & PLAYER TABLE)
# ==============================================================================

st.markdown("---")
st.subheader("📈 2. Weekly Trend & 7-Day Historical Analysis")

# --- TRAFFIC LIGHT 2 (BOTTOM): WEEKLY / HOURLY TREND ---
if max_ped_20m >= soglia_hof_stop:
    colore_t = "rossa"
    titolo_t = f"TREND: POOL DRAINED ({max_ped_20m:.0f} PED HoF)"
    desc_t = f"A big HoF ({max_ped_20m:.0f} PED) hit in the last 20m. Pool is drained — wait or switch mob."
    stato_audio_t = "ROSSO"
elif percentuale_budget_orario < 75 and indice_pressione_pool >= 60:
    colore_t = "verde"
    titolo_t = f"TREND: POOL LOADED ({ped_ammo_run} PED RUN)"
    desc_t = f"Paid {ped_totali_oggi:.0f}/{attesi_entro_questa_ora:.0f} PED ({percentuale_budget_orario:.0f}%). Strong payout backlog!"
    stato_audio_t = "VERDE"
elif percentuale_budget_orario > 135:
    colore_t = "rossa"
    titolo_t = "TREND: DAILY QUOTA EXCEEDED"
    desc_t = f"Paid {ped_totali_oggi:.0f}/{attesi_entro_questa_ora:.0f} PED ({percentuale_budget_orario:.0f}%). Over target — slow payout risk."
    stato_audio_t = "ROSSO"
else:
    colore_t = "gialla"
    titolo_t = f"TREND: PROBING ({ped_ammo_run} PED)"
    desc_t = f"Paid {ped_totali_oggi:.0f}/{attesi_entro_questa_ora:.0f} PED. Do max 1 test run of {ped_ammo_run} PED."
    stato_audio_t = "GIALLO"

stato_combinato = f"{stato_audio_t}_{stato_audio_l}"
if st.session_state.get("ultimo_stato_audio") != stato_combinato:
    st.session_state["ultimo_stato_audio"] = stato_combinato
    if "VERDE" in stato_combinato:
        attiva_allarme_sonoro("VERDE")
    elif "ROSSO" in stato_combinato:
        attiva_allarme_sonoro("ROSSO")

st.markdown(f"""
<div class="semaforo-box">
    <div class="luce luce-{colore_t}"></div>
    <div class="testo-semaforo">
        <h2>{titolo_t}</h2>
        <p>{desc_t}</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.write(f"**Hourly Distribution ({fonte_statistica}):** Paid **{ped_totali_oggi:.0f} PED** out of **{attesi_entro_questa_ora:.0f} PED** expected by {ora_attuale.strftime('%H:%M')} (Full day avg: {media_ped_giornaliera:.0f} PED)")
progresso = min(percentuale_budget_orario / 100.0, 1.0)
st.progress(progresso)

w1, w2, w3, w4 = st.columns(4)
with w1:
    st.metric(
        label="7-Day Clean Accumulation",
        value=f"{ped_accumulo_settimana:.0f} PED",
        help="Normalized PED total (excluding MegaHoFs >400) over the last 7 days"
    )
with w2:
    st.metric(
        label="Clean Daily Average",
        value=f"{media_ped_giornaliera:.0f} PED/day",
        delta=fonte_statistica
    )
with w3:
    st.metric(
        label="7-Day Globals Count",
        value=f"{qta_global_settimana} Globals",
        delta=f"Avg: {ped_medio_settimana:.0f} PED"
    )
with w4:
    st.metric(
        label="Active Days (Last 7d)",
        value=f"{giorni_attivi} / 7 days",
        help="Days with recorded Globals in the last week"
    )

# --- 7-DAY WEEKLY HISTOGRAM ---
ultimi_7_giorni = [(ora_attuale.date() - timedelta(days=i)) for i in range(6, -1, -1)]
df_7gg['Data'] = pd.to_datetime(df_7gg['Timestamp'], errors='coerce').dt.date

riepilogo_settimana = df_7gg.groupby('Data').agg(
    Quantita=('PED', 'count'),
    Totale_PED=('PED', 'sum')
).reindex(ultimi_7_giorni, fill_value=0).reset_index()

riepilogo_settimana['Etichetta_Giorno'] = riepilogo_settimana['Data'].apply(lambda d: d.strftime('%a %d/%m'))

fig_sett = go.Figure()
fig_sett.add_trace(go.Bar(
    x=riepilogo_settimana['Etichetta_Giorno'],
    y=riepilogo_settimana['Totale_PED'],
    name='Weekly PED Paid',
    marker_color='#00e676',
    yaxis='y1',
    text=riepilogo_settimana['Totale_PED'].apply(lambda v: f"{v:.0f}" if v > 0 else ""),
    textposition='auto'
))
fig_sett.add_trace(go.Bar(
    x=riepilogo_settimana['Etichetta_Giorno'],
    y=riepilogo_settimana['Quantita'],
    name='Globals Count (#)',
    marker_color='#29b6f6',
    yaxis='y2',
    text=riepilogo_settimana['Quantita'].apply(lambda v: f"{v}" if v > 0 else ""),
    textposition='auto'
))
fig_sett.update_layout(
    title="7-Day Historical Histogram — Daily PED & Globals Count",
    barmode='group',
    xaxis=dict(title="Last 7 Days", showgrid=False),
    yaxis=dict(title="Total Global PED", side="left", showgrid=True, gridcolor="#333"),
    yaxis2=dict(title="Globals Count", side="right", overlaying="y", showgrid=False, dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=50, b=20),
    hovermode="x unified",
    height=360
)
st.plotly_chart(fig_sett, use_container_width=True)

with st.expander("📋 View last 10 Globals/HoFs recorded for this mob"):
    if len(df_mob) > 0:
        ultimi_10 = df_mob.sort_values('Timestamp', ascending=False).head(10).copy()
        ultimi_10['Timestamp'] = ultimi_10['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        cols_visibili = [c for c in ['Timestamp', 'Player', 'Mob', 'PED'] if c in ultimi_10.columns]
        st.dataframe(ultimi_10[cols_visibili], use_container_width=True, hide_index=True)
    else:
        st.info("No Globals found yet for this mob.")

time.sleep(10)
st.rerun()

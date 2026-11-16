# ==============================================================================
# >>>>>> BLOCK >>> A <<< (SETTINGS, TRAFFIC LIGHT UI & BROWSER AUDIO)
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import os
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_ITALIA = ZoneInfo("Europe/Rome")

def ora_italia_now():
    return datetime.now(TZ_ITALIA).replace(tzinfo=None)

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

def attiva_allarme_sonoro(tipo):
    if tipo == "VERDE":
        sequenza = "[[1000, 0.15, 0], [1800, 0.30, 0.18]]"
    elif tipo == "GIALLO":
        sequenza = "[[1200, 0.15, 0], [1200, 0.15, 0.25]]"
    else:
        sequenza = "[[800, 0.20, 0], [600, 0.20, 0.22], [400, 0.35, 0.44]]"

    js_audio = f"""
    <script>
    (function() {{
        try {{
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioCtx();
            const notes = {sequenza};
            notes.forEach(([freq, dur, delay]) => {{
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, ctx.currentTime + delay);
                gain.gain.setValueAtTime(0.25, ctx.currentTime + delay);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + dur);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + delay);
                osc.stop(ctx.currentTime + delay + dur);
            }});
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_audio, height=0, width=0)

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
# >>>>>> BLOCK >>> C <<< (ENTROPIA NEXUS LIVE API & DATA PARSER)
# ==============================================================================

import cloudscraper
import json

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Entropia Nexus Live Feed")

@st.cache_data(ttl=25)
def scarica_da_entropia_nexus(lista_mob_noti):
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    dominio_base = "https://entropianexus.com"
    url_pagina_globals = dominio_base + "/globals"
    adesso = ora_italia_now()
    mobs_ordinati = sorted(lista_mob_noti, key=len, reverse=True)

    try:
        scraper.get(dominio_base, timeout=8)
    except Exception:
        pass

    api_urls = [
        dominio_base + "/api/globals?limit=100",
        dominio_base + "/api/globals",
        dominio_base + "/globals?limit=100"
    ]
    
    headers_api = {
        "Accept": "application/json, text/plain, */*",
        "Referer": dominio_base + "/globals",
        "Origin": dominio_base
    }
    
    # 1. Tentativo API JSON diretta
    for url in api_urls:
        try:
            r = scraper.get(url, headers=headers_api, timeout=10)
            if r.status_code == 200 and r.text.strip().startswith(("{", "[")):
                data = r.json()
                lista_globals = data.get("globals", data.get("data", [])) if isinstance(data, dict) else data
                records = []
                for g in lista_globals:
                    if not isinstance(g, dict):
                        continue
                    tipo = str(g.get("type") or g.get("category") or g.get("profession") or "").lower()
                    if tipo and tipo != "hunting":
                        continue
                    
                    raw_target = g.get("target") or g.get("mob") or g.get("creature") or g.get("name") or ""
                    target_name = str(raw_target.get("name") if isinstance(raw_target, dict) else raw_target).strip()

                    raw_player = g.get("player") or g.get("avatar") or g.get("user") or "Unknown"
                    player_nome = str(raw_player.get("name") if isinstance(raw_player, dict) else raw_player).strip()

                    ped_val = g.get("value") or g.get("ped") or g.get("amount")
                    ts_raw = g.get("timestamp") or g.get("createdAt") or g.get("created_at") or g.get("date")
                    
                    if target_name and ped_val is not None and ts_raw:
                        ts_utc = pd.to_datetime(ts_raw, utc=True, errors="coerce")
                        if pd.notna(ts_utc):
                            ts_it = ts_utc.tz_convert(TZ_ITALIA).tz_localize(None)
                            records.append({
                                "Timestamp": ts_it,
                                "Player": player_nome if player_nome else "Unknown",
                                "Mob": target_name.title(),
                                "PED": int(float(ped_val))
                            })
                if records:
                    return records, True, f"API OK ({len(records)} hunting)"
        except Exception:
            continue

    # 2. Parsing automatico dalla pagina /globals e dalla Homepage
    for web_url in [url_pagina_globals, dominio_base]:
        try:
            r_web = scraper.get(web_url, timeout=12)
            if r_web.status_code == 200:
                html_raw = r_web.text
                records_web = []

                testo = re.sub(r"<[^>]+>", " ", html_raw)
                testo = re.sub(r"\s+", " ", testo)
                
                matches = re.findall(
                    r"Hunting\s+(.+?)\s+(\d+(?:\.\d+)?)\s*PED(?:\s+HoF)?\s+(just now|\d+\s*(?:s|m|h)\s*ago)",
                    testo,
                    re.IGNORECASE
                )
                
                if matches:
                    for blocco_testo, ped_txt, ago_txt in matches:
                        blocco_pulito = blocco_testo.strip()
                        if len(blocco_pulito) > 95:
                            continue
                        
                        minuti_fa = 0
                        if "m" in ago_txt.lower():
                            m_num = re.search(r"\d+", ago_txt)
                            minuti_fa = int(m_num.group()) if m_num else 0
                        elif "h" in ago_txt.lower():
                            h_num = re.search(r"\d+", ago_txt)
                            minuti_fa = int(h_num.group()) * 60 if h_num else 0
                            
                        ts_calc = (adesso - timedelta(minutes=minuti_fa)).replace(second=0, microsecond=0)
                        
                        player_trovato = "Unknown"
                        mob_trovato = blocco_pulito.title()
                        
                        for m_noto in mobs_ordinati:
                            idx = blocco_pulito.lower().find(m_noto.lower())
                            if idx != -1:
                                player_trovato = blocco_pulito[:idx].strip() or "Unknown"
                                mob_trovato = blocco_pulito[idx:].strip().title()
                                break
                        
                        records_web.append({
                            "Timestamp": ts_calc,
                            "Player": player_trovato,
                            "Mob": mob_trovato,
                            "PED": int(float(ped_txt))
                        })
                    
                    if records_web:
                        return records_web, True, f"Web OK ({len(records_web)} hunting)"

                json_matches = re.findall(
                    r'"(?:target|mob|creature)"\s*:\s*"([^"]+)"[^}]*?"(?:value|ped|amount)"\s*:\s*(\d+(?:\.\d+)?)',
                    html_raw
                )
                if json_matches:
                    for mob_raw, ped_raw in json_matches:
                        records_web.append({
                            "Timestamp": adesso.replace(second=0, microsecond=0),
                            "Player": "Unknown",
                            "Mob": mob_raw.strip().title(),
                            "PED": int(float(ped_raw))
                        })
                    if records_web:
                        return records_web, True, f"NextJS OK ({len(records_web)} hunting)"
        except Exception:
            continue

    return [], False, "Cloudflare block su IP cloud"

def aggiorna_database_live():
    if os.path.exists(PATH_DATABASE_CSV) and os.path.getsize(PATH_DATABASE_CSV) > 0:
        try:
            df_storico = pd.read_csv(PATH_DATABASE_CSV)
            df_storico["Timestamp"] = pd.to_datetime(df_storico["Timestamp"], errors="coerce")
            if "Player" not in df_storico.columns:
                df_storico["Player"] = "Unknown"
        except Exception:
            df_storico = pd.DataFrame(columns=["Timestamp", "Player", "Mob", "PED"])
    else:
        df_storico = pd.DataFrame(columns=["Timestamp", "Player", "Mob", "PED"])

    tutti_mobs_noti = [m for mobs in MOBS_PER_PIANETA.values() for m in mobs]
    nuovi_record, api_ok, stato_msg = scarica_da_entropia_nexus(tutti_mobs_noti)

    if nuovi_record:
        df_nuovi = pd.DataFrame(nuovi_record)
        df_totale = pd.concat([df_storico, df_nuovi], ignore_index=True)
    else:
        df_totale = df_storico.copy()

    if len(df_totale) > 0:
        df_totale = df_totale.dropna(subset=["Timestamp", "Mob", "PED"])
        df_totale["Mob"] = df_totale["Mob"].astype(str).str.strip().str.title()
        df_totale["Player"] = df_totale["Player"].fillna("Unknown").astype(str).str.strip()
        df_totale["Ha_Player"] = (df_totale["Player"] != "Unknown").astype(int)

        df_totale = df_totale.sort_values(
            ["Player", "Mob", "PED", "Timestamp", "Ha_Player"],
            ascending=[True, True, True, True, False]
        )

        diff_sec = df_totale.groupby(["Player", "Mob", "PED"])["Timestamp"].diff().dt.total_seconds()
        df_totale = df_totale[diff_sec.isna() | (diff_sec > 300)]

        df_totale = df_totale.drop(columns=["Ha_Player"]).sort_values("Timestamp", ascending=True)
        df_totale.to_csv(PATH_DATABASE_CSV, index=False)

    return df_totale, api_ok, stato_msg

df_globale, nexus_ok, stato_nexus = aggiorna_database_live()

if nexus_ok:
    st.sidebar.success(f"✅ Entropia Nexus LIVE! [{stato_nexus}] ({len(df_globale)} Globals)")
else:
    st.sidebar.warning(f"⚠️ Nexus: {stato_nexus} (CSV: {len(df_globale)} Globals)")

@st.cache_data(show_spinner=False)
def analizza_chat_log_cache(file_bytes):
    try:
        testo_log = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        testo_log = file_bytes.decode("latin-1", errors="ignore")

    pattern_chat = re.compile(
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[Globals\]\s+\[\]\s+(.+?)\s+killed a creature\s+\((.+?)\)\s+with a value of\s+(\d+)\s+PED",
        re.IGNORECASE
    )
    trovati_log = pattern_chat.findall(testo_log)
    nuovi_log = []
    for ts_s, pl_s, mob_s, ped_s in trovati_log:
        ts_dt = pd.to_datetime(ts_s, errors="coerce")
        if pd.notna(ts_dt):
            ts_it = ts_dt.tz_localize("UTC").tz_convert(TZ_ITALIA).tz_localize(None)
            nuovi_log.append({
                "Timestamp": ts_it,
                "Player": pl_s.strip(),
                "Mob": mob_s.strip().title(),
                "PED": int(ped_s)
            })
    return pd.DataFrame(nuovi_log) if nuovi_log else pd.DataFrame(columns=["Timestamp", "Player", "Mob", "PED"])

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Sync from chat.log (Intraday)")
uploaded_chat_log = st.sidebar.file_uploader("Upload Entropia chat.log:", type=["log", "txt"])

if uploaded_chat_log is not None:
if uploaded_chat_log is not None:
    df_log = analizza_chat_log_cache(uploaded_chat_log.getvalue())
    if len(df_log) > 0:
        if "ultimo_log_unito" not in st.session_state or st.session_state.ultimo_log_unito != uploaded_chat_log.name:
            df_globale = pd.concat([df_globale, df_log], ignore_index=True)
            df_globale = df_globale.drop_duplicates(subset=["Timestamp", "Player", "Mob", "PED"]).sort_values("Timestamp")
            df_globale.to_csv(PATH_DATABASE_CSV, index=False)
            st.session_state.ultimo_log_unito = uploaded_chat_log.name
        st.sidebar.success(f"✅ {len(df_log)} Globals synced from chat.log!")
    else:
        st.sidebar.warning("⚠️ No hunting globals found in chat.log.")

st.sidebar.markdown("---")


# ==============================================================================
# >>>>>> BLOCK >>> D <<< (CHAT.LOG UPLOADER, INTRADAY SYNC & CSV EXPORT)
# ==============================================================================

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Sync from chat.log (Intraday)")
uploaded_chat_log = st.sidebar.file_uploader("Upload Entropia chat.log:", type=["log", "txt"])

if uploaded_chat_log is not None:
    try:
        raw_bytes = uploaded_chat_log.getvalue()
        try:
            testo_log = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            testo_log = raw_bytes.decode("latin-1", errors="ignore")

        pattern_chat = re.compile(
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[Globals\]\s+\[\]\s+(.+?)\s+killed a creature\s+\((.+?)\)\s+with a value of\s+(\d+)\s+PED",
            re.IGNORECASE
        )
        trovati_log = pattern_chat.findall(testo_log)

        if trovati_log:
            nuovi_log = []
            for ts_s, pl_s, mob_s, ped_s in trovati_log:
                ts_dt = pd.to_datetime(ts_s, errors="coerce")
                if pd.notna(ts_dt):
                    ts_it = ts_dt.tz_localize("UTC").tz_convert(TZ_ITALIA).tz_localize(None)
                    nuovi_log.append({
                        "Timestamp": ts_it,
                        "Player": pl_s.strip(),
                        "Mob": mob_s.strip().title(),
                        "PED": int(ped_s)
                    })

            if nuovi_log:
                df_log = pd.DataFrame(nuovi_log)
                df_globale = pd.concat([df_globale, df_log], ignore_index=True)
                df_globale = df_globale.drop_duplicates(subset=["Timestamp", "Player", "Mob", "PED"]).sort_values("Timestamp")
                df_globale.to_csv(PATH_DATABASE_CSV, index=False)
                st.sidebar.success(f"✅ Loaded {len(df_log)} Globals from chat.log!")
        else:
            st.sidebar.warning("⚠️ No hunting globals found in chat.log.")
    except Exception as e:
        st.sidebar.error(f"Error reading chat.log: {e}")

if len(df_globale) > 0:
    csv_download = df_globale.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label="💾 Download Updated CSV",
        data=csv_download,
        file_name="storico_semaforo_pulito.csv",
        mime="text/csv"
    )

st.sidebar.markdown("---")


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

ora_attuale = ora_italia_now()
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
st.markdown("""
<div style="background-color: #161b22; border: 1px solid #30363d; border-left: 4px solid #00e676; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; color: #e6edf3;">
    <div style="margin-bottom: 6px;">
        📩 <b>Want to suggest new mobs, planets, or features?</b> Contact me via <b>In-Game Mail / PM</b>: <span style="color: #00e676; font-weight: bold;">vanessa bil any</span>
    </div>
    <div style="font-size: 12.5px; color: #9da7b3;">
        🙏 <b>Special Thanks:</b> Built for <a href="https://entropiauniverse.com" target="_blank" style="color: #58a6ff; text-decoration: none;">Entropia Universe (MindArk)</a>, powered by <a href="https://entropianexus.com" target="_blank" style="color: #58a6ff; text-decoration: none;">Entropia Nexus</a> live data & hosted on <a href="https://github.com" target="_blank" style="color: #58a6ff; text-decoration: none;">GitHub</a>. Huge thanks to <b>Fabio (Ephestus)</b> for the dedicated hunting & field testing!
    </div>
</div>
""", unsafe_allow_html=True)



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
# >>>>>> BLOCK >>> H <<< (SECTION 2: WEEKLY TREND, BEST HOURS & PLAYER TABLE)
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

# --- SECTION 3: BEST HUNTING TIME WINDOW (HISTORICAL PEAK HOURS) ---
st.markdown("---")
st.subheader(f"🕒 3. Best Hunting Time Windows for {mob_selezionato} ({grado_mob})")

if len(df_mob) >= 3:
    df_mob_ore = df_mob.copy()
    df_mob_ore['Ora_Storica'] = pd.to_datetime(df_mob_ore['Timestamp'], errors='coerce').dt.hour
    stats_orarie = df_mob_ore.groupby('Ora_Storica').agg(
        Conteggio=('PED', 'count'),
        Totale_PED=('PED', 'sum'),
        Media_PED=('PED', 'mean')
    ).reindex(range(24), fill_value=0).reset_index()

    top_3_ore = stats_orarie.sort_values(['Conteggio', 'Totale_PED'], ascending=[False, False]).head(3)
    ora_migliore = int(top_3_ore.iloc[0]['Ora_Storica'])
    ora_fine_migliore = (ora_migliore + 2) % 24
    glob_ora_migliore = int(top_3_ore.iloc[0]['Conteggio'])
    media_ora_migliore = float(top_3_ore.iloc[0]['Media_PED'])

    # Calcolo finestra mobile di 2 ore consecutiva con piu Global
    miglior_blocco_inizio = 0
    max_glob_blocco = -1
    for h in range(24):
        h_next = (h + 1) % 24
        somma_2h = int(stats_orarie.loc[h, 'Conteggio'] + stats_orarie.loc[h_next, 'Conteggio'])
        if somma_2h > max_glob_blocco:
            max_glob_blocco = somma_2h
            miglior_blocco_inizio = h
    miglior_blocco_fine = (miglior_blocco_inizio + 2) % 24

    b1, b2, b3 = st.columns(3)
    with b1:
        st.success(
            f"🏆 **Prime Hunting Window (2h):**\n\n"
            f"**{miglior_blocco_inizio:02d}:00 — {miglior_blocco_fine:02d}:00** (IT Time)\n\n"
            f"Peak concentration: **{max_glob_blocco} Globals** recorded in this 2-hour slot."
        )
    with b2:
        st.info(
            f"⏰ **Single Peak Hour:**\n\n"
            f"**{ora_migliore:02d}:00 — {(ora_migliore + 1) % 24:02d}:00**\n\n"
            f"**{glob_ora_migliore} Globals** (Avg payout: **{media_ora_migliore:.0f} PED**)"
        )
    with b3:
        elenco_top3 = " | ".join([f"**{int(r['Ora_Storica']):02d}:00** ({int(r['Conteggio'])}x)" for _, r in top_3_ore.iterrows() if r['Conteggio'] > 0])
        st.warning(
            f"🎯 **Top 3 Active Hours & Zone:**\n\n"
            f"{elenco_top3}\n\n"
            f"Area: **{coord_mob}**"
        )

    fig_ore_storico = go.Figure()
    fig_ore_storico.add_trace(go.Bar(
        x=[f"{h:02d}:00" for h in stats_orarie['Ora_Storica']],
        y=stats_orarie['Conteggio'],
        name='Historical Globals (#)',
        marker_color='#ffea00',
        text=stats_orarie['Conteggio'].apply(lambda v: f"{v}" if v > 0 else ""),
        textposition='auto'
    ))
    fig_ore_storico.add_vline(x=ora_attuale.hour, line_dash="dash", line_color="#00e676", annotation_text="Now")
    fig_ore_storico.update_layout(
        title=f"All-Time Hourly Distribution for {mob_selezionato} (Best Time to Hunt)",
        xaxis=dict(title="Hour of Day (Italian Time 00:00 - 23:00)", showgrid=False),
        yaxis=dict(title="Historical Globals Count", showgrid=True, gridcolor="#333", dtick=1),
        margin=dict(l=20, r=20, t=45, b=20),
        height=290
    )
    st.plotly_chart(fig_ore_storico, use_container_width=True)
else:
    st.info(f"Not enough historical data yet for {mob_selezionato} to calculate peak hunting hours.")

with st.expander("📋 View last 10 Globals/HoFs recorded for this mob"):
    if len(df_mob) > 0:
        ultimi_10 = df_mob.sort_values('Timestamp', ascending=False).head(10).copy()
        ultimi_10['Timestamp'] = ultimi_10['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        cols_visibili = [c for c in ['Timestamp', 'Player', 'Mob', 'PED'] if c in ultimi_10.columns]
        st.dataframe(ultimi_10[cols_visibili], use_container_width=True, hide_index=True)
    else:
        st.info("No Globals found yet for this mob.")

# Timer leggero lato browser (nessun blocco server e zero effetto ghost)
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

col_r1, col_r2 = st.sidebar.columns(2)
st.session_state.auto_refresh = col_r1.checkbox("🔄 Auto-Refresh", value=st.session_state.auto_refresh)
if col_r2.button("⚡ Refresh Now"):
    st.rerun()

if st.session_state.auto_refresh:
    components.html(
        """
        <script>
        setTimeout(function() {
            window.parent.document.querySelectorAll('button').forEach(btn => {
                if (btn.innerText.includes('Refresh Now')) {
                    btn.click();
                }
            });
        }, 90000);
        </script>
        """,
        height=0,
        width=0
    )




import streamlit as st
from supabase import create_client, Client
import datetime
from datetime import date
# --- CONNESSIONE AL DATABASE ---
# Sostituisci questi valori con i tuoi dati di Supabase!
SUPABASE_URL = "https://jblladmggeuokluiopou.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpibGxhZG1nZ2V1b2tsdWlvcG91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE2OTI2OTIsImV4cCI6MjA5NzI2ODY5Mn0.GvrR_Lnl7QeDGN5Q-xkV2ez4t3xOrXNw9A4mgv3B28Y"

# --- 🎯 IMPOSTA I TUOI OBIETTIVI GIORNALIERI QUI ---
TARGET_KCAL = 1600
TARGET_CARBI = 170
TARGET_PRO = 110
TARGET_GRASSI = 50

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- FUNZIONI DI RECUPERO E SALVATAGGIO DATI ---
def ottieni_ingredienti():
    res = supabase.table("ingredienti").select("*").order("nome").execute()
    return res.data

def ottieni_piatti():
    res = supabase.table("piatti").select("*").order("nome_piatto").execute()
    return res.data

def ottieni_componenti_piatto(id_piatto):
    res = supabase.table("composizione_piatti").select("grammi, ingredienti(calorie_100g, carboidrati_100g, proteine_100g, grassi_100g, nome)").eq("id_piatto", id_piatto).execute()
    return res.data

def ottieni_diario_oggi():
    # Recupera solo i cibi mangiati nella data odierna
    oggi = date.today().isoformat()
    res = supabase.table("diario_oggi").select("*").eq("data_giorno", oggi).execute()
    return res.data

def aggiungi_al_diario(nome, kcal, carbi, pro, fat):
    data = {
        "data_giorno": date.today().isoformat(),
        "nome_cibo": nome,
        "calorie": kcal,
        "carboidrati": carbi,
        "proteine": pro,
        "grassi": fat
    }
    supabase.table("diario_oggi").insert(data).execute()

def svuota_diario_oggi():
    oggi = date.today().isoformat()
    supabase.table("diario_oggi").delete().eq("data_giorno", oggi).execute()

# --- FUNZIONE AUSILIARIA PER GENERARE I CONTATORI COLORATI ---
def genera_card_macro(titolo, attuale, target, unita="g"):
    percentuale = (attuale / target) * 100 if target > 0 else 0
    
    if percentuale > 100:
        colore = "#FF4B4B"  # Rosso
    elif percentuale > 80:
        colore = "#FFA500"  # Arancione
    else:
        colore = "#00E676"  # Verde
        
    html_code = f"""
    <div style="
        background-color: #262730; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid {colore};
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    ">
        <p style="margin: 0; font-size: 14px; color: #FFFFFF; font-weight: bold; opacity: 0.9;">{titolo}</p>
        <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold; color: #FFFFFF;">
            <span style="color: {colore}; font-size: 22px;">{attuale:.1f}</span> <span style="color: #DDDDDD;">/ {target}{unita}</span>
        </p>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: {colore}; font-weight: bold;">{percentuale:.1f}% del target</p>
    </div>
    """
    return st.markdown(html_code, unsafe_allow_html=True)

# --- INTERFACCIA GRAFICA (DIARIO) ---
st.title("🥑 Il mio Diario dei Macronutrienti")

col1, col2 = st.columns(2)

# Recupera subito i dati aggiornati dal database
diario_salvato = ottieni_diario_oggi()
lista_ingredienti = ottieni_ingredienti()
nomi_ingr = [i["nome"] for i in lista_ingredienti]

with col1:
    st.subheader("➕ Aggiungi nel Piatto")
    if nomi_ingr:
        ingr_scelto = st.selectbox("Seleziona Ingrediente", nomi_ingr, key="ingr")
        grammi = st.number_input("Grammi", min_value=1, value=100, step=10)
        
        if st.button("Aggiungi Ingrediente"):
            dettagli = next(item for item in lista_ingredienti if item["nome"] == ingr_scelto)
            kcal = (dettagli.get("calorie_100g", 0) * grammi) / 100
            carbi = (dettagli["carboidrati_100g"] * grammi) / 100
            pro = (dettagli["proteine_100g"] * grammi) / 100
            fat = (dettagli["grassi_100g"] * grammi) / 100
            
            aggiungi_al_diario(f"{ingr_scelto} ({grammi}g)", kcal, carbi, pro, fat)
            st.success(f"Aggiunto: {ingr_scelto}!")
            st.rerun()
    else:
        st.warning("Nessun ingrediente presente. Crealo nel pannello sotto!")

with col2:
    st.subheader("🥞 Aggiungi un Piatto")
    lista_piatti = ottieni_piatti()
    nomi_piatti = [p["nome_piatto"] for p in lista_piatti]
    
    if nomi_piatti:
        piatto_scelto = st.selectbox("Seleziona Piatto", nomi_piatti, key="piatto")
        
        if st.button("Aggiungi Piatto alla Giornata"):
            dettagli_piatto = next(item for item in lista_piatti if item["nome_piatto"] == piatto_scelto)
            componenti = ottieni_componenti_piatto(dettagli_piatto["id"])
            
            tot_kcal, tot_carbi, tot_pro, tot_fat = 0, 0, 0, 0
            for comp in componenti:
                g = comp["grammi"]
                ing = comp["ingredienti"]
                tot_kcal += (ing.get("calorie_100g", 0) * g) / 100
                tot_carbi += (ing["carboidrati_100g"] * g) / 100
                tot_pro += (ing["proteine_100g"] * g) / 100
                tot_fat += (ing["grassi_100g"] * g) / 100
                
            aggiungi_al_diario(piatto_scelto, tot_kcal, tot_carbi, tot_pro, tot_fat)
            st.success(f"Aggiunto: {piatto_scelto}!")
            st.rerun()
    else:
        st.info("Nessun piatto salvato.")

# --- TOTALE DELLA GIORNATA ---
st.header("📊 Riassunto Oggi")

tot_kcal = sum(item["calorie"] for item in diario_salvato) if diario_salvato else 0.0
tot_c = sum(item["carboidrati"] for item in diario_salvato) if diario_salvato else 0.0
tot_p = sum(item["proteine"] for item in diario_salvato) if diario_salvato else 0.0
tot_f = sum(item["grassi"] for item in diario_salvato) if diario_salvato else 0.0

c1, c2, c3, c4 = st.columns(4)
with c1:
    genera_card_macro("⚡ Calorie", tot_kcal, TARGET_KCAL, "kcal")
with c2:
    genera_card_macro("🍞 Carboidrati", tot_c, TARGET_CARBI)
with c3:
    genera_card_macro("🍗 Proteine", tot_p, TARGET_PRO)
with c4:
    genera_card_macro("🥑 Grassi", tot_f, TARGET_GRASSI)

if diario_salvato:
    st.write("### Cibi inseriti oggi:")
    for item in diario_salvato:
        st.text(f"• {item['nome_cibo']} ➡️ {int(item['calorie'])} kcal | C: {item['carboidrati']:.1f}g | P: {item['proteine']:.1f}g | G: {item['grassi']:.1f}g")
        
    if st.button("Svuota Giornata"):
        svuota_diario_oggi()
        st.rerun()
else:
    st.info("Non hai ancora mangiato nulla oggi.")

st.markdown("---")

# --- PANNELLO DI GESTIONE DATABASE ---
st.header("⚙️ Pannello di Controllo (Inserimento cibi)")

expander_ing = st.expander("📝 Crea Nuovo Ingrediente Base")
with expander_ing:
    nuovo_nome = st.text_input("Nome Alimento (es. Riso Basmati)")
    kcal_100 = st.number_input("Calorie (kcal) per 100g", min_value=0, step=1)
    c_100 = st.number_input("Carboidrati per 100g", min_value=0.0, step=0.1)
    p_100 = st.number_input("Proteine per 100g", min_value=0.0, step=0.1)
    f_100 = st.number_input("Grassi per 100g", min_value=0.0, step=0.1)
    
    if st.button("Salva Ingrediente nel Database"):
        if nuovo_nome:
            data = {
                "nome": nuovo_nome, 
                "calorie_100g": kcal_100,
                "carboidrati_100g": c_100, 
                "proteine_100g": p_100, 
                "grassi_100g": f_100
            }
            supabase.table("ingredienti").insert(data).execute()
            st.success(f"'{nuovo_nome}' salvato con successo! Ricarica la pagina.")
            st.rerun()
        else:
            st.error("Inserisci un nome valido!")

expander_piatto = st.expander("🍳 Componi e Salva un Nuovo Piatto")
with expander_piatto:
    nome_nuovo_piatto = st.text_input("Nome del Piatto (es. Spaghettata, Cena Fit)")
    
    st.write("Seleziona gli ingredienti che compongono questo piatto (Puoi aggiungerne uno alla volta):")
    if "ingredienti_nuovo_piatto" not in st.session_state:
        st.session_state.ingredienti_nuovo_piatto = []
        
    ing_piatto = st.selectbox("Seleziona Ingrediente da inserire nel piatto", nomi_ingr, key="ing_p")
    gr_piatto = st.number_input("Grammi nel piatto", min_value=1, value=100, step=5, key="gr_p")
    
    if st.button("Inserisci questo ingrediente nel piatto"):
        ing_dettagli = next(item for item in lista_ingredienti if item["nome"] == ing_piatto)
        st.session_state.ingredienti_nuovo_piatto.append({"id": ing_dettagli["id"], "nome": ing_piatto, "grammi": gr_piatto})

    if st.session_state.ingredienti_nuovo_piatto:
        st.write("**Ingredienti attualmente inseriti nel piatto:**")
        for ing in st.session_state.ingredienti_nuovo_piatto:
            st.text(f"- {ing['nome']}: {ing['grammi']}g")
            
        if st.button("SALVA PIATTO DEFINITIVAMENTE"):
            if nome_nuovo_piatto:
                res_piatto = supabase.table("piatti").insert({"nome_piatto": nome_nuovo_piatto}).execute()
                id_nuovo_piatto = res_piatto.data[0]["id"]
                
                for ing in st.session_state.ingredienti_nuovo_piatto:
                    supabase.table("composizione_piatti").insert({
                        "id_piatto": id_nuovo_piatto,
                        "id_ingrediente": ing["id"],
                        "grammi": ing["grammi"]
                    }).execute()
                    
                st.session_state.ingredienti_nuovo_piatto = []
                st.success(f"Piatto '{nome_nuovo_piatto}' salvato nel database!")
                st.rerun()
            else:
                st.error("Dai un nome al piatto prima di salvare!")

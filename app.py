import streamlit as st
from supabase import create_client, Client

# --- CONNESSIONE AL DATABASE ---
# Sostituisci questi valori con i tuoi dati di Supabase!
SUPABASE_URL = "https://jblladmggeuokluiopou.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpibGxhZG1nZ2V1b2tsdWlvcG91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE2OTI2OTIsImV4cCI6MjA5NzI2ODY5Mn0.GvrR_Lnl7QeDGN5Q-xkV2ez4t3xOrXNw9A4mgv3B28Y"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- INIZIALIZZAZIONE DELLA GIORNATA (STATO DELL'APP) ---
if "diario_alimentare" not in st.session_state:
    st.session_state.diario_alimentare = []  # Lista dei macro dei cibi mangiati oggi

# --- FUNZIONI DI RECUPERO DATI ---
def ottieni_ingredienti():
    res = supabase.table("ingredienti").select("*").execute()
    return res.data

def ottieni_piatti():
    res = supabase.table("piatti").select("*").execute()
    return res.data

def ottieni_componenti_piatto(id_piatto):
    res = supabase.table("composizione_piatti").select("grammi, ingredienti(carboidrati_100g, proteine_100g, grassi_100g, nome)").eq("id_piatto", id_piatto).execute()
    return res.data

# --- INTERFACCIA GRAFICA (STREAMLIT) ---
st.title("🥑 Il mio Diario dei Macronutrienti")

col1, col2 = st.columns(2)

with col1:
    st.subheader("➕ Aggiungi Ingrediente Singolo")
    lista_ingredienti = ottieni_ingredienti()
    nomi_ingr = [i["nome"] for i in lista_ingredienti]
    
    ingr_scelto = st.selectbox("Seleziona Ingrediente", nomi_ingr, key="ingr")
    grammi = st.number_input("Grammi", min_value=1, value=100, step=10)
    
    if st.button("Aggiungi Ingrediente"):
        # Trova i dettagli dell'ingrediente selezionato
        dettagli = next(item for item in lista_ingredienti if item["nome"] == ingr_scelto)
        # Calcolo proporzione sui grammi inseriti
        carbi = (dettagli["carboidrati_100g"] * grammi) / 100
        pro = (dettagli["proteine_100g"] * grammi) / 100
        fat = (dettagli["grassi_100g"] * grammi) / 100
        
        st.session_state.diario_alimentare.append({
            "nome": f"{ingr_scelto} ({grammi}g)", "carbi": carbi, "pro": pro, "fat": fat
        })
        st.success(f"Aggiunto: {ingr_scelto}!")

with col2:
    st.subheader("🥞 Aggiungi un Piatto Salvato")
    lista_piatti = ottieni_piatti()
    nomi_piatti = [p["nome_piatto"] for p in lista_piatti]
    
    piatto_scelto = st.selectbox("Seleziona Piatto", nomi_piatti, key="piatto")
    
    if st.button("Aggiungi Piatto alla Giornata"):
        dettagli_piatto = next(item for item in lista_piatti if item["nome_piatto"] == piatto_scelto)
        componenti = ottieni_componenti_piatto(dettagli_piatto["id"])
        
        # Somma i macro di tutti gli ingredienti dentro il piatto
        tot_carbi, tot_pro, tot_fat = 0, 0, 0
        for comp in componenti:
            g = comp["grammi"]
            ing = comp["ingredienti"]
            tot_carbi += (ing["carboidrati_100g"] * g) / 100
            tot_pro += (ing["proteine_100g"] * g) / 100
            tot_fat += (ing["grassi_100g"] * g) / 100
            
        st.session_state.diario_alimentare.append({
            "nome": piatto_scelto, "carbi": tot_carbi, "pro": tot_pro, "fat": tot_fat
        })
        st.success(f"Aggiunto: {piatto_scelto}!")


# --- TOTALE DELLA GIORNATA ---
st.header("📊 Riassunto Oggi")

if st.session_state.diario_alimentare:
    # Calcolo dei totali generali
    tot_c = sum(item["carbi"] for item in st.session_state.diario_alimentare)
    tot_p = sum(item["pro"] for item in st.session_state.diario_alimentare)
    tot_f = sum(item["fat"] for item in st.session_state.diario_alimentare)
    # Formula standard per le calorie: Carbi*4 + Pro*4 + Fat*9
    tot_kcal = (tot_c * 4) + (tot_p * 4) + (tot_f * 9)
    
    # Mostra i contatori grafici
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⚡ Calorie", f"{int(tot_kcal)} kcal")
    c2.metric("🍞 Carboidrati", f"{tot_c:.1f} g")
    c3.metric("🍗 Proteine", f"{tot_p:.1f} g")
    c4.metric("🥑 Grassi", f"{tot_f:.1f} g")
    
    # Mostra la lista delle cose mangiate
    st.write("### Cibi inseriti oggi:")
    for item in st.session_state.diario_alimentare:
        st.text(f"• {item['nome']} ➡️ C: {item['carbi']:.1f}g | P: {item['pro']:.1f}g | G: {item['fat']:.1f}g")
        
    if st.button("Svuota Giornata"):
        st.session_state.diario_alimentare = []
        st.rerun()
else:
    st.info("Non hai ancora mangiato nulla oggi. Aggiungi un ingrediente o un piatto sopra!")

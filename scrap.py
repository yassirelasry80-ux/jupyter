import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

# Liste des raisons sociales extraites de ProdCRM
data = [
    "G.C TRA", "AGRI GOOD", "RAMSIK TRAVAUX", "ANTEUS AGRI", "EARLY CITRUS"
]

raisons_sociales = pd.DataFrame({'nom': data})

# URL CIBLE
TARGET_URL = "https://ice.marocfacture.com/" 

def init_driver():
    """Initialise le driver une seule fois."""
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Commenter pour voir le navigateur
    # Options pour éviter d'être détecté comme un bot (aide à ne pas être bloqué)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def collecter_infos_ice(driver, nom_entreprise):
    """
    Collecte les infos pour une entreprise donnée en utilisant le driver existant.
    Retourne un dictionnaire de données.
    """
    donnees = {
        "nom_recherche": nom_entreprise,
        "Activite_Status": "N/A",
        "Nom_Trouve": "N/A",
        "ICE": "Non trouvé",
        "Forme_Juridique": "N/A",
        "RC": "N/A",
        "Capital": "N/A",
        "Date_Creation": "N/A",
        "Activite": "N/A"
    }
    
    try:
        print(f"--- Traitement de : {nom_entreprise} ---")
        
        # On retourne à la page d'accueil ou on reste sur la page si c'est la même structure
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10) # 10s suffisent généralement si le site est rapide

        # 1. Saisie du nom
        try:
            search_input = wait.until(EC.element_to_be_clickable((By.ID, "valrs")))
            search_input.clear()
            search_input.send_keys(nom_entreprise)
            # Pas besoin de sleep ici si on tape juste
            
            # Validation par ENTREE (plus rapide que de chercher le bouton)
            search_input.send_keys(Keys.RETURN)
            
        except Exception as e:
            print(f"  ERREUR RECHERCHE: {e}")
            return donnees
        
        # 3. Attendre les résultats
        try:
            # On attend que le conteneur apparaisse
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".conta")))
            
            premier_resultat = driver.find_element(By.CSS_SELECTOR, ".conta")
            
            # 5. Extraction (optimisée pour la vitesse, on enchaine les try/except)
            
            # Status
            try: donnees["Activite_Status"] = premier_resultat.find_element(By.CSS_SELECTOR, ".note.activite").text
            except: pass

            # Nom 
            try: donnees["Nom_Trouve"] = premier_resultat.find_element(By.CSS_SELECTOR, ".par1").text.strip()
            except: pass
                
            # ICE 
            try: donnees["ICE"] = premier_resultat.find_element(By.CSS_SELECTOR, "input.inj").get_attribute("value")
            except: pass

            # Bloc .cnv
            try:
                cnv_div = premier_resultat.find_element(By.CSS_SELECTOR, ".cnv")
                try: donnees["Forme_Juridique"] = cnv_div.find_element(By.CSS_SELECTOR, ".par3").text
                except: pass
                
                par4_elements = cnv_div.find_elements(By.CSS_SELECTOR, ".par4")
                for p in par4_elements:
                    text = p.text
                    if "RC" in text: donnees["RC"] = text.replace("RC", "").strip()
                    elif "Capital" in text: donnees["Capital"] = text.replace("Capital :", "").strip()
                    elif "Création" in text: donnees["Date_Creation"] = text.replace("Création :", "").strip()
            except: pass
            
            # Activité (logique split robuste)
            try:
                activite_text = premier_resultat.find_element(By.CSS_SELECTOR, ".par5").text
                if ":" in activite_text:
                    donnees["Activite"] = activite_text.split(":")[-1].strip()
                else:
                    donnees["Activite"] = activite_text.strip()
            except: pass
            
        except Exception as e:
            print(f"  PAS DE RÉSULTATS (ou timeout)")
            # Optionnel: Sauvegarde page si erreur critique, mais on veut de la vitesse
            # with open(f"error_{nom_entreprise}.html", "w", encoding="utf-8") as f: f.write(driver.page_source)

    except Exception as e:
        print(f"  ERREUR GLOBALE: {e}")
        
    return donnees

# --- MAIN ---

driver = init_driver()
resultats_finaux = []

try:
    for entreprise in raisons_sociales['nom']:
        infos = collecter_infos_ice(driver, entreprise)
        resultats_finaux.append(infos)
        
        if infos["ICE"] != "Non trouvé":
            print(f"  -> OK: {infos['ICE']}, Activité: {infos['Activite']}")
        else:
            print("  -> Non trouvé")
            
        # Pause courte pour ne pas être bloqué ("IP block") mais rester rapide
        # 1 à 2 secondes est un bon compromis. Si blockage, augmenter.
        time.sleep(1.5) 

finally:
    # On ferme le navigateur à la TOUTE FIN seulement
    driver.quit()
    print("Navigateur fermé.")

# Création CSV
df_reference = pd.DataFrame(resultats_finaux)
df_reference.to_csv('table_reference_ice_new.csv', index=False)
print("\n--- TERMINE ! Fichier table_reference_ice_new.csv créé ---")
print(df_reference.head())
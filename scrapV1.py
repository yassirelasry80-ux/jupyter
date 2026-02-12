import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

# Liste des raisons sociales extraites de ProdCRM (version courte fournie par l'utilisateur)
data = [
    "G.C TRA", "AGRI GOOD", "RAMSIK TRAVAUX", "ANTEUS AGRI", "EARLY CITRUS"
]

raisons_sociales = pd.DataFrame({'nom': data})

# URL CIBLE - À REMPLACER PAR L'URL CORRECTE
TARGET_URL = "https://ice.marocfacture.com/" 

def collecter_infos_ice(nom_entreprise):
    chrome_options = Options()
    # chrome_options.add_argument("--headless") 
    driver = webdriver.Chrome(options=chrome_options)
    
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
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 20) # Temps d'attente augmenté

        # 1. Saisie du nom dans le champ id="valrs"
        try:
            print("  Recherche du champ de saisie...")
            search_input = wait.until(EC.presence_of_element_located((By.ID, "valrs")))
            search_input.clear()
            search_input.send_keys(nom_entreprise)
            time.sleep(1) 
            
            # Utilisation de ENTREE au lieu du clic (souvent plus fiable)
            print("  Envoi de la requête (ENTREE)...")
            search_input.send_keys(Keys.RETURN)
            
        except Exception as e:
            print(f"  ERREUR RECHERCHE pour {nom_entreprise}: {e}")
            # Sauvegarder la page pour comprendre pourquoi le champ n'est pas trouvé
            with open("debug_page_search_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return donnees
        
        # 3. Attendre que le conteneur de résultats apparaisse
        try:
            print("  Attente des résultats...")
            # On cherche le conteneur .conta
            # On attend un peu que le JS s'exécute
            time.sleep(3)
            
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".conta")))
            print("  Conteneur .conta trouvé!")
            
            premier_resultat = driver.find_element(By.CSS_SELECTOR, ".conta")
            
            # 5. Extraction des données
            
            # Status en activité
            try:
                donnees["Activite_Status"] = premier_resultat.find_element(By.CSS_SELECTOR, ".note.activite").text
            except: pass

            # Nom 
            try:
                par1 = premier_resultat.find_element(By.CSS_SELECTOR, ".par1")
                donnees["Nom_Trouve"] = par1.text.strip()
            except: pass
                
            # ICE 
            try:
                ice_input = premier_resultat.find_element(By.CSS_SELECTOR, "input.inj")
                donnees["ICE"] = ice_input.get_attribute("value")
            except: pass

            # Bloc .cnv
            try:
                cnv_div = premier_resultat.find_element(By.CSS_SELECTOR, ".cnv")
                
                try:
                    donnees["Forme_Juridique"] = cnv_div.find_element(By.CSS_SELECTOR, ".par3").text
                except: pass
                
                par4_elements = cnv_div.find_elements(By.CSS_SELECTOR, ".par4")
                for p in par4_elements:
                    text = p.text
                    if "RC" in text:
                        donnees["RC"] = text.replace("RC", "").strip()
                    elif "Capital" in text:
                        donnees["Capital"] = text.replace("Capital :", "").strip()
                    elif "Création" in text:
                         donnees["Date_Creation"] = text.replace("Création :", "").strip()
            except: pass
            
            # Activité
            try:
                activite_elem = premier_resultat.find_element(By.CSS_SELECTOR, ".par5")
                activite_text = activite_elem.text
                print(f"  Texte Activité brut: '{activite_text}'")
                if ":" in activite_text:
                    donnees["Activite"] = activite_text.split(":")[-1].strip()
                else:
                    donnees["Activite"] = activite_text.strip()
            except Exception as e:
                print(f"  Erreur extraction Activité: {e}")
            
        except Exception as e:
            print(f"  PAS DE RÉSULTATS ou TIMEOUT pour {nom_entreprise}")
            # Sauvegarder la page pour débogage
            filename = f"debug_page_{nom_entreprise.replace(' ', '_')}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"  SOURCE PAGE SAUVEGARDÉE DANS : {filename}")

    except Exception as e:
        print(f"  ERREUR GLOBALE pour {nom_entreprise}: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        
    return donnees

# 2. Boucle d'extraction
resultats_finaux = []
for entreprise in raisons_sociales['nom']:
    infos = collecter_infos_ice(entreprise)
    resultats_finaux.append(infos)
    print(f"  -> ICE trouvé : {infos['ICE']}")
    time.sleep(2) 

# 3. Création de la table de référence
df_reference = pd.DataFrame(resultats_finaux)

# Export
df_reference.to_csv('table_reference_ice_new.csv', index=False)
print("\n--- RÉSULTATS FINAUX ---")
print(df_reference)
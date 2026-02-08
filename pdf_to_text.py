import os
from pypdf import PdfReader

INPUT_DIRECTORY = "input"

def convert():
    """
    Funzione principale per la conversione da PDF a testo.
    Legge tutti i file .pdf nella cartella 'input' e li converte in .txt
    nella stessa cartella.
    """
    print("Inizio conversione da PDF a testo...")
    
    if not os.path.exists(INPUT_DIRECTORY):
        print(f"La cartella '{INPUT_DIRECTORY}' non esiste. Creazione in corso...")
        os.makedirs(INPUT_DIRECTORY)
        print("Cartella creata. Inserisci i file PDF e riprova.")
        return

    files = [f for f in os.listdir(INPUT_DIRECTORY) if f.lower().endswith('.pdf')]
    
    if not files:
        print(f"Nessun file PDF trovato nella cartella '{INPUT_DIRECTORY}'.")
        return

    for filename in files:
        pdf_path = os.path.join(INPUT_DIRECTORY, filename)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(INPUT_DIRECTORY, txt_filename)
        
        print(f"Convertendo '{filename}' in '{txt_filename}'...")
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            print(f"Conversione completata: {txt_path}")
        except Exception as e:
            print(f"Errore durante la conversione di '{filename}': {e}")

    print("Processo di conversione terminato.")

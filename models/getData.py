import time
import pandas as pd
import feedparser

# Charger les données existantes depuis le fichier CSV
data = pd.read_csv("datafake_train.csv", header=0, delimiter=";")

# Définir l'URL du fichier RSS cible
rss_url = "https://www.seneweb.com/feed"

while True:
    # Récupérer les données du fichier RSS
    feed = feedparser.parse(rss_url)

    # Parcourir les entrées (articles) du fichier RSS
    for entry in feed.entries:
        # Extraire les informations pertinentes de chaque entrée
        # par exemple, le titre de l'article comme auteur et la description comme contenu
        media = entry.title
        post = entry.description

        # Prétraiter le contenu si nécessaire
        preprocessed_content = preprocess_text(post)

        # Ajouter les informations extraites à votre dataframe existant
        data = data._append({"media": media, "post": preprocessed_content, "fake": 1}, ignore_index=True)

    # Enregistrer le dataframe mis à jour dans un fichier CSV avec des points-virgules comme séparateurs
    data.to_csv("datafake_train_updated.csv", sep=";", index=False)

    # Pause de 5 minutes avant la prochaine exécution
    time.sleep(300)  # 300 secondes = 5 minutes

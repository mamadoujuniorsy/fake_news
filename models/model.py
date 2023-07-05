import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from models.getData import update_data_from_rss

# Téléchargement des ressources nécessaires de NLTK
nltk.download('stopwords')
# Fonction de prétraitement du texte
def preprocess_text(text):
    # Suppression des caractères spéciaux et des chiffres
    text = re.sub(r'\W+|\d+', ' ', text)

    # Mise en minuscules
    text = text.lower()

    # Tokenisation
    tokens = text.split()

    # Suppression des mots vides (stopwords) français
    stop_words = set(stopwords.words('french'))
    tokens = [word for word in tokens if word not in stop_words]
     # Reconstitution du texte prétraité
    preprocessed_text = ' '.join(tokens)

    return preprocessed_text
 
    # Stemming
    stemmer = SnowballStemmer('french')
    tokens = [stemmer.stem(word) for word in tokens]


csv_file = "datafake_train.csv"
rss_url = "https://www.seneweb.com/feed"

update_data_from_rss(csv_file, rss_url)
# Charger les données d'entraînement depuis le fichier CSV
data = pd.read_csv("datafake_train_updated.csv", header=0, delimiter=";")

# Prétraitement du texte
data['post'] = data['post'].apply(preprocess_text)

# Extraction des caractéristiques avec TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(data["post"])

# Extraction des étiquettes
y = data["fake"]

# Division des données en ensembles d'entraînement et de validation
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraînement du modèle SVM
svm_model = SVC()
svm_model.fit(X_train, y_train)

# Entraînement du modèle de forêt aléatoire
rf_model = RandomForestClassifier()
rf_model.fit(X_train, y_train)

# Validation croisée
svm_val_preds = svm_model.predict(X_val)
svm_val_accuracy = accuracy_score(y_val, svm_val_preds)

rf_val_preds = rf_model.predict(X_val)
rf_val_accuracy = accuracy_score(y_val, rf_val_preds)

def predict_fake_news(article_text, threshold=80):
    # Prétraitement de l'article
    preprocessed_text = preprocess_text(article_text)
    
    # Extraction des caractéristiques avec TF-IDF
    article_features = vectorizer.transform([preprocessed_text])
    
    # Prédiction avec les modèles
    svm_prediction = svm_model.predict(article_features)
    rf_prediction = rf_model.predict(article_features)
    
    # Combinaison des prédictions
    combined_prediction = (svm_prediction + rf_prediction) / 2
    
    # Calcul du pourcentage de chance que l'information soit fausse
    fake_percentage = 100 - (combined_prediction * 100)
    
    # Vérification du seuil
    if fake_percentage >= threshold:
        message = "fake"
    else:
        message = "real"
    
    return message    
# Exemple d'utilisation
#article = ""
#result = predict_fake_news(article)
#print(result)
#print("Validation Accuracy - SVM:", svm_val_accuracy)
#print("Validation Accuracy - Random Forest:", rf_val_accuracy)

# Charger les données de test depuis le fichier CSV
#test_data = pd.read_csv("datafake_test.csv", header=0, delimiter=";")

# Prétraitement du texte pour les données de test
#test_data['post'] = test_data['post'].apply(preprocess_text)

# Prétraitement des données de test
#X_test = vectorizer.transform(test_data["post"])

# Prédiction des étiquettes des données de test
#svm_test_preds = svm_model.predict(X_test)
#rf_test_preds = rf_model.predict(X_test)

# Affichage des prédictions pour SVM
#print("Prédictions SVM :")
#for i, prediction in enumerate(svm_test_preds):
 #   print("Post:", test_data["post"][i])
  #  if prediction == 0:
   #     print("Prédiction: Fausse")
    #else:
     #   print("Prédiction: Vraie")
    #print("---------------------------")

# Affichage des prédictions pour Random Forest
#print("Prédictions Random Forest :")
#for i, prediction in enumerate(rf_test_preds):
 #   print("Post:", test_data["post"][i])
  #  if prediction == 0:
   #     print("Prédiction: Fausse")
    #else:
     #   print("Prédiction: Vraie")
    #print("---------------------------")

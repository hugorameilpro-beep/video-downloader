# 🎬 VidéoClip

Mini-application Streamlit pour récupérer des **vidéos publiques** (YouTube, Facebook, LinkedIn, Vimeo, X…) au format **MP4 H.264 + AAC**, compatible avec PowerPoint sur Windows et Mac.

## 📱 Mockup iPhone

L'onglet **« Mockup iPhone »** incruste une vidéo (récupérée par URL, importée depuis votre ordinateur, ou déjà téléchargée dans le premier onglet) dans l'écran d'un iPhone à encoche :

- Cadre généré avec Pillow (`iphone_mockup.py`) : finitions Argent, Or, Graphite ou Titane bleu, écran 100 % transparent.
- Orientation portrait ou paysage (détection automatique), cadrage « remplir » (rognage) ou « ajuster » (bandes noires).
- Export MP4 H.264 + AAC via ffmpeg, avec une couleur de fond au choix (le MP4 ne gère pas la transparence : prenez la couleur de votre diapositive).
- Bouton d'aperçu instantané et téléchargement du cadre PNG transparent seul.

## 🚀 Déployer gratuitement sur Streamlit Community Cloud

1. **Forkez ou poussez ce dépôt** sur votre compte GitHub.
2. Rendez-vous sur **[share.streamlit.io](https://share.streamlit.io)**, connectez-vous avec GitHub puis cliquez sur **« Create app »**.
3. Sélectionnez le dépôt, la branche et le fichier principal **`app.py`**, puis cliquez sur **« Deploy »**. ✅

Streamlit installe automatiquement `requirements.txt` (Python) et `packages.txt` (`ffmpeg`, nécessaire pour assembler l'image et le son en MP4).

## 💻 Lancer en local

```bash
pip install -r requirements.txt   # + ffmpeg installé sur la machine
streamlit run app.py
```

## ℹ️ Bon à savoir

- Seules les vidéos **publiques** sont prises en charge (pas de contenu privé ou nécessitant une connexion).
- Taille maximale : 500 Mo (modifiable via `MAX_FILESIZE_MB` dans `app.py`).
- Certaines plateformes (notamment YouTube) peuvent bloquer ponctuellement les serveurs cloud ; réessayez plus tard ou lancez l'app en local.
- Respectez les droits d'auteur des vidéos que vous réutilisez.

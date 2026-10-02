# 🎬 VidéoClip

Mini-application Streamlit pour récupérer des **vidéos publiques** (YouTube, Facebook, LinkedIn, Vimeo, X…) au format **MP4 H.264 + AAC**, compatible avec PowerPoint sur Windows et Mac.

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

"""VidéoClip — téléchargez des vidéos publiques en MP4 pour vos présentations PowerPoint."""

import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import yt_dlp

# Taille maximale acceptée (Streamlit Community Cloud dispose d'environ 1 Go de RAM).
MAX_FILESIZE_MB = 500

st.set_page_config(
    page_title="VidéoClip · Vidéos MP4 pour PowerPoint",
    page_icon="🎬",
    layout="centered",
)

# --------------------------------------------------------------------------- #
#  Style Glassmorphism                                                        #
# --------------------------------------------------------------------------- #
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --glass-bg: rgba(255, 255, 255, 0.07);
    --glass-bg-strong: rgba(255, 255, 255, 0.12);
    --glass-border: rgba(255, 255, 255, 0.20);
    --glass-shadow: 0 8px 32px rgba(4, 6, 24, 0.45);
    --text: #eef0ff;
    --text-muted: rgba(238, 240, 255, 0.68);
    --accent-1: #a78bfa;
    --accent-2: #22d3ee;
    --accent-3: #f472b6;
}

html, body, [class*="css"], .stApp, input, button, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ---- Arrière-plan mesh gradient ---- */
.stApp {
    background-color: #0b1020;
    background-image:
        radial-gradient(at 12% 18%, rgba(124, 58, 237, 0.55) 0px, transparent 50%),
        radial-gradient(at 88% 12%, rgba(34, 211, 238, 0.35) 0px, transparent 50%),
        radial-gradient(at 78% 88%, rgba(244, 114, 182, 0.35) 0px, transparent 50%),
        radial-gradient(at 8% 92%, rgba(59, 130, 246, 0.40) 0px, transparent 50%);
    background-attachment: fixed;
    color: var(--text);
}

/* Orbes flottants décoratifs */
.stApp::before, .stApp::after {
    content: "";
    position: fixed;
    border-radius: 50%;
    filter: blur(70px);
    opacity: 0.45;
    z-index: 0;
    pointer-events: none;
    animation: float 18s ease-in-out infinite alternate;
}
.stApp::before {
    width: 340px; height: 340px; top: 8%; left: -80px;
    background: linear-gradient(135deg, var(--accent-1), var(--accent-3));
}
.stApp::after {
    width: 300px; height: 300px; bottom: 6%; right: -60px;
    background: linear-gradient(135deg, var(--accent-2), var(--accent-1));
    animation-delay: -9s;
}
@keyframes float {
    from { transform: translate(0, 0) scale(1); }
    to   { transform: translate(40px, -30px) scale(1.12); }
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }
.block-container {
    position: relative;
    z-index: 1;
    padding-top: 3.5rem;
    max-width: 760px;
}

/* ---- En-tête ---- */
.hero { text-align: center; margin-bottom: 1.8rem; }
.badge {
    display: inline-flex; align-items: center; gap: .45rem;
    padding: .38rem .95rem;
    border-radius: 999px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    font-size: .78rem; font-weight: 500; letter-spacing: .04em;
    color: var(--text-muted);
    box-shadow: 0 4px 16px rgba(0, 0, 0, .2);
}
.badge .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #34d399; box-shadow: 0 0 10px #34d399;
}
.hero h1 {
    font-size: clamp(2.2rem, 6vw, 3.4rem);
    font-weight: 800; line-height: 1.08; letter-spacing: -.03em;
    margin: 1rem 0 .7rem; padding: 0;
    background: linear-gradient(120deg, #ffffff 10%, var(--accent-1) 45%, var(--accent-2) 75%, var(--accent-3));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p {
    color: var(--text-muted);
    font-size: 1.05rem; font-weight: 400; line-height: 1.6;
    max-width: 540px; margin: 0 auto;
}
.platforms {
    display: flex; flex-wrap: wrap; justify-content: center; gap: .5rem;
    margin-top: 1.1rem;
}
.platforms span {
    padding: .25rem .7rem; border-radius: 10px;
    font-size: .76rem; color: var(--text-muted);
    background: rgba(255, 255, 255, .05);
    border: 1px solid rgba(255, 255, 255, .10);
}

/* ---- Cartes en verre dépoli ---- */
[data-testid="stForm"], .glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border) !important;
    border-radius: 24px !important;
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    box-shadow: var(--glass-shadow), inset 0 1px 0 rgba(255, 255, 255, .12);
    padding: 1.6rem 1.6rem 1.2rem !important;
}

/* ---- Champ de saisie ---- */
[data-testid="stTextInput"] label p {
    color: var(--text) !important;
    font-weight: 600; font-size: .92rem;
}
[data-testid="stTextInput"] div[data-baseweb="input"] {
    background: rgba(255, 255, 255, .06) !important;
    border: 1px solid rgba(255, 255, 255, .18) !important;
    border-radius: 14px !important;
    transition: border-color .25s ease, box-shadow .25s ease, background .25s ease;
}
[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border-color: rgba(167, 139, 250, .85) !important;
    background: rgba(255, 255, 255, .09) !important;
    box-shadow: 0 0 0 4px rgba(167, 139, 250, .18);
}
[data-testid="stTextInput"] input {
    color: var(--text) !important;
    background: transparent !important;
    padding: .85rem 1rem !important;
    font-size: .98rem;
}
[data-testid="stTextInput"] input::placeholder { color: rgba(238, 240, 255, .40); }

/* ---- Boutons ---- */
.stButton > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid="stDownloadButton"] > button {
    width: 100%;
    padding: .8rem 1.4rem;
    border-radius: 14px;
    font-weight: 600; font-size: 1rem; letter-spacing: .01em;
    color: #fff !important;
    background: linear-gradient(135deg, rgba(167, 139, 250, .55), rgba(34, 211, 238, .40));
    border: 1px solid rgba(255, 255, 255, .28) !important;
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 6px 22px rgba(124, 58, 237, .30), inset 0 1px 0 rgba(255, 255, 255, .25);
    transition: transform .2s ease, box-shadow .25s ease, background .25s ease;
}
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-2px);
    background: linear-gradient(135deg, rgba(167, 139, 250, .75), rgba(34, 211, 238, .55));
    box-shadow: 0 10px 30px rgba(124, 58, 237, .45), inset 0 1px 0 rgba(255, 255, 255, .35);
}
.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active,
[data-testid="stDownloadButton"] > button:active { transform: translateY(0); }
.stButton > button:focus:not(:active),
[data-testid="stFormSubmitButton"] > button:focus:not(:active),
[data-testid="stDownloadButton"] > button:focus:not(:active) { border-color: rgba(255, 255, 255, .5) !important; }

[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(52, 211, 153, .55), rgba(34, 211, 238, .45));
    box-shadow: 0 6px 22px rgba(16, 185, 129, .30), inset 0 1px 0 rgba(255, 255, 255, .25);
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(52, 211, 153, .75), rgba(34, 211, 238, .60));
    box-shadow: 0 10px 30px rgba(16, 185, 129, .45), inset 0 1px 0 rgba(255, 255, 255, .35);
}

/* ---- Spinner ---- */
[data-testid="stSpinner"] {
    margin-top: 1rem;
    padding: .9rem 1.2rem;
    border-radius: 16px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    box-shadow: var(--glass-shadow);
    color: var(--text);
}
[data-testid="stSpinner"] i, [data-testid="stSpinner"] svg {
    border-top-color: var(--accent-2) !important;
    color: var(--accent-2) !important;
}

/* ---- Alertes (erreurs, infos) ---- */
[data-testid="stAlert"] {
    border-radius: 16px !important;
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 6px 24px rgba(0, 0, 0, .25);
}
[data-testid="stAlertContainer"], [data-testid="stAlert"] > div {
    border-radius: 16px !important;
}
[data-testid="stAlertContentError"], div[data-baseweb="notification"][kind="negative"] {
    color: #fecdd3 !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div,
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
    background: rgba(244, 63, 94, .12) !important;
    border: 1px solid rgba(251, 113, 133, .40) !important;
}

/* ---- Carte résultat ---- */
.result-card { margin-top: 1.6rem; padding: 1.4rem !important; }
.result-head { display: flex; gap: 1.1rem; align-items: center; }
.result-thumb {
    flex: 0 0 168px; height: 95px;
    border-radius: 14px; overflow: hidden;
    border: 1px solid rgba(255, 255, 255, .18);
    background: rgba(255, 255, 255, .05);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
}
.result-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.result-info { min-width: 0; }
.result-kicker {
    font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .12em;
    color: #6ee7b7; margin-bottom: .3rem;
}
.result-title {
    font-size: 1.12rem; font-weight: 700; line-height: 1.35; color: var(--text);
    margin: 0 0 .7rem;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.chips { display: flex; flex-wrap: wrap; gap: .45rem; }
.chip {
    padding: .3rem .7rem; border-radius: 999px;
    font-size: .78rem; font-weight: 500; color: var(--text);
    background: rgba(255, 255, 255, .08);
    border: 1px solid rgba(255, 255, 255, .16);
}
@media (max-width: 560px) {
    .result-head { flex-direction: column; align-items: stretch; }
    .result-thumb { flex-basis: auto; height: 170px; }
}

/* ---- Lecteur vidéo ---- */
[data-testid="stVideo"], video {
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, .16);
    box-shadow: var(--glass-shadow);
}

.footer {
    text-align: center; margin-top: 2.6rem;
    font-size: .8rem; color: rgba(238, 240, 255, .45);
}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
#  Utilitaires                                                                #
# --------------------------------------------------------------------------- #
class UserFacingError(Exception):
    """Erreur dont le message peut être affiché tel quel à l'utilisateur."""


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc) and "." in parsed.netloc


def format_duration(seconds) -> str:
    if not seconds:
        return "Durée inconnue"
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}h {minutes:02d}min {secs:02d}s" if hours else f"{minutes}min {secs:02d}s"


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("octets", "Ko", "Mo", "Go"):
        if size < 1024 or unit == "Go":
            return f"{size:.0f} {unit}" if unit == "octets" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} Go"


def safe_filename(title: str, ext: str = ".mp4") -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", title or "video")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name[:120] or "video") + ext


def friendly_error(raw: str) -> str:
    """Traduit les erreurs yt-dlp les plus courantes en messages clairs."""
    msg = re.sub(r"\x1b\[[0-9;]*m", "", raw or "")
    low = msg.lower()
    if "unsupported url" in low:
        return "Ce lien n'est pas pris en charge. Vérifiez qu'il pointe bien vers une page contenant une vidéo."
    if "private" in low or "login" in low or "log in" in low or "sign in" in low or "cookies" in low \
            or "authentication" in low or "members-only" in low or "confirm your age" in low:
        return ("Cette vidéo est privée ou restreinte (connexion requise, contenu réservé ou limite d'âge). "
                "Seules les vidéos publiques peuvent être récupérées.")
    if "not a bot" in low:
        return ("La plateforme a temporairement bloqué la requête (protection anti-robot). "
                "Réessayez dans quelques minutes ou avec un autre lien.")
    if "geo" in low or "not available in your country" in low:
        return "Cette vidéo n'est pas disponible depuis la région du serveur (restriction géographique)."
    if "404" in low or "not found" in low or "unavailable" in low or "removed" in low or "does not exist" in low:
        return "Vidéo introuvable : elle a peut-être été supprimée ou le lien est incorrect."
    if "no video formats" in low or "requested format" in low:
        return "Aucun format vidéo téléchargeable n'a été trouvé pour ce lien."
    if "max_filesize" in low or "larger than max" in low:
        return f"La vidéo dépasse la taille maximale autorisée ({MAX_FILESIZE_MB} Mo)."
    if "timed out" in low or "connection" in low or "network" in low:
        return "Problème de connexion avec la plateforme. Réessayez dans un instant."
    short = msg.replace("ERROR:", "").strip()
    return f"Impossible de récupérer la vidéo. Détail : {short[:300]}"


def build_ydl_options(output_dir: str) -> dict:
    has_ffmpeg = shutil.which("ffmpeg") is not None
    if has_ffmpeg:
        # Priorité : H.264 (avc1) + AAC (mp4a) → compatibilité PowerPoint / Windows / Mac maximale.
        fmt = (
            "bv*[vcodec^=avc1][ext=mp4]+ba[acodec^=mp4a]/"
            "b[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
            "bv*[ext=mp4]+ba[ext=m4a]/"
            "b[ext=mp4]/"
            "bv*+ba/b"
        )
    else:
        # Sans ffmpeg, impossible de fusionner : on prend le meilleur fichier MP4 « tout-en-un ».
        fmt = "b[ext=mp4][vcodec^=avc1]/b[ext=mp4]/b"

    opts = {
        "format": fmt,
        "outtmpl": str(Path(output_dir) / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "restrictfilenames": True,
        "max_filesize": MAX_FILESIZE_MB * 1024 * 1024,
        "socket_timeout": 30,
        "retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    }
    if has_ffmpeg:
        opts["merge_output_format"] = "mp4"
        # Garantit un conteneur MP4 même si la source n'en était pas un.
        opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
    return opts


def probe_codecs(path: Path) -> tuple[str | None, str | None]:
    """Renvoie (codec vidéo, codec audio) du fichier via ffprobe."""
    if not shutil.which("ffprobe"):
        return None, None
    codecs = {}
    for kind in ("v", "a"):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", f"{kind}:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        codecs[kind] = result.stdout.strip() or None
    return codecs["v"], codecs["a"]


def probe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def ensure_powerpoint_compatible(path: Path) -> Path:
    """Ré-encode en H.264 + AAC si la source n'utilise pas déjà ces codecs."""
    if path.suffix.lower() != ".mp4" or not shutil.which("ffmpeg"):
        return path
    vcodec, acodec = probe_codecs(path)
    if vcodec is None or (vcodec == "h264" and acodec in ("aac", None)):
        return path

    output = path.with_name(path.stem + "_h264.mp4")
    video_args = ["-c:v", "copy"] if vcodec == "h264" else [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
    ]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), *video_args,
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0 or not output.exists():
        return path  # On garde le MP4 d'origine plutôt que d'échouer.
    path.unlink(missing_ok=True)
    return output


def fetch_video(url: str) -> dict:
    """Télécharge la vidéo dans un dossier temporaire, lit le fichier puis nettoie le dossier."""
    tmp_dir = tempfile.mkdtemp(prefix="videoclip_")
    try:
        with yt_dlp.YoutubeDL(build_ydl_options(tmp_dir)) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise UserFacingError("Aucune vidéo n'a été trouvée à cette adresse.")
            if info.get("_type") == "playlist":
                entries = [e for e in (info.get("entries") or []) if e]
                if not entries:
                    raise UserFacingError("Ce lien correspond à une playlist vide ou inaccessible.")
                info = entries[0]

        files = [p for p in Path(tmp_dir).rglob("*") if p.is_file() and not p.name.endswith((".part", ".ytdl"))]
        mp4_files = [p for p in files if p.suffix.lower() == ".mp4"]
        candidates = mp4_files or files
        if not candidates:
            raise UserFacingError(
                f"Le téléchargement n'a produit aucun fichier (la vidéo dépasse peut-être {MAX_FILESIZE_MB} Mo)."
            )
        video_path = ensure_powerpoint_compatible(max(candidates, key=lambda p: p.stat().st_size))
        data = video_path.read_bytes()

        return {
            "title": info.get("title") or "Vidéo sans titre",
            "duration": info.get("duration") or probe_duration(video_path),
            "uploader": info.get("uploader") or info.get("channel") or info.get("extractor_key"),
            "thumbnail": info.get("thumbnail"),
            "platform": info.get("extractor_key") or "",
            "resolution": f"{info['height']}p" if info.get("height") else None,
            "is_mp4": video_path.suffix.lower() == ".mp4",
            "size": len(data),
            "data": data,
            "filename": safe_filename(info.get("title"), video_path.suffix.lower()),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --------------------------------------------------------------------------- #
#  Interface                                                                  #
# --------------------------------------------------------------------------- #
st.markdown(
    """
<div class="hero">
    <span class="badge"><span class="dot"></span>MP4 H.264 · Prêt pour PowerPoint</span>
    <h1>VidéoClip</h1>
    <p>Collez le lien d'une vidéo publique et récupérez-la en MP4,
    prête à être glissée dans vos présentations.</p>
    <div class="platforms">
        <span>YouTube</span><span>Facebook</span><span>LinkedIn</span>
        <span>Vimeo</span><span>X / Twitter</span><span>Instagram</span><span>+ 1 000 sites</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("download_form", border=False):
    url = st.text_input(
        "Lien de la vidéo",
        placeholder="https://www.youtube.com/watch?v=…",
        help="Fonctionne uniquement avec les vidéos publiques (sans connexion requise).",
    )
    submitted = st.form_submit_button("🎬  Récupérer la vidéo", use_container_width=True)

if submitted:
    st.session_state.pop("video", None)
    url = (url or "").strip()
    if not url:
        st.error("⚠️ Veuillez coller l'URL d'une vidéo avant de lancer la récupération.")
    elif not is_valid_url(url):
        st.error("⚠️ Cette URL ne semble pas valide. Elle doit commencer par « http:// » ou « https:// ».")
    else:
        try:
            with st.spinner("Récupération et conversion de la vidéo en MP4… Cela peut prendre quelques instants."):
                st.session_state["video"] = fetch_video(url)
        except UserFacingError as exc:
            st.error(f"❌ {exc}")
        except yt_dlp.utils.DownloadError as exc:
            st.error(f"❌ {friendly_error(str(exc))}")
        except Exception as exc:  # noqa: BLE001 — on ne veut jamais afficher de traceback brut
            st.error(f"❌ Une erreur inattendue est survenue : {html.escape(str(exc))[:300]}")

video = st.session_state.get("video")
if video:
    thumb = (
        f'<img src="{html.escape(video["thumbnail"], quote=True)}" alt="Miniature">'
        if video.get("thumbnail") else "🎞️"
    )
    chips = [f"⏱ {format_duration(video['duration'])}", f"💾 {format_size(video['size'])}"]
    if video.get("resolution"):
        chips.append(f"📐 {video['resolution']}")
    if video.get("platform"):
        chips.append(f"🌐 {video['platform']}")
    if video.get("uploader") and video.get("uploader") != video.get("platform"):
        chips.append(f"👤 {video['uploader']}")
    chips_html = "".join(f'<span class="chip">{html.escape(str(c))}</span>' for c in chips)

    st.markdown(
        f"""
<div class="glass-card result-card">
    <div class="result-head">
        <div class="result-thumb">{thumb}</div>
        <div class="result-info">
            <div class="result-kicker">✓ Vidéo prête</div>
            <div class="result-title">{html.escape(video["title"])}</div>
            <div class="chips">{chips_html}</div>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")
    if video["is_mp4"]:
        st.video(video["data"], format="video/mp4")
    else:
        st.info("ℹ️ Le format MP4 n'était pas disponible pour cette source : le fichier d'origine est fourni.")

    st.download_button(
        label="⬇️  Télécharger le fichier MP4",
        data=video["data"],
        file_name=video["filename"],
        mime="video/mp4",
        use_container_width=True,
    )

st.markdown(
    '<div class="footer">Respectez les droits d\'auteur : n\'utilisez que des vidéos que vous êtes '
    "autorisé·e à réutiliser.</div>",
    unsafe_allow_html=True,
)

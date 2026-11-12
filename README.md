# Convertisseur

Petite application personnelle qui convertit **localement** (sans Internet, sans envoi de fichiers) :
vidéo, audio, images, GIF, PDF, documents, tableurs, présentations, ebooks, sous-titres, polices,
archives, données (JSON, YAML, XML, TOML, SQLite) et pages web.
Chaque fichier peut être converti vers **tous les formats atteignables** (jusqu'à 65 par fichier) :
quand il n'existe pas de conversion directe, l'application enchaîne automatiquement plusieurs étapes
(par exemple DOCX → PDF → JPG, ou EPUB → HTML → TXT → MP3 en lecture vocale).

La **transcription de la parole** (audio ou vidéo → TXT, sous-titres SRT/VTT, DOCX) fonctionne aussi hors ligne
avec Whisper : le modèle choisi est téléchargé une seule fois (75 Mo à 1,6 Go selon la précision) dans
le dossier `modeles\whisper` de l'application (le modèle « Équilibré » y est déjà). Les sous-titres déjà
intégrés à une vidéo sont extraits directement. Avec une carte NVIDIA, la transcription passe sur le GPU
(bibliothèques CUDA installées dans `C:\ProgramData\Convertisseur`).

## Télécharger depuis un lien

Collez un lien YouTube, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo, Dailymotion… (plus de 1 800 sites
grâce à yt-dlp) dans la barre « Coller un lien », ou directement n'importe où dans la fenêtre (Ctrl+V).
Le contenu est téléchargé puis converti dans le format choisi : MP3, MP4, AVI, GIF, sous-titres SRT…
Les playlists et chaînes ajoutent un élément par vidéo (200 au maximum). Pour les contenus qui exigent une
connexion (Instagram, Facebook…), choisissez dans les Réglages le navigateur où vous êtes connecté.
Le bouton « Mettre à jour » des Réglages actualise yt-dlp quand un site change.

**Spotify → MP3** : collez le lien d'un titre, d'un album ou d'une playlist publique. Spotify protège ses fichiers
(DRM) : chaque morceau est donc retrouvé sur YouTube (même titre, même durée), puis converti en MP3 avec son titre,
son artiste, son année et sa pochette.
À réserver aux contenus dont vous avez les droits (vos vidéos, licences libres…).

## Boîte à outils

Plus de 70 outils, rangés par thème dans la barre latérale (Ctrl+K pour en chercher un). Les outils qui demandent un
réglage (mot de passe, pages, texte du filigrane…) ouvrent directement leurs réglages.

**Outils PDF** : fusionner, diviser (une page par fichier, par groupes ou par plages), extraire ou supprimer des
pages (dans l'ordre voulu), pivoter, protéger par mot de passe (AES-256, restrictions possibles), retirer un mot de
passe connu, filigrane, numéros de page, **PDF cherchable** (OCR de Windows, texte invisible placé sur chaque mot),
extraction des images, nettoyage des métadonnées, compression.

**Outils image** : **suppression de l'arrière-plan** par IA (modèle téléchargé une fois, fonctionne hors ligne),
redimensionner (50 %, 1920 px, agrandissement ×2 ou ×4), recadrer (1:1, 4:5, 16:9, 9:16…), pivoter ou retourner,
noir et blanc, sépia, netteté, flou, négatif, filigrane (coin, diagonale, répété), retrait des données EXIF et GPS,
collage en grille, lecture de **QR codes et codes-barres** (QR, EAN, UPC, Code 128, Data Matrix, PDF417…), kit
d'icônes pour site web (favicon), compression.

**Outils vidéo** : compression pour Discord, couper, **format vertical sur fond flou** (Reels, TikTok, Shorts),
recadrer, pivoter, vitesse, lecture à l'envers ou en boomerang, stabilisation, filigrane, ajout d'un logo,
remplacement ou mélange de la bande-son, retrait du son, sous-titres automatiques ou ajoutés, planche d'aperçu
horodatée, extraction d'images (ZIP), découpage en segments sans réencodage, fusion.

**Outils audio** : couper, normaliser, augmenter le volume, réduire le bruit, renforcer les basses, vitesse,
retirer la voix (karaoké), lecture à l'envers, **modifier les tags** (titre, artiste, album, année), ajouter une
pochette, découper en morceaux, sonnerie iPhone.

**Outils fichiers** (tous les fichiers, même inconnus) : rapport d'informations détaillé (codecs, EXIF et GPS,
pages, auteur, contenu d'archive), empreintes SHA-256, SHA-1, SHA-512 et MD5 (une ou un lot), archive 7Z ou ZIP
protégée par mot de passe, découpage d'un gros fichier en volumes, nettoyage des métadonnées, renommage en lot,
compression ZIP, extraction d'archives.

**Créer** : QR code (lien, texte, Wi-Fi, contact, e-mail, SMS, téléphone ; PNG, SVG ou PDF, couleurs au choix),
code-barres (EAN-13, UPC-A, Code 128, Code 39, ISBN…), lecture à voix haute d'un texte tapé ou collé (MP3),
**enregistrement de l'écran** (avec le micro si souhaité) et **enregistrement du micro**.

**Partout** : collez une capture d'écran avec Ctrl+V pour la convertir, la compresser ou y lire du texte ; chaque
conversion garde ses retouches (filigrane, recadrage, tags…) dans des sections de réglages repliables.

## Installation

Téléchargez **Convertisseur-Setup-x.y.z.exe** sur la page
[Releases](https://github.com/TheUnknownMurda/Convertisseur/releases) et lancez-le. L'assistant installe
l'application pour votre compte (sans droits administrateur), puis propose les logiciels nécessaires ; ceux qui
sont déjà présents sont détectés et décochés :

- Python 3.13 et les modules Python (obligatoire) ;
- FFmpeg, LibreOffice, Calibre, 7-Zip et Node.js ;
- l'accélération NVIDIA de la transcription (si une carte NVIDIA est présente) ;
- le modèle de transcription « Équilibré », pour transcrire sans Internet.

Une connexion Internet est nécessaire pendant l'installation. Windows demande une seule autorisation pour
LibreOffice, Calibre, 7-Zip et Node.js. L'installateur n'est pas signé : si Windows SmartScreen affiche
« Windows a protégé votre ordinateur », cliquez sur « Informations complémentaires » puis « Exécuter quand même ».
Le détail de l'installation est noté dans `installation.log`, dans le dossier de l'application.

Pour désinstaller : Paramètres → Applications → Convertisseur (les logiciels installés à côté restent en place).

## Lancer

Double-cliquez sur **`Convertisseur.bat`**. Au premier lancement, les composants Python s'installent
(quelques minutes). L'application s'ouvre ensuite dans sa propre fenêtre et se ferme avec elle.

Dans **Réglages**, les boutons ajoutent un **raccourci sur le Bureau** et l'entrée **Envoyer vers → Convertisseur**
du clic droit de l'Explorateur. Les fichiers envoyés (ou glissés sur le raccourci) s'ajoutent à la fenêtre déjà
ouverte.

## Utilisation

1. Choisissez un outil à gauche (Ctrl+K pour en chercher un, par exemple « heic jpg »), ou restez sur
   « Tous les fichiers », qui reconnaît le format tout seul.
2. Glissez des fichiers ou des dossiers dans la fenêtre, ou cliquez pour parcourir (Ctrl+O).
3. Pour chaque fichier, choisissez le format de sortie (recherche possible) et, au besoin, les options
   (qualité, résolution, début/fin, pages, ppp…).
4. Cliquez sur **Convertir** ou **Tout convertir** (Ctrl+Entrée).

Les fichiers sont enregistrés dans `Téléchargements\Convertisseur` (modifiable dans les Réglages).
Le bouton **Assembler…** en bas regroupe les fusions : images en **PDF**, **GIF animé** ou **diaporama MP4**,
vidéos ou audios bout à bout, sous-titres, archive ZIP (dans l'ordre de la liste ; glissez les lignes pour réordonner).
Chaque fichier affiche son trajet de conversion : format d'origine, étapes intermédiaires éventuelles, format choisi.

## Langue et thème

L'interface existe en **français** et en **anglais** : par défaut, elle suit la langue de Windows. Le bouton **EN / FR**
en bas de la barre latérale change de langue tout de suite ; le choix se retrouve aussi dans les Réglages
(« Automatique », « Français », « English »). Les messages, les rapports et les noms des fichiers produits suivent la
langue choisie (« photo (protected).pdf » en anglais).

Le **thème clair ou sombre** suit Windows par défaut ; le bouton soleil / lune à côté des Réglages bascule de l'un à
l'autre, et les Réglages permettent de revenir au mode « Automatique ». L'installateur demande aussi sa langue au
démarrage et la donne à l'application lors d'une première installation.

## Moteurs utilisés

| Moteur | Rôle |
|---|---|
| FFmpeg | vidéo, audio, GIF/APNG/WebP animés (accélération NVIDIA/Intel/AMD si disponible) |
| Pillow, pillow-heif, resvg, vtracer | images, HEIC/AVIF, rendu et vectorisation SVG |
| PyMuPDF, pdf2docx | PDF → images, texte, Word, EPUB, PowerPoint, Excel ; XPS/EPUB/MOBI/FB2/CBZ → PDF |
| LibreOffice | DOC, DOCX, ODT, RTF, XLS(X), ODS, PPT(X), ODP |
| Calibre | EPUB, MOBI, AZW3, FB2, LIT, PDB, LRF, HTMLZ, TXTZ, SNB, TCR, RB |
| Microsoft Edge | mise en page HTML/Markdown/TXT → PDF, pages web → PDF/PNG |
| 7-Zip | archives 7Z, RAR, ISO, CAB… (ZIP et TAR fonctionnent aussi sans) |
| pysubs2, fontTools | sous-titres ; polices |
| yt-dlp | téléchargement depuis YouTube, SoundCloud, Instagram, Facebook, TikTok, X… |
| faster-whisper (Whisper) | transcription de la parole : audio/vidéo → texte, SRT, VTT, DOCX |
| Windows | voix de synthèse (texte → audio) et OCR (image → texte) |

Les logiciels absents sont simplement signalés : les conversions qui en dépendent apparaissent grisées
avec la raison.

## Fichiers

- `app.py` : serveur local (127.0.0.1) et fenêtre.
- `convertisseur/graph.py` : graphe des conversions (calcule le meilleur chemin pour chaque paire).
- `convertisseur/engines/` : convertisseurs directs (médias, images, PDF, texte, bureautique, voix, OCR,
  sous-titres, polices, archives, données, pages web).
- `convertisseur/worker.py` : chaque conversion tourne dans un processus séparé (annulable).
- `convertisseur/i18n.py` : traduction anglaise des libellés, messages et noms de fichiers (le français sert de référence).
- `web/` : interface (`web/i18n.js` : traduction anglaise de l'interface).
- `installer/` : installateur Windows (Inno Setup) et script d'installation des prérequis (`setup.ps1`).
- `requirements-lock.txt` : versions exactes testées, utilisées par l'installateur.
- `config.json` : réglages et favoris ; `historique.json` : historique ; `convertisseur.log` : journal.

## Compiler l'installateur

Avec [Inno Setup](https://jrsoftware.org/isdl.php) 6.7 ou plus récent :

```bash
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

Le fichier est créé dans `dist\`. `installer\make_images.py` régénère les images de l'assistant.

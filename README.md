# Convertisseur

Petite application personnelle qui convertit **localement** (sans Internet, sans envoi de fichiers) :
vidéo, audio, images, GIF, PDF, documents, tableurs, présentations, ebooks, sous-titres, polices,
archives, données (JSON, YAML, XML, TOML, SQLite) et pages web.
Chaque fichier peut être converti vers **tous les formats atteignables** (jusqu'à 55 par fichier) :
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

## Outils

- **Compresser pour Discord** (10 Mo par défaut ; 8, 25, 50… au choix), et pour toute vidéo une **taille maximale** : encodage en deux
  passes, la résolution baisse au besoin pour garder une image nette.
- **Images** avec un poids maximal en Ko, **PDF compressé** (écran, liseuse ou impression).
- **Sous-titres** : conversion SRT, VTT, ASS, SSA, SBV, TTML, LRC, SUB, SAMI ; **sous-titres automatiques**
  (Whisper) incrustés dans l'image ou ajoutés comme piste ; l'outil « Ajouter des sous-titres » assemble une vidéo et un
  fichier de sous-titres.
- **Retouches vidéo et audio** (dans les options) : recadrage (carré, 9:16, 16:9… ou bandes noires retirées),
  rotation, vitesse, stabilisation, volume normalisé, fondus, silences retirés. Les vidéos HDR sont converties
  en SDR avec des couleurs correctes.
- **Fusionner** plusieurs vidéos ou audios bout à bout ; **compresser** des fichiers en ZIP ou 7Z ;
  **extraire** une archive (ZIP, RAR, 7Z, TAR, ISO…).
- **Page web** : collez un lien et choisissez PDF, capture PNG/JPG, HTML, Markdown, DOCX…
- **Polices** TTF, OTF, WOFF, WOFF2 entre elles, et aperçu PNG/PDF.
- **Favoris** : le bouton « Enregistrer ces réglages en favori » (dans les options d'un fichier) ajoute le format
  et les réglages choisis dans la barre latérale.
- **Historique** (icône d'horloge en haut) : les dernières conversions, avec ouverture du fichier ou du dossier.

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
- `web/` : interface.
- `installer/` : installateur Windows (Inno Setup) et script d'installation des prérequis (`setup.ps1`).
- `requirements-lock.txt` : versions exactes testées, utilisées par l'installateur.
- `config.json` : réglages et favoris ; `historique.json` : historique ; `convertisseur.log` : journal.

## Compiler l'installateur

Avec [Inno Setup](https://jrsoftware.org/isdl.php) 6.7 ou plus récent :

```bash
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

Le fichier est créé dans `dist\`. `installer\make_images.py` régénère les images de l'assistant.

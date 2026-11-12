"""Langue de l'interface.

Le français est la langue de référence du code. Chaque texte destiné à l'utilisateur (libellé, message,
nom de fichier produit) passe par tr(), qui renvoie sa traduction anglaise quand l'anglais est choisi.
Une entrée contenant « {} » est un gabarit : « Rendu de la page {}… » traduit aussi « Rendu de la page 3… ».
"""
from __future__ import annotations

import os
import re

LANG = "fr"


def set_lang(lang: str | None) -> None:
    global LANG
    LANG = lang if lang in ("fr", "en") else "fr"
    _CACHE.clear()


# Une entrée par ligne : « français => anglais ». Les lignes « // » sont des commentaires.
_EN = r"""
// ---------------------------------------------------------------- raccourcis de la barre latérale
Tous les fichiers => All files
Convertisseur universel => Universal converter
Vidéo, audio, image, PDF, document, tableur, présentation, ebook, sous-titres, police, archive ou données : déposez n'importe quel fichier, ou collez un lien. => Video, audio, image, PDF, document, spreadsheet, presentation, ebook, subtitles, font, archive or data: drop any file, or paste a link.
Convertisseur vidéo => Video converter
MP4, MKV, WEBM, MOV, AVI, WMV… changez de format, de résolution, coupez ou compressez. => MP4, MKV, WEBM, MOV, AVI, WMV… change the format or resolution, trim or compress.
Vidéo & audio => Video & audio
Convertisseur audio => Audio converter
MP3, WAV, FLAC, OGG, M4A, OPUS… dans tous les sens, avec le débit de votre choix. => MP3, WAV, FLAC, OGG, M4A, OPUS… any way round, at the bitrate of your choice.
Convertisseur MP3 => MP3 converter
N'importe quel audio ou vidéo en MP3. => Any audio or video to MP3.
Extraire la bande-son d'une vidéo MP4. => Extract the soundtrack of an MP4 video.
Vidéo → MP3 => Video → MP3
Extraire l'audio de n'importe quelle vidéo. => Extract the audio of any video.
Convertisseur MP4 => MP4 converter
Tout en MP4 (H.264 + AAC), lisible partout. => Everything to MP4 (H.264 + AAC), plays everywhere.
Vidéos d'iPhone ou de QuickTime en MP4 (sans perte quand c'est possible). => iPhone or QuickTime videos to MP4 (lossless when possible).
Audio → texte => Audio → text
Transcrivez la parole d'un audio ou d'une vidéo en texte, sur cet ordinateur (Whisper). => Transcribe the speech of an audio or video file to text, on this computer (Whisper).
Vidéo → sous-titres => Video → subtitles
Créez des sous-titres SRT ou VTT par reconnaissance de la parole, ou extrayez ceux intégrés à la vidéo. => Create SRT or VTT subtitles with speech recognition, or extract the ones embedded in the video.
MP3 en OGG Vorbis. => MP3 to OGG Vorbis.
Depuis un lien => From a link
Télécharger depuis un lien => Download from a link
Collez un lien YouTube, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo… puis choisissez le format. => Paste a YouTube, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo… link, then choose the format.
En ligne => Online
Collez un lien YouTube (vidéo ou playlist) pour récupérer l'audio en MP3. => Paste a YouTube link (video or playlist) to get the audio as MP3.
Collez un lien YouTube pour récupérer la vidéo en MP4 (résolution au choix dans les options). => Paste a YouTube link to get the video as MP4 (pick the resolution in the options).
Collez un lien SoundCloud (titre ou playlist) pour le récupérer en MP3. => Paste a SoundCloud link (track or playlist) to get it as MP3.
Collez un lien Spotify (titre, album ou playlist) : chaque morceau est retrouvé sur YouTube, converti en MP3 avec son titre, son artiste et sa pochette. => Paste a Spotify link (track, album or playlist): each song is found on YouTube and converted to MP3 with its title, artist and cover art.
Collez le lien d'un Reel ou d'une vidéo Instagram. => Paste the link of an Instagram Reel or video.
Collez le lien d'une vidéo ou d'un Reel Facebook. => Paste the link of a Facebook video or Reel.
Collez le lien d'une vidéo TikTok. => Paste the link of a TikTok video.
Collez le lien d'un message X (Twitter) contenant une vidéo. => Paste the link of an X (Twitter) post that contains a video.
Page web → PDF => Web page → PDF
Collez l'adresse d'une page web pour l'enregistrer en PDF, en image ou en Markdown. => Paste the address of a web page to save it as PDF, image or Markdown.
Fusionner des PDF => Merge PDFs
Ajoutez plusieurs PDF (et des images), puis « Fusionner en PDF » : dans l'ordre de la liste. => Add several PDFs (and images), then “Merge into PDF”: in list order.
Outils PDF => PDF tools
Diviser un PDF => Split a PDF
Un fichier par page, par groupes de pages ou selon vos plages. => One file per page, per group of pages or by your own ranges.
Extraire des pages => Extract pages
Gardez seulement les pages choisies, dans l'ordre de votre choix (ex. 3, 1-2, 8-). => Keep only the chosen pages, in the order you want (e.g. 3, 1-2, 8-).
Supprimer des pages => Delete pages
Retirez des pages d'un PDF. => Remove pages from a PDF.
Pivoter un PDF => Rotate a PDF
Faites pivoter toutes les pages ou seulement certaines. => Rotate every page or only some of them.
Protéger un PDF => Protect a PDF
Mot de passe à l'ouverture (chiffrement AES-256), restrictions possibles. => Password to open it (AES-256 encryption), optional restrictions.
Déverrouiller un PDF => Unlock a PDF
Retirez le mot de passe d'un PDF dont vous connaissez le mot de passe. => Remove the password from a PDF whose password you know.
Filigrane sur un PDF => Watermark a PDF
Texte en diagonale, répété ou dans un coin, avec l'opacité choisie. => Diagonal, tiled or corner text, at the opacity you choose.
Numéroter les pages => Number the pages
Ajoutez « 1, 2, 3… » ou « Page 1 sur 10 » sur chaque page. => Add “1, 2, 3…” or “Page 1 of 10” on every page.
PDF cherchable (OCR) => Searchable PDF (OCR)
Rend le texte des documents scannés sélectionnable et cherchable (reconnaissance de Windows). => Makes the text of scanned documents selectable and searchable (Windows recognition).
Extraire les images => Extract images
Récupère les images contenues dans un PDF, dans leur qualité d'origine. => Gets the images contained in a PDF, at their original quality.
Compresser un PDF => Compress a PDF
Allège un PDF (images recompressées, polices réduites). => Makes a PDF smaller (recompressed images, subset fonts).
Supprimer l'arrière-plan => Remove background
Détourage automatique par intelligence artificielle, sur cet ordinateur : PNG transparent. => Automatic AI cut-out, on this computer: transparent PNG.
Outils image => Image tools
Redimensionner => Resize
Changez la taille (50 %, 1920 px, agrandissement ×2…), dans le même format. => Change the size (50%, 1920 px, ×2 upscale…), in the same format.
Retouches => Edits
Recadrer => Crop
Carré, 4:5 Instagram, 16:9, 9:16 stories… recadrage centré. => Square, 4:5 Instagram, 16:9, 9:16 stories… centered crop.
Pivoter ou retourner => Rotate or flip
Rotation de 90°, 180° ou effet miroir. => 90° or 180° rotation, or mirror effect.
Noir et blanc et filtres => Black & white and filters
Noir et blanc, sépia, contraste automatique, netteté, flou, négatif. => Black & white, sepia, auto contrast, sharpen, blur, negative.
Filigrane sur des images => Watermark images
Signez vos photos : texte dans un coin, en diagonale ou répété. => Sign your photos: text in a corner, diagonal or tiled.
Filigrane => Watermark
Agrandir une image => Upscale an image
Agrandissement ×2 ou ×4 avec netteté. => ×2 or ×4 upscale with sharpening.
Compresser une image => Compress an image
Allège les images (qualité 75, ou taille maximale en Ko dans les options). => Makes images smaller (quality 75, or a maximum size in KB in the options).
Retirer les données EXIF / GPS => Remove EXIF / GPS data
Supprime l'appareil, la date et la position GPS avant de partager une photo. => Removes the camera, date and GPS location before you share a photo.
Créer un collage => Make a collage
Assemblez plusieurs images en une grille (colonnes, espacement, fond). => Arrange several images in a grid (columns, spacing, background).
Lire un QR code => Read a QR code
Lit les QR codes, codes-barres, Data Matrix et PDF417 d'une image ou d'une capture. => Reads QR codes, barcodes, Data Matrix and PDF417 from an image or a screenshot.
Kit d'icônes (favicon) => Icon kit (favicon)
Toutes les icônes d'un site web (favicon.ico, Apple, Android) et le code à coller. => Every icon a website needs (favicon.ico, Apple, Android) and the code to paste.
Compresser pour Discord => Compress for Discord
Vidéo en MP4 de 10 Mo maximum (taille réglable dans les options : 25, 50, 500 Mo…). => Video as an MP4 of 10 MB max (size adjustable in the options: 25, 50, 500 MB…).
Outils vidéo => Video tools
Couper une vidéo => Trim a video
Gardez un extrait : indiquez le début et la fin. => Keep a clip: set the start and the end.
Format vertical (Reels, TikTok) => Vertical format (Reels, TikTok)
La vidéo entière en 9:16, sur un fond flou d'elle-même, prête pour Reels, TikTok et Shorts. => The whole video in 9:16, over a blurred copy of itself, ready for Reels, TikTok and Shorts.
Recadrer une vidéo => Crop a video
Carré, 9:16, 16:9, bandes noires retirées… => Square, 9:16, 16:9, black bars removed…
Pivoter une vidéo => Rotate a video
Accélérer ou ralentir => Speed up or slow down
De 0,5× à 2×, son compris. => From 0.5× to 2×, sound included.
Inverser ou boomerang => Reverse or boomerang
Lecture à l'envers ou aller-retour (extraits de 3 minutes au plus). => Backwards or back-and-forth playback (clips of 3 minutes max).
Stabiliser une vidéo => Stabilize a video
Corrige les tremblements d'une vidéo filmée à la main. => Fixes the shaking of a handheld video.
Filigrane sur une vidéo => Watermark a video
Ajoutez votre nom ou une mention dans un coin de la vidéo. => Add your name or a notice in a corner of the video.
Ajouter un logo => Add a logo
Ajoutez une vidéo et une image (PNG transparent idéalement), puis « Ajouter le logo ». => Add a video and an image (ideally a transparent PNG), then “Add the logo”.
Remplacer la bande-son => Replace the soundtrack
Ajoutez une vidéo et une musique : remplacez ou mélangez le son d'origine. => Add a video and a music track: replace the original sound or mix with it.
Retirer le son => Remove the sound
Une vidéo muette, dans le même format. => A silent video, in the same format.
Sous-titres automatiques => Automatic subtitles
La parole est transcrite (Whisper) puis incrustée dans la vidéo. => The speech is transcribed (Whisper), then burned into the video.
Ajouter des sous-titres => Add subtitles
Ajoutez une vidéo et un fichier SRT, VTT ou ASS, puis « Ajouter les sous-titres ». => Add a video and an SRT, VTT or ASS file, then “Add the subtitles”.
Planche d'aperçu => Contact sheet
Une image qui résume la vidéo : 9 à 25 vignettes avec leur minutage. => One image that sums up the video: 9 to 25 thumbnails with their timestamps.
Extraire des images => Extract frames
Les images de la vidéo en JPG (1 par seconde, ou toutes), dans un ZIP. => The video frames as JPG (1 per second, or all of them), in a ZIP.
Découper en segments => Split into segments
Des morceaux de 15 s, 1 min, 10 min… sans réencodage (stories, envoi par messagerie). => Pieces of 15 s, 1 min, 10 min… without re-encoding (stories, messaging apps).
Fusionner vidéos ou audios => Merge videos or audio
Mettez plusieurs vidéos ou audios bout à bout (dans l'ordre de la liste). => Join several videos or audio files end to end (in list order).
Couper un audio => Trim audio
Outils audio => Audio tools
Normaliser le volume => Normalize the volume
Volume homogène (norme EBU R128), dans le même format. => Even volume (EBU R128 standard), in the same format.
Augmenter le volume => Increase the volume
De −12 à +10 dB, sans saturation. => From −12 to +10 dB, without clipping.
Son => Sound
Réduire le bruit => Reduce noise
Atténue le souffle et le bruit de fond d'un enregistrement. => Reduces the hiss and background noise of a recording.
Renforcer les basses => Boost the bass
Des basses plus présentes, sans saturation. => Fuller bass, without clipping.
De 0,5× à 2×, sans changer la hauteur de la voix. => From 0.5× to 2×, without changing the pitch.
Retirer la voix (karaoké) => Remove vocals (karaoke)
Atténue la voix enregistrée au centre (résultat variable selon le mixage). => Reduces vocals panned to the center (results depend on the mix).
Inverser un audio => Reverse audio
Lecture à l'envers. => Backwards playback.
Modifier les tags => Edit tags
Titre, artiste, album et année d'un morceau. => Title, artist, album and year of a song.
Étiquettes => Tags
Ajouter une pochette => Add cover art
Ajoutez un audio et une image, puis « Ajouter la pochette » (sans réencodage). => Add an audio file and an image, then “Add the cover” (no re-encoding).
Découper en morceaux => Split into pieces
Des morceaux de durée fixe, sans réencodage. => Fixed-length pieces, without re-encoding.
Sonnerie iPhone => iPhone ringtone
Un extrait de 40 secondes au plus, au format M4R des iPhone. => A clip of 40 seconds max, in the iPhone M4R format.
Informations détaillées => Detailed information
Tout sur un fichier : codecs, résolution, EXIF et GPS, pages, auteur, contenu d'archive, empreintes. => Everything about a file: codecs, resolution, EXIF and GPS, pages, author, archive contents, checksums.
Outils fichiers => File tools
Empreintes (SHA-256, MD5) => Checksums (SHA-256, MD5)
Vérifiez qu'un fichier n'a pas été modifié ou qu'un téléchargement est complet. => Check that a file has not been modified, or that a download is complete.
Protéger par mot de passe => Password-protect
Archive 7Z ou ZIP chiffrée en AES-256. Pour tout regrouper : « Compresser en ZIP » avec un mot de passe. => 7Z or ZIP archive with AES-256 encryption. To bundle several files: “Compress to ZIP” with a password.
Découper un gros fichier => Split a large file
En parties de 25 Mo, 100 Mo, 4 Go… à rassembler avec 7-Zip. => Into parts of 25 MB, 100 MB, 4 GB… to be joined again with 7-Zip.
Nettoyer les métadonnées => Clean metadata
Retire auteur, appareil, position GPS et commentaires avant de partager. => Removes author, camera, GPS location and comments before you share.
Renommer en lot => Batch rename
Des copies renommées selon un modèle : « Vacances {date} - {n} »… => Copies renamed from a pattern: “Holidays {date} - {n}”…
Empreintes d'un lot => Batch checksums
Un seul fichier texte avec l'empreinte SHA-256 et MD5 de chaque fichier. => A single text file with the SHA-256 and MD5 checksum of every file.
Compresser en ZIP => Compress to ZIP
Ajoutez plusieurs fichiers puis « Compresser en ZIP » (mot de passe possible). => Add several files, then “Compress to ZIP” (optional password).
Extraire une archive => Extract an archive
ZIP, RAR, 7Z, TAR, ISO… extraits dans un dossier. => ZIP, RAR, 7Z, TAR, ISO… extracted to a folder.
Créer un QR code => Create a QR code
Lien, texte, Wi-Fi, contact, e-mail, SMS ou téléphone : en PNG, SVG ou PDF, aux couleurs voulues. => Link, text, Wi-Fi, contact, email, SMS or phone: as PNG, SVG or PDF, in the colors you want.
Créer => Create
Créer un code-barres => Create a barcode
EAN-13, UPC-A, Code 128, Code 39, ISBN… en PNG ou SVG. => EAN-13, UPC-A, Code 128, Code 39, ISBN… as PNG or SVG.
Lire un texte à voix haute => Read text aloud
Tapez ou collez un texte : il est lu par une voix de Windows et enregistré en MP3. => Type or paste a text: a Windows voice reads it and it is saved as MP3.
Enregistrer l'écran => Record the screen
Une vidéo MP4 de votre écran, avec le son de votre micro si vous le souhaitez. => An MP4 video of your screen, with the sound of your microphone if you like.
Enregistrer le micro => Record the microphone
Un enregistrement audio MP3 depuis le micro de votre choix. => An MP3 audio recording from the microphone of your choice.
Convertisseur d'images => Image converter
PNG, JPG, WEBP, HEIC, AVIF, TIFF, ICO, SVG… redimensionnez et compressez au passage. => PNG, JPG, WEBP, HEIC, AVIF, TIFF, ICO, SVG… resize and compress along the way.
Images WEBP en PNG. => WEBP images to PNG.
Images JFIF en PNG. => JFIF images to PNG.
Vectorisez une image : idéal pour les logos et les illustrations. => Vectorize an image: ideal for logos and illustrations.
Photos d'iPhone (HEIC) en JPG. => iPhone photos (HEIC) to JPG.
Photos d'iPhone (HEIC) en PNG. => iPhone photos (HEIC) to PNG.
Images WEBP en JPG. => WEBP images to JPG.
Convertisseur SVG => SVG converter
SVG vers PNG, JPG, PDF… ou n'importe quelle image vers SVG. => SVG to PNG, JPG, PDF… or any image to SVG.
Convertisseur PDF => PDF converter
Tout vers PDF, et PDF vers Word, images, EPUB, Excel, PowerPoint… => Anything to PDF, and PDF to Word, images, EPUB, Excel, PowerPoint…
Convertisseur de documents => Document converter
DOCX, DOC, ODT, RTF, TXT, Markdown, HTML, PDF… dans tous les sens. => DOCX, DOC, ODT, RTF, TXT, Markdown, HTML, PDF… any way round.
Convertisseur de tableurs => Spreadsheet converter
Convertisseur de présentations => Presentation converter
PPTX, PPT, ODP vers PDF, images, vidéo ou texte. => PPTX, PPT, ODP to PDF, images, video or text.
Convertisseur d'ebooks => Ebook converter
EPUB, MOBI, AZW3, FB2, PDF… pour toutes les liseuses. => EPUB, MOBI, AZW3, FB2, PDF… for every e-reader.
PDF en document Word modifiable (DOCX). => PDF to an editable Word document (DOCX).
Une image JPG par page. => One JPG image per page.
PDF en livre numérique EPUB. => PDF to an EPUB ebook.
Livre numérique EPUB en PDF. => EPUB ebook to PDF.
Photos HEIC en PDF (une par fichier, ou fusionnées). => HEIC photos to PDF (one per file, or merged).
Documents Word en PDF, mise en page conservée. => Word documents to PDF, layout preserved.
Images JPG en PDF : un fichier par image, ou toutes fusionnées. => JPG images to PDF: one file per image, or all merged.
Sous-titres => Subtitles
SRT, VTT, ASS, SSA, SBV, TTML, LRC, SUB, SAMI dans tous les sens. => SRT, VTT, ASS, SSA, SBV, TTML, LRC, SUB, SAMI any way round.
Autres formats => Other formats
Polices => Fonts
TTF, OTF, WOFF, WOFF2 entre elles, et aperçu en PNG ou PDF. => TTF, OTF, WOFF, WOFF2 between each other, and previews as PNG or PDF.
ZIP, 7Z, RAR, TAR, GZ, ISO… vers ZIP, 7Z, TAR.GZ ou un dossier. => ZIP, 7Z, RAR, TAR, GZ, ISO… to ZIP, 7Z, TAR.GZ or a folder.
Données => Data
JSON, YAML, XML, TOML, SQLite vers CSV, Excel, HTML… et inversement. => JSON, YAML, XML, TOML, SQLite to CSV, Excel, HTML… and back.
Vidéo → GIF => Video → GIF
Transformez un extrait vidéo en GIF animé. => Turn a video clip into an animated GIF.
MP4 en GIF animé. => MP4 to animated GIF.
WEBM en GIF animé. => WEBM to animated GIF.
PNG animé (APNG) en GIF. => Animated PNG (APNG) to GIF.
GIF en vidéo MP4 (beaucoup plus léger). => GIF to MP4 video (much smaller).
GIF en PNG animé (APNG), en couleurs complètes. => GIF to animated PNG (APNG), in full color.
Assemblez plusieurs images en un GIF animé. => Combine several images into an animated GIF.
MOV en GIF animé. => MOV to animated GIF.
AVI en GIF animé. => AVI to animated GIF.

// ---------------------------------------------------------------- options
Qualité => Quality
Originale (rapide si possible) => Original (fast when possible)
Haute => High
Moyenne => Medium
Basse (fichier léger) => Low (small file)
Résolution => Resolution
Originale => Original
originale => original
Début => Start
Fin => End
jusqu'à la fin => to the end
Débit => Bitrate
Canaux => Channels
Originaux => Original
Originales => Original
Stéréo => Stereo
Fréquence => Sample rate
44,1 kHz => 44.1 kHz
22,05 kHz => 22.05 kHz
Images par seconde => Frames per second
Largeur => Width
Lecture en boucle => Loop playback
Moment de la capture => Capture time
auto (10 %) => auto (10%)
Images => Frames
Première image => First frame
Toutes les images (ZIP) => All frames (ZIP)
Sans perte => Lossless
Largeur max (px) => Max width (px)
Hauteur max (px) => Max height (px)
Fond (transparence) => Background (transparency)
Largeur de rendu (px) => Render width (px)
Affiche (aplats de couleur) => Poster (flat colors)
Photo (détaillé) => Photo (detailed)
Noir et blanc => Black & white
72 ppp => 72 dpi
96 ppp => 96 dpi
150 ppp => 150 dpi
200 ppp => 200 dpi
300 ppp (impression) => 300 dpi (print)
600 ppp => 600 dpi
toutes (ex. 1-3, 5) => all (e.g. 1-3, 5)
Regrouper en ZIP (sinon : un dossier) => Bundle in a ZIP (otherwise: a folder)
Format de page => Page size
Lettre US => US Letter
Légal US => US Legal
Taille du texte => Text size
A4 (orientation auto) => A4 (auto orientation)
Lettre US (orientation auto) => US Letter (auto orientation)
Taille de l'image => Image size
Durée (secondes) => Duration (seconds)
Durée par page (s) => Duration per page (s)
Durée par image (ms) => Duration per image (ms)
Voix => Voice
Automatique (selon la langue) => Automatic (by language)
Vitesse => Speed
Lente => Slow
Posée => Steady
Normale => Normal
Rapide => Fast
Très rapide => Very fast
Modèle (téléchargé au 1er usage) => Model (downloaded on first use)
{} — déjà téléchargé => {} — already downloaded
Très rapide (75 Mo) => Very fast (75 MB)
Rapide (145 Mo) => Fast (145 MB)
Équilibré (485 Mo) => Balanced (485 MB)
Précis (1,5 Go) => Accurate (1.5 GB)
Très précis (1,6 Go) => Very accurate (1.6 GB)
Langue parlée => Spoken language
Détection automatique => Automatic detection
Français => French
Anglais => English
Espagnol => Spanish
Allemand => German
Italien => Italian
Portugais => Portuguese
Néerlandais => Dutch
Arabe => Arabic
Chinois => Chinese
Japonais => Japanese
Coréen => Korean
Russe => Russian
Polonais => Polish
Turc => Turkish
Ukrainien => Ukrainian
Traduire en anglais => Translate to English
Source des sous-titres => Subtitle source
Sous-titres intégrés s'il y en a, sinon transcription => Embedded subtitles if any, otherwise transcription
Toujours transcrire la parole => Always transcribe the speech
Sous-titres automatiques (Whisper) => Automatic subtitles (Whisper)
Non => No
Incrustés (toujours visibles) => Burned in (always visible)
Intégrés (désactivables) => Embedded (can be turned off)
Taille des sous-titres incrustés => Burned-in subtitle size
Petits => Small
Moyens => Medium
Grands => Large
Taille maximale => Maximum size
Aucune limite => No limit
8 Mo => 8 MB
10 Mo (Discord) => 10 MB (Discord)
25 Mo => 25 MB
50 Mo (Discord Nitro Basic) => 50 MB (Discord Nitro Basic)
100 Mo => 100 MB
500 Mo (Discord Nitro) => 500 MB (Discord Nitro)
Taille max (Ko) => Max size (KB)
aucune => none
aucun => none
Fondu début/fin => Fade in/out
Aucun => None
Aucune => None
Couper les silences (début et fin) => Trim silence (start and end)
0,5× => 0.5×
0,75× => 0.75×
1,25× => 1.25×
1,5× => 1.5×
90° à droite => 90° right
90° à gauche => 90° left
Miroir horizontal => Horizontal mirror
Miroir vertical => Vertical mirror
Recadrage => Crop
Auto (bandes noires) => Auto (black bars)
Carré 1:1 => Square 1:1
Paysage 16:9 => Landscape 16:9
Vertical 9:16 sur fond flou (Reels, TikTok, Shorts) => Vertical 9:16 on a blurred background (Reels, TikTok, Shorts)
Carré sur fond flou => Square on a blurred background
Stabiliser l'image (plus lent) => Stabilize the picture (slower)
Auto (MP4 s'il y a de la vidéo, sinon MP3) => Auto (MP4 if there is video, otherwise MP3)
Format de l'archive => Archive format
7Z (plus compact) => 7Z (more compact)
Niveau => Level
Écran (très léger, 72 ppp) => Screen (very light, 72 dpi)
Équilibré (150 ppp) => Balanced (150 dpi)
Impression (300 ppp) => Print (300 dpi)
Largeur de la page => Page width
Texte d'aperçu => Preview text
Portez ce vieux whisky au juge blond qui fume => The quick brown fox jumps over the lazy dog
Séparateur => Separator
Virgule ( , ) => Comma ( , )
Point-virgule ( ; ) => Semicolon ( ; )
Tabulation => Tab
Feuilles => Sheets
Première feuille => First sheet
Toutes (un fichier par feuille, ZIP) => All (one file per sheet, ZIP)
Taille => Size
Taille d'origine => Original size
75 % => 75%
50 % => 50%
25 % => 25%
Agrandir ×2 => Upscale ×2
Agrandir ×4 => Upscale ×4
Recadrer (proportions) => Crop (aspect ratio)
Filtre => Filter
Sépia => Sepia
Contraste automatique => Auto contrast
Plus net => Sharper
Flou => Blur
Négatif => Negative
24 (cinéma) => 24 (cinema)
Lecture => Playback
À l'envers => Backwards
Aller-retour (boomerang) => Back and forth (boomerang)
Réduire le bruit de fond => Reduce background noise
Basses => Bass
Normales => Normal
Renforcées => Boosted
Très renforcées => Strongly boosted
Inchangé => Unchanged
inchangé => unchanged
Retirer la voix (karaoké, approximatif) => Remove vocals (karaoke, approximate)
Lire à l'envers => Play backwards
Texte du filigrane => Watermark text
ex. © Mon nom, CONFIDENTIEL => e.g. © My name, CONFIDENTIAL
En diagonale => Diagonal
Répété partout => Tiled everywhere
Au centre => Center
En haut => Top
En bas => Bottom
En haut à gauche => Top left
En haut à droite => Top right
En bas à gauche => Bottom left
En bas à droite => Bottom right
En bas au centre => Bottom center
En haut au centre => Top center
Petite => Small
Grande => Large
Petit => Small
Grand => Large
Moyen => Medium
Opacité (%) => Opacity (%)
Couleur => Color
Titre => Title
Artiste => Artist
Année => Year
ex. 2026 => e.g. 2026
Supprimer les métadonnées (auteur, appareil, position GPS…) => Remove metadata (author, camera, GPS location…)
Confidentialité => Privacy
Découpage => Split
Une page par fichier => One page per file
Par groupes de 2 pages => In groups of 2 pages
Par groupes de 5 pages => In groups of 5 pages
Par groupes de 10 pages => In groups of 10 pages
Selon les plages ci-contre => By the ranges entered
Plages (une par fichier) => Ranges (one per file)
ex. 1-3, 4-6, 7- => e.g. 1-3, 4-6, 7-
Garder ces pages (dans cet ordre) => Keep these pages (in this order)
Supprimer ces pages => Delete these pages
Mot de passe => Password
à choisir => choose one
Interdire aussi l'impression, la copie et la modification => Also prevent printing, copying and editing
Page 1 sur 10 => Page 1 of 10
Premier numéro => First number
Langue du texte => Text language
Langue de Windows => Windows language
Qualité du détourage => Cut-out quality
Précis (modèle de 175 Mo, téléchargé une fois) => Accurate (175 MB model, downloaded once)
Rapide (modèle de 5 Mo) => Fast (5 MB model)
Recadrer sur le sujet => Crop to the subject
Fond => Background
Blanc => White
Noir => Black
Grille => Grid
1 par seconde => 1 per second
2 par seconde => 2 per second
5 par seconde => 5 per second
10 par seconde => 10 per second
Toutes => All
Durée de chaque morceau => Length of each piece
15 secondes (stories) => 15 seconds (stories)
30 secondes => 30 seconds
1 heure => 1 hour
Taille de chaque partie => Size of each part
5 Mo => 5 MB
10 Mo => 10 MB
25 Mo (pièce jointe) => 25 MB (attachment)
700 Mo (CD) => 700 MB (CD)
4 Go (clé FAT32) => 4 GB (FAT32 drive)
Colonnes => Columns
Automatique => Automatic
Espacement => Spacing
Ajustement => Fit
Remplir les cases (recadré) => Fill the cells (cropped)
Images entières => Whole images
Position du logo => Logo position
Taille du logo => Logo size
Bande-son => Soundtrack
Remplacer le son d'origine => Replace the original sound
Mélanger avec le son d'origine => Mix with the original sound
Modèle de nom => Name pattern
{n} numéro · {nom} nom d'origine · {date} date => {n} number · {name} original name · {date} date
Fichier {n} => File {n}
Chiffres => Digits
Mot de passe (facultatif) => Password (optional)
ex. 1-3, 7, 10- => e.g. 1-3, 7, 10-
toutes => all
celui du PDF => the PDF's own

// ---------------------------------------------------------------- formats, groupes, familles
Vidéo => Video
WEBP animé => Animated WEBP
M4B (livre audio) => M4B (audiobook)
M4R (sonnerie) => M4R (ringtone)
Tableur => Spreadsheet
Présentation => Presentation
LRC (paroles) => LRC (lyrics)
Police => Font
Dossier (extraire) => Folder (extract)
Compresser le PDF => Compress the PDF
Diviser (un fichier par page) => Split (one file per page)
Extraire ou supprimer des pages => Extract or delete pages
Pivoter les pages => Rotate the pages
Retirer le mot de passe => Remove the password
Ajouter un filigrane => Add a watermark
Rendre le texte cherchable (OCR) => Make the text searchable (OCR)
Supprimer les métadonnées => Remove metadata
Supprimer l'arrière-plan (PNG) => Remove background (PNG)
Lire un QR code ou un code-barres => Read a QR code or barcode
Kit d'icônes pour site web (ZIP) => Website icon kit (ZIP)
Planche d'aperçu (JPG) => Contact sheet (JPG)
Extraire des images (ZIP) => Extract frames (ZIP)
Empreintes (SHA-256, MD5…) => Checksums (SHA-256, MD5…)
Outils fichier => File tools
Rapport d'informations (TXT) => Information report (TXT)
Archive protégée par mot de passe => Password-protected archive
Découper en volumes (7-Zip) => Split into volumes (7-Zip)
Capture => Screenshot
Image (capture) => Image (snapshot)
Document (capture) => Document (snapshots)
Texte (transcription de la parole) => Text (speech transcription)
Vidéo (pochette ou onde) => Video (cover or waveform)
Image (spectrogramme) => Image (spectrogram)
Image (1re image) => Image (1st frame)
Document (une page par image) => Document (one page per frame)
Document (image intégrée) => Document (embedded image)
Vidéo (image fixe) => Video (still image)
Texte (reconnaissance OCR) => Text (OCR)
Présentation (image intégrée) => Presentation (embedded image)
Image (une par page) => Image (one per page)
Vidéo (diaporama) => Video (slideshow)
Audio (lecture vocale) => Audio (read aloud)
Texte des dialogues => Dialogue text
Aperçu de la police => Font preview
Capture de la page => Page screenshot
Fichier => File
Page web => Web page
Inconnu => Unknown
fichier => file

// ---------------------------------------------------------------- assemblages
Fusionner en un PDF => Merge into one PDF
Fusionner en PDF => Merge into PDF
Créer un GIF animé => Create an animated GIF
Créer un diaporama vidéo => Create a video slideshow
Diaporama MP4 => MP4 slideshow
Fusionner bout à bout => Join end to end
Fusionner vidéo/audio => Merge video/audio
Ajouter les sous-titres à la vidéo => Add the subtitles to the video
Ajouter les sous-titres => Add the subtitles
Compresser en une archive => Compress into an archive
Ajouter le logo à la vidéo => Add the logo to the video
Ajouter le logo => Add the logo
Ajouter la pochette => Add the cover
Renommer en lot (copies) => Batch rename (copies)
Empreintes de tous les fichiers => Checksums of all files
Empreintes du lot => Batch checksums

// ---------------------------------------------------------------- outils manquants (« Nécessite … »)
Nécessite {}. => Requires {}.
une voix de synthèse Windows => a Windows speech voice
la reconnaissance de texte de Windows (OCR) => Windows text recognition (OCR)
le module {} => the {} module
l'encodeur {} => the {} encoder

// ---------------------------------------------------------------- serveur
Annulé => Cancelled
Terminé => Done
En attente… => Waiting…
Démarrage… => Starting…
Ce fichier a été déplacé ou supprimé. => This file has been moved or deleted.
Le fichier a été déplacé ou supprimé. => The file has been moved or deleted.
Collez une adresse complète, qui commence par https:// => Paste a full address, starting with https://
Le module de téléchargement (yt-dlp) est manquant. => The download module (yt-dlp) is missing.
Saisissez ou collez un texte. => Type or paste some text.
Texte trop long (2 millions de caractères au plus). => Text too long (2 million characters max).
Dossier « Envoyer vers » introuvable. => “Send to” folder not found.
Fichier introuvable : réimportez-le. => File not found: add it again.
Dossier où enregistrer les conversions => Folder where conversions are saved
Impossible de créer le raccourci. => Could not create the shortcut.
Convertisseur de fichiers local => Local file converter
Générateur inconnu. => Unknown generator.
Format de sortie non proposé pour ce fichier. => This output format is not offered for this file.
Conversion indisponible. => Conversion unavailable.
Les liens doivent d'abord être convertis en fichiers. => Links must be converted into files first.
Certains fichiers ne peuvent pas être assemblés ainsi. => Some files cannot be combined this way.
Mode inconnu. => Unknown mode.
Choisir des fichiers => Choose files
Choisir des fichiers à convertir => Choose files to convert
Choisir un dossier => Choose a folder
Enregistrement d'écran => Screen recording
Enregistrement audio => Audio recording
Code-barres => Barcode
Analyse du lien impossible : {} => Could not analyze the link: {}
La mise à jour a échoué : {} => The update failed: {}
Dossier de sortie inaccessible : {} => Output folder not accessible: {}
Dossier de sortie inaccessible ({}) : {} => Output folder not accessible ({}): {}
Impossible d'ouvrir le fichier : {} => Could not open the file: {}
Le convertisseur s'est arrêté de façon inattendue (code {}). => The converter stopped unexpectedly (code {}).
Dossier inutilisable : {} => Unusable folder: {}
Import interrompu : {} => Import interrupted: {}
Enregistrement impossible : {} => Could not record: {}
Erreur inattendue : {} => Unexpected error: {}
Mémoire insuffisante pour cette conversion. => Not enough memory for this conversion.

// ---------------------------------------------------------------- conversion : progression
Préparation… => Preparing…
Étape {}/{} : {} → {}… => Step {}/{}: {} → {}…
Nouvel essai par un autre chemin… => Trying another way…
Cette conversion n'est pas possible avec les outils installés. => This conversion is not possible with the installed tools.
La conversion n'a produit aucun fichier. => The conversion produced no file.
Ajout de {}… => Adding {}…
Analyse de la mise en page… => Analyzing the layout…
Analyse des tremblements… => Analyzing the shake…
Analyse du fichier… => Analyzing the file…
Analyse des couleurs… => Analyzing colors…
Assemblage de l'image et du son… => Merging picture and sound…
Calcul des empreintes… => Computing checksums…
Calcul du spectrogramme… => Computing the spectrogram…
Capture de la page… => Capturing the page…
Carte graphique indisponible : passage au processeur… => Graphics card unavailable: switching to the processor…
Chargement du modèle ({})… => Loading the model ({})…
Chiffrement AES-256… => AES-256 encryption…
Chiffrement… => Encrypting…
Compression des images… => Compressing images…
Compression… => Compressing…
Conversion avec Calibre… => Converting with Calibre…
Conversion avec LibreOffice… => Converting with LibreOffice…
Conversion de l'image… => Converting the image…
Conversion de la police… => Converting the font…
Conversion audio… => Converting audio…
Création des icônes… => Creating the icons…
Création du ZIP ({} images)… => Creating the ZIP ({} frames)…
Création du document Word… => Creating the Word document…
Création du GIF… => Creating the GIF…
Création de l'APNG… => Creating the APNG…
Création du WEBP animé… => Creating the animated WEBP…
Création de la vidéo… => Creating the video…
Création du diaporama… => Creating the slideshow…
Création de la planche d'aperçu… => Creating the contact sheet…
Découpage… => Splitting…
Découpage en volumes… => Splitting into volumes…
Détourage du sujet… => Cutting out the subject…
Encodage vidéo… => Encoding video…
Encodage vidéo ({})… => Encoding video ({})…
Enregistrement… => Saving…
Extraction… => Extracting…
Extraction de la pochette… => Extracting the cover…
Extraction des images… => Extracting frames…
Extraction des sous-titres intégrés… => Extracting embedded subtitles…
Fichier {}/{}… => File {}/{}…
Impression de la page en PDF… => Printing the page to PDF…
Inversion de la vidéo… => Reversing the video…
Lecture de l'EPUB… => Reading the EPUB…
Lecture de la page… => Reading the page…
Lecture de {}… => Reading {}…
Lecture des données… => Reading the data…
Lecture du document Word… => Reading the Word document…
Lecture du morceau Spotify… => Reading the Spotify track…
Lecture du tableur… => Reading the spreadsheet…
Lecture vocale ({})… => Reading aloud ({})…
voix par défaut => default voice
Mise en page du PDF… => Laying out the PDF…
Mise en page {}–{} / {}… => Laying out {}–{} / {}…
Optimisation des polices et de la structure… => Optimizing fonts and structure…
Ouverture du PDF… => Opening the PDF…
Préparation de la page {}/{}… => Preparing page {}/{}…
Préparation de {}… => Preparing {}…
Préparation de l'audio… => Preparing the audio…
Recherche de QR codes et de codes-barres… => Looking for QR codes and barcodes…
Recherche de tableaux, page {}… => Looking for tables, page {}…
Recherche de « {} » sur YouTube… => Searching YouTube for “{}”…
Reconnaissance du texte ({} page(s))… => Recognizing text ({} page(s))…
Reconnaissance du texte… => Recognizing text…
Remplacement de la bande-son… => Replacing the soundtrack…
Remuxage rapide (sans réencodage)… => Fast remux (no re-encoding)…
Ajout du logo… => Adding the logo…
Rendu de la page {}… => Rendering page {}…
Rendu de la page… => Rendering the page…
Téléchargement du modèle de détourage… {} / {} Mo => Downloading the cut-out model… {} / {} MB
Téléchargement du modèle « {} » ({}, une seule fois)… => Downloading the “{}” model ({}, only once)…
Téléchargement… {} Mo => Downloading… {} MB
Téléchargement terminé. => Download complete.
Transcription ({}, langue : {}) — {}× le temps réel… => Transcription ({}, language: {}) — {}× real time…
Transcription ({}) — {}× le temps réel… => Transcription ({}) — {}× real time…
Vectorisation… => Vectorizing…
Écriture… => Writing…
{}/{} : {} => {}/{}: {}
{} page(s) conservée(s)… => {} page(s) kept…

// ---------------------------------------------------------------- conversion : erreurs
7-Zip est nécessaire pour ce type d'archive. => 7-Zip is required for this type of archive.
7-Zip est nécessaire pour cet outil. => 7-Zip is required for this tool.
L'archive est vide. => The archive is empty.
Cette archive est protégée par un mot de passe. => This archive is password-protected.
Format de données non géré : {} => Unsupported data format: {}
La base de données ne contient aucune table. => The database contains no tables.
Données illisibles ({}) : {} => Unreadable data ({}): {}
Format de sortie non géré : {} => Unsupported output format: {}
Lien non reconnu : ce site n'est pas pris en charge (ou l'adresse est incomplète). => Link not recognized: this site is not supported (or the address is incomplete).
Ce contenu est protégé (DRM) : il ne peut pas être téléchargé. => This content is protected (DRM): it cannot be downloaded.
Ce contenu est privé. => This content is private.
Contenu soumis à une limite d'âge : une connexion est nécessaire. Dans Réglages, choisissez le navigateur où vous êtes connecté. => Age-restricted content: you need to be signed in. In Settings, choose the browser where you are signed in.
Ce site demande d'être connecté pour ce contenu. Dans Réglages, choisissez le navigateur où vous êtes connecté pour utiliser sa session. => This site requires you to be signed in for this content. In Settings, choose the browser where you are signed in to use its session.
Contenu indisponible (supprimé, privé ou bloqué dans votre pays). => Content unavailable (deleted, private or blocked in your country).
Problème de connexion Internet : réessayez. => Internet connection problem: try again.
Téléchargement impossible. => The download failed.
Lien Spotify introuvable, privé ou réservé à certains pays. => Spotify link not found, private or limited to some countries.
Ce lien Spotify ne désigne pas un morceau. => This Spotify link is not a track.
Aucun morceau lisible dans ce lien Spotify. => No playable track in this Spotify link.
Collez le lien d'un titre, d'un album ou d'une playlist Spotify (bouton Partager → Copier le lien). => Paste the link of a Spotify track, album or playlist (Share button → Copy link).
Rien à télécharger à cette adresse. => Nothing to download at this address.
Le téléchargement n'a produit aucun fichier. => The download produced no file.
Spotify est inaccessible : {} => Spotify is unreachable: {}
Cette liste de lecture est vide. => This playlist is empty.
Ce lien est une liste de lecture : ajoutez-le avec « Ajouter » pour obtenir un élément par vidéo. => This link is a playlist: add it with “Add” to get one item per video.
Morceau introuvable sur YouTube : {} => Track not found on YouTube: {}
Le fichier fait moins de {} Mo : il n'y a rien à découper. => The file is smaller than {} MB: there is nothing to split.
Indiquez un mot de passe dans les réglages. => Enter a password in the settings.
Indiquez le nom du réseau Wi-Fi. => Enter the Wi-Fi network name.
Indiquez au moins un nom. => Enter at least one name.
Indiquez l'adresse e-mail. => Enter the email address.
Indiquez le numéro de téléphone. => Enter the phone number.
Saisissez le texte ou le lien à encoder. => Type the text or link to encode.
Saisissez le contenu du code-barres. => Type the barcode content.
Texte trop long pour un QR code : {} => Text too long for a QR code: {}
Contenu invalide pour un code {} : {} => Invalid {} content: {}
Contenu invalide pour un code {} ({}) : {} => Invalid {} content ({}): {}
12 ou 13 chiffres => 12 or 13 digits
7 ou 8 chiffres => 7 or 8 digits
11 ou 12 chiffres => 11 or 12 digits
un ISBN commençant par 978 ou 979 => an ISBN starting with 978 or 979
un nombre pair de chiffres => an even number of digits
des majuscules, chiffres et - . $ / + % espace => capital letters, digits and - . $ / + % space
Le module pillow-heif est nécessaire pour les images HEIC. => The pillow-heif module is required for HEIC images.
Aucune page à créer. => No pages to create.
Aucune image trouvée dans cette archive. => No images found in this archive.
« {} » est protégé par un mot de passe. => “{}” is password-protected.
« {} » est illisible. => “{}” is unreadable.
« {} » ne contient pas de son. => “{}” has no sound.
Format d'image non géré : {} => Unsupported image format: {}
Le module onnxruntime est introuvable : réinstallez les modules Python. => The onnxruntime module is missing: reinstall the Python modules.
Aucun QR code ni code-barres lisible dans cette image. => No readable QR code or barcode in this image.
Ajoutez au moins deux images pour un collage. => Add at least two images for a collage.
Téléchargement du modèle impossible (connexion Internet ?) : {} => Could not download the model (Internet connection?): {}
Le détourage a échoué : {} => The cut-out failed: {}
Format vidéo non géré : {} => Unsupported video format: {}
Format audio non géré : {} => Unsupported audio format: {}
FFmpeg est introuvable. => FFmpeg was not found.
FFmpeg a échoué : {} => FFmpeg failed: {}
Fichier illisible ou corrompu : aucun flux audio ou vidéo reconnu. => Unreadable or corrupt file: no audio or video stream recognized.
Le début est après la fin du fichier. => The start is after the end of the file.
La fin doit être après le début. => The end must be after the start.
Aucune piste vidéo dans ce fichier. => No video track in this file.
Ajoutez une vidéo et un fichier de sous-titres. => Add a video and a subtitle file.
Ce fichier ne contient aucune piste audio. => This file has no audio track.
Ce PDF est protégé par un mot de passe. => This PDF is password-protected.
La lecture inversée est limitée à 3 minutes : réglez « Début » et « Fin » sur un extrait. => Reverse playback is limited to 3 minutes: set “Start” and “End” to a clip.
Aucune image dans ce fichier. => No frames in this file.
Durée inconnue : impossible de répartir les images. => Unknown duration: the frames cannot be spread out.
La planche n'a pas pu être créée. => The contact sheet could not be created.
Cela ferait environ {} images : choisissez moins d'images par seconde, ou un extrait (Début et Fin). => That would make about {} frames: choose fewer frames per second, or a clip (Start and End).
Aucune image n'a pu être extraite. => No frames could be extracted.
Le fichier est plus court qu'un morceau : il n'y a rien à découper. => The file is shorter than one piece: there is nothing to split.
Le découpage n'a produit aucun fichier. => Splitting produced no file.
Ajoutez une vidéo et une image (le logo). => Add a video and an image (the logo).
Ajoutez une vidéo et un fichier audio (la nouvelle bande-son). => Add a video and an audio file (the new soundtrack).
Ajoutez un fichier audio et une image (la pochette). => Add an audio file and an image (the cover).
Aucun texte reconnu dans cette image. => No text recognized in this image.
Aucune langue de reconnaissance de texte n'est installée dans Windows. => No text recognition language is installed in Windows.
La reconnaissance de texte a échoué : {} => Text recognition failed: {}
Lecture de tableur non gérée : {} => Unsupported spreadsheet reading: {}
LibreOffice est nécessaire pour cette conversion. => LibreOffice is required for this conversion.
Calibre est nécessaire pour cette conversion. => Calibre is required for this conversion.
Le tableur est vide. => The spreadsheet is empty.
Aucun texte ni tableau trouvé dans ce PDF. => No text or tables found in this PDF.
LibreOffice a mis trop de temps à répondre. => LibreOffice took too long to respond.
LibreOffice n'a pas pu convertir ce fichier. => LibreOffice could not convert this file.
Calibre n'a pas pu convertir ce fichier : {} => Calibre could not convert this file: {}
Format de tableur non géré : {} => Unsupported spreadsheet format: {}
Le document ne contient aucune page. => The document has no pages.
Impossible d'ouvrir le document : {} => Could not open the document: {}
Ce PDF est protégé par un mot de passe : retirez-le d'abord avec l'outil « Déverrouiller un PDF ». => This PDF is password-protected: remove the password first with the “Unlock a PDF” tool.
Indiquez les pages dans les réglages (exemple : 1-3, 7, 10-). => Enter the pages in the settings (example: 1-3, 7, 10-).
Aucune de ces pages n'existe : ce PDF en compte {}. => None of these pages exist: this PDF has {}.
Ce PDF ne contient aucune image à extraire. => This PDF contains no images to extract.
Ce PDF contient déjà du texte sélectionnable : rien à reconnaître. => This PDF already contains selectable text: there is nothing to recognize.
Aucun texte n'a été reconnu dans les pages scannées. => No text was recognized in the scanned pages.
Indiquez les plages dans les réglages (exemple : 1-3, 4-6, 7-). => Enter the ranges in the settings (example: 1-3, 4-6, 7-).
Toutes les pages seraient supprimées. => Every page would be deleted.
Indiquez le mot de passe du PDF dans les réglages. => Enter the PDF password in the settings.
Ce PDF n'est pas protégé : il n'y a rien à retirer. => This PDF is not protected: there is nothing to remove.
Pages non comprises : « {} » (exemple : 1-3, 7, 10-). => Pages not understood: “{}” (example: 1-3, 7, 10-).
Aucun sous-titre trouvé dans ce fichier. => No subtitles found in this file.
La création du PDF a échoué. => PDF creation failed.
Ce fichier ne contient aucune piste audio à transcrire. => This file has no audio track to transcribe.
L'audio est trop court pour être transcrit. => The audio is too short to be transcribed.
Aucune parole reconnue dans ce fichier. => No speech recognized in this file.
Impossible de télécharger le modèle de transcription « {} » (connexion Internet requise la première fois) : {} => Could not download the transcription model “{}” (an Internet connection is required the first time): {}
Aucun texte à lire dans ce fichier. => No text to read in this file.
La synthèse vocale a échoué. {} => Speech synthesis failed. {}
La synthèse vocale a échoué. => Speech synthesis failed.
Aucune adresse de page web. => No web page address.
Microsoft Edge est nécessaire pour les pages web. => Microsoft Edge is required for web pages.
La page n'a pas pu être enregistrée. => The page could not be saved.
La capture de la page a échoué. => The page capture failed.
Temps invalide : « {} » (exemples : 1:30 ou 90). => Invalid time: “{}” (examples: 1:30 or 90).
Aucune page valide dans « {} » (le document compte {} page(s)). => No valid page in “{}” (the document has {} page(s)).
Pages invalides : « {} » (exemple : 1-3, 5). => Invalid pages: “{}” (example: 1-3, 5).
FFmpeg est nécessaire pour enregistrer. => FFmpeg is required to record.
L'enregistrement est vide. => The recording is empty.
Un enregistrement est déjà en cours. => A recording is already in progress.
Choisissez un micro. => Choose a microphone.
L'enregistrement n'a pas pu démarrer. => The recording could not start.
L'enregistrement n'a pas pu démarrer : {} => The recording could not start: {}
Aucun enregistrement en cours. => No recording in progress.
Mot de passe incorrect. => Incorrect password.
7-Zip n'a pas pu traiter l'archive : {} => 7-Zip could not process the archive: {}
Base SQLite illisible : {} => Unreadable SQLite database: {}
Recherche sur YouTube impossible : {} => YouTube search failed: {}
Ce format audio ne peut pas contenir de pochette. => This audio format cannot hold cover art.
Connexion au site… => Connecting to the site…
Police illisible : {} => Unreadable font: {}
SVG illisible : {} => Unreadable SVG: {}
Image illisible ou format non reconnu : {} => Unreadable image or unrecognized format: {}
Compression (passe 1/2)… => Compressing (pass 1/2)…
Compression (passe 2/2)… => Compressing (pass 2/2)…
Fusion… => Merging…
Capture de l'image… => Capturing the frame…
LibreOffice ne sait pas produire ce format ({}). => LibreOffice cannot produce this format ({}).
LibreOffice n'a pas pu convertir ce fichier.{} => LibreOffice could not convert this file.{}
PDF illisible : {} => Unreadable PDF: {}
Sous-titres illisibles : {} => Unreadable subtitles: {}
Page inaccessible : {} => Page not accessible: {}

// ---------------------------------------------------------------- noms des fichiers produits
(converti) => (converted)
(compressé) => (compressed)
(pages) => (pages)
(pivoté) => (rotated)
(protégé) => (protected)
(déverrouillé) => (unlocked)
(filigrane) => (watermark)
(numéroté) => (numbered)
(cherchable) => (searchable)
(nettoyé) => (cleaned)
(détouré) => (cut out)
(contenu) => (content)
(icônes) => (icons)
(aperçu) => (preview)
(images) => (images)
(empreintes) => (checksums)
(infos) => (info)
(archive) => (archive)
(volumes) => (volumes)
(sous-titres) => (subtitles)
(fusion) => (merged)
(animation) => (animation)
(diaporama) => (slideshow)
(collage) => (collage)
(morceaux) => (pieces)
(logo) => (logo)
(bande-son) => (soundtrack)
(pochette) => (cover)
partie => part
page => page
pages => pages
image => image
Fichiers renommés => Renamed files
LISEZ-MOI => README
Pour reconstituer le fichier : gardez toutes les parties dans le même dossier, puis ouvrez la première (.7z.001) avec 7-Zip et choisissez « Extraire ». => To rebuild the file: keep all the parts in the same folder, then open the first one (.7z.001) with 7-Zip and choose “Extract”.
A coller dans la balise head => Paste into the head tag
texte => text
clé => key
valeur => value
Table des matières => Contents
Page {n} sur {total} => Page {n} of {total}

// ---------------------------------------------------------------- rapport d'informations
Rapport d'informations — {} => Information report — {}
— Média — => — Media —
— Image — => — Image —
— Document Office — => — Office document —
— Empreintes — => — Checksums —
Taille => Size
Type => Type
Créé le => Created
Modifié le => Modified
sans extension => no extension
Conteneur => Container
Durée => Duration
Débit total => Total bitrate
Pochette => Cover
im/s => fps
mono => mono
stéréo => stereo
{} canaux => {} channels
canaux inconnus => unknown channels
Dimensions => Dimensions
Mode de couleur => Color mode
Images (animation) => Frames (animation)
Profil de couleur => Color profile
Fabricant => Make
Appareil => Camera
Logiciel => Software
Auteur => Author
Prise de vue => Taken
Position GPS => GPS location
Position GPS : {}  ← retirée par l'outil « Nettoyer les métadonnées » => GPS location: {}  ← removed by the “Clean metadata” tool
ppp => dpi
Fichiers pris en charge => Supported files
CONFIDENTIEL => CONFIDENTIAL
Portez ce vieux whisky au juge blond qui fume. 0123456789 => The quick brown fox jumps over the lazy dog. 0123456789
Téléphone {} => Phone {}
présente => present
Protégé par un mot de passe : contenu illisible sans lui. => Password-protected: the content cannot be read without it.
Format de la 1re page => First page size
Sujet => Subject
Mots-clés => Keywords
Créé avec => Created with
Produit par => Produced by
Chiffré : oui (ouverture libre, restrictions possibles) => Encrypted: yes (opens freely, restrictions possible)
Texte sélectionnable => Selectable text
oui => yes
non => no
non (document scanné ? → « PDF cherchable ») => no (scanned document? → “Searchable PDF”)
Modifié par => Modified by
Révision => Revision
Fichiers => Files
… et {} autres => … and {} more
octets => bytes
# SHA-256 (vérifiable avec : certutil -hashfile NOM SHA256) => # SHA-256 (verify with: certutil -hashfile NAME SHA256)
"""

# Textes identiques en anglais (pour l'inventaire des textes non traduits).
_SAME = r"""
Image
Audio
Document
Animation
Archive
Archives
Ebook
Format
Page
Pages
Style
Position
Rotation
Volume
Action
Transparent
Large
Album
Date
Copyright
Version
Logo / illustration
Logo
— PDF —
— Archive —
Mobile (390 px)
QR code
GPU
CPU
Pages {}–{}
Page {}/{}…
Image {}/{}…
"""


def _parse(raw: str) -> dict[str, str]:
    out = {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        fr, sep, en = line.partition(" => ")
        if not sep:
            raise ValueError(f"Ligne de traduction invalide : {line!r}")
        out[fr.strip()] = en.strip()
    return out


EN: dict[str, str] = _parse(_EN)
SAME = {s.strip() for s in _SAME.strip().splitlines() if s.strip()}

# Gabarits : « {} » remplace n'importe quel texte ; les plus longs passent en premier.
PATTERNS = sorted(
    ((re.compile("^" + "(.+?)".join(re.escape(p) for p in k.split("{}")) + "$", re.S), v)
     for k, v in EN.items() if "{}" in k),
    key=lambda kv: -len(kv[0].pattern))

_CACHE: dict[str, str] = {}
_AUDIT = os.environ.get("CONVERTISSEUR_I18N_AUDIT")
_SEEN: set[str] = set()


def _part(s: str) -> str:
    """Morceau capturé par un gabarit : traduit s'il est connu, élément par élément pour une liste."""
    if s in EN:
        return EN[s]
    if ", " in s:
        return ", ".join(_tr(x) or x for x in s.split(", "))
    return _tr(s) or s


def _tr(s: str) -> str | None:
    if s in EN:
        return EN[s]
    if s != s.strip():                               # espaces autour : traduit le texte, garde les espaces
        t = _tr(s.strip())
        return None if t is None else s[:len(s) - len(s.lstrip())] + t + s[len(s.rstrip()):]
    for rx, tpl in PATTERNS:
        m = rx.match(s)
        if m:
            return tpl.format(*(_part(g) for g in m.groups()))
    return None


def tr(s, lang: str | None = None):
    """Traduit un texte de l'interface (inchangé en français ou s'il n'est pas connu)."""
    if not isinstance(s, str) or not s or (lang or LANG) != "en":
        return s
    if s in _CACHE:
        return _CACHE[s]
    t = _tr(s)
    if t is None:
        t = s
        if _AUDIT and s not in SAME and s not in _SEEN and re.search(r"[^\W\d_]{2}", s):
            _SEEN.add(s)
            try:
                with open(_AUDIT, "a", encoding="utf-8") as f:
                    f.write(s.replace("\n", "\\n") + "\n")
            except OSError:
                pass
    if len(_CACHE) < 20000:
        _CACHE[s] = t
    return t


def known(s: str) -> bool:
    """Vrai si le texte a une traduction (ou s'écrit pareil en anglais)."""
    return s in SAME or _tr(s) is not None


def dec(s: str) -> str:
    """Séparateur décimal : virgule en français, point en anglais."""
    return s.replace(".", ",") if LANG == "fr" else s


def colon() -> str:
    """Deux-points : précédé d'une espace en français."""
    return " : " if LANG == "fr" else ": "


def size(n: int) -> str:
    """Taille lisible (1,5 Mo / 1.5 MB)."""
    units = (("Go", "GB", 1 << 30), ("Mo", "MB", 1 << 20), ("Ko", "KB", 1 << 10))
    for fr, en, div in units:
        if n >= div:
            return dec(f"{n / div:.1f}") + " " + (en if LANG == "en" else fr)
    return f"{n} " + ("bytes" if LANG == "en" else "octets")


def report_line(line: str) -> str:
    """Ligne « Libellé : valeur » d'un rapport : libellé et valeur connue traduits."""
    if LANG != "en" or not line.strip():
        return line
    body = line.lstrip()
    t = _tr(body)
    if t is not None:
        return line[:len(line) - len(body)] + t
    m = re.match(r"^(\s*)(.+?)(\s*) : (.*)$", line, re.S)
    if not m:
        return line
    indent, label, pad, value = m.groups()
    t = _tr(label)
    if t is None:                                    # « Vidéo (eng) » : libellé suivi d'une précision
        mm = re.match(r"^(.+?)( \(.+\))$", label)
        t = (_tr(mm.group(1)) or mm.group(1)) + mm.group(2) if mm else label
    return f"{indent}{t}{pad}: {tr(value)}"


# ---------------------------------------------------------------- données envoyées à l'interface
def option(o: dict) -> dict:
    out = dict(o)
    for k in ("label", "placeholder", "section"):
        if k in out:
            out[k] = tr(out[k])
    kind = out.get("type")
    if not kind and out.get("id"):                   # option d'un assemblage : type de l'option de référence
        from .formats import OPTIONS
        kind = OPTIONS.get(out["id"], {}).get("type")
    if kind == "text" and isinstance(out.get("default"), str):
        out["default"] = tr(out["default"])
    if "choices" in out:
        out["choices"] = [[c[0], tr(c[1]), *c[2:]] for c in out["choices"]]
    return out


def options(d: dict) -> dict:
    return {k: option(v) for k, v in d.items()}


def preset(p: dict) -> dict:
    out = dict(p)
    out["gkey"] = p.get("group")                     # nom d'origine : sert de clé (couleurs, groupes ouverts)
    for k in ("label", "title", "desc", "group"):
        if k in out:
            out[k] = tr(out[k])
    if isinstance(out.get("open"), str):
        out["open"] = tr(out["open"])
    return out


def combine(d: dict) -> dict:
    out = {}
    for k, c in d.items():
        c = dict(c)
        c["label"], c["button"] = tr(c["label"]), tr(c["button"])
        c["options"] = [option(o) for o in c.get("options", [])]
        out[k] = c
    return out


def target(t: dict) -> dict:
    out = dict(t)
    out["label"], out["group"] = tr(t["label"]), tr(t["group"])
    out["base_label"] = tr(t.get("base"))
    if t.get("reason"):
        out["reason"] = tr(t["reason"])
    if t.get("options"):
        out["options"] = [option(o) for o in t["options"]]
    return out

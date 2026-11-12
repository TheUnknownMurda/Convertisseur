/* Langue de l'interface : le français est la langue de référence, l'anglais est traduit ici.
   t("Texte {n}", { n: 3 }) traduit puis remplace les {variables} ; tn() choisit le singulier ou le pluriel. */
(() => {
  "use strict";
  const LANG = document.documentElement.lang === "en" ? "en" : "fr";

  // Une entrée par ligne : « français => anglais ».
  const RAW = String.raw`
Tout format · 100 % local => Any format · 100% local
Rechercher un outil… => Search tools…
Rechercher un outil => Search tools
Outils => Tools
Convertisseur universel => Universal converter
Ajouter des fichiers => Add files
Collez un lien… => Paste a link…
Lien à télécharger => Link to download
Ajouter => Add
Le téléchargement passe par Internet ; la conversion reste sur cet ordinateur. À réserver aux contenus dont vous avez les droits (vos vidéos, licences libres…). => Downloading goes through the Internet; the conversion stays on this computer. Only for content you have the rights to (your own videos, free licenses…).
Lâchez pour ajouter => Drop to add
Les fichiers restent sur cet ordinateur. => Files stay on this computer.
Erreur {status} => Error {status}
Page web => Web page
Lien => Link
FICHIERS => FILES
MÊME FORMAT => SAME FORMAT
DOSSIER => FOLDER
TEXTE => TEXT
ICÔNES => ICONS
MORCEAUX => PIECES
RAPPORT => REPORT
Un fichier entre, il ressort converti => A file goes in, it comes out converted
o => B
Ko => KB
Mo => MB
Go => GB
{n} image => {n} frame
{n} images => {n} frames
{n} page => {n} page
{n} pages => {n} pages
protégé => protected
illisible ? => unreadable?
Échec de l'import => Import failed
Import annulé => Import cancelled
Collez une adresse complète, qui commence par https:// => Paste a full address, starting with https://
Analyse du lien… => Analyzing the link…
{n} éléments ajoutés depuis la liste de lecture. => {n} items added from the playlist.
Ce lien est déjà dans la liste. => This link is already in the list.
Collez un lien {site}… ({kind}) => Paste a {site} link… ({kind})
titre, album ou playlist => track, album or playlist
vidéo, Reel ou playlist => video, Reel or playlist
Collez un lien YouTube, Spotify, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo… => Paste a YouTube, Spotify, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo… link
Choisissez un format de sortie. => Choose an output format.
Rien à convertir : tout est déjà fait ou en cours. => Nothing to convert: everything is done or in progress.
Conversion terminée => Conversion complete
{n} fichier => {n} file
{n} fichiers => {n} files
{n} en cours => {n} in progress
{n} terminé => {n} done
{n} terminés => {n} done
{done} sur {n} terminé => {done} of {n} done
{done} sur {n} terminés => {done} of {n} done
Tout convertir ({n}) => Convert all ({n})
Tout est converti => All converted
Tout convertir => Convert all
Ajouter d'autres fichiers => Add more files
Ou convertir des fichiers de cet ordinateur => Or convert files from this computer
Cliquez pour parcourir, ou glissez-les n'importe où dans la fenêtre. => Click to browse, or drag them anywhere in the window.
Déposez vos fichiers ici => Drop your files here
Le format est reconnu tout seul et toutes les conversions possibles vous sont proposées. Les dossiers sont acceptés. => The format is detected automatically and every possible conversion is offered. Folders are accepted.
Ou cliquez pour les choisir. Les dossiers sont acceptés. => Or click to choose them. Folders are accepted.
Parcourir les fichiers => Browse files
Coller un lien => Paste a link
Déposez vos fichiers => Drop your files
Choisissez le format => Choose the format
Convertissez => Convert
Aucun envoi sur Internet : tout est converti sur cet ordinateur. => Nothing is uploaded: everything is converted on this computer.
Raccourcis populaires => Popular shortcuts
{label} avec {n} fichiers, dans l'ordre de la liste => {label} with {n} files, in list order
Assembler plusieurs fichiers de la liste en un seul => Combine several files of the list into one
Autres assemblages => Other combinations
Assembler… ({n}) => Combine… ({n})
Assembler les fichiers de la liste => Combine the files of the list
{n} fichiers, dans l'ordre de la liste => {n} files, in list order
Glisser pour réordonner => Drag to reorder
Choisir le format de sortie => Choose the output format
Réglages de cette conversion => Settings for this conversion
Réglages => Settings
Retirer de la liste => Remove from the list
Contenu en ligne => Online content
Étape intermédiaire : {fmt} => Intermediate step: {fmt}
Passe par {route} => Goes through {route}
Passe par : {route} => Goes through: {route}
Conversion directe => Direct conversion
en => to
Choisir… => Choose…
Import… => Importing…
Import… {p} % => Importing… {p}%
Aucune sortie => No output
Annuler => Cancel
Réessayer => Retry
Convertir => Convert
Format non reconnu : aucune conversion disponible pour ce type de fichier. => Unrecognized format: no conversion available for this type of file.
En attente d'un emplacement libre… => Waiting for a free slot…
{p} % => {p}%
−{p} % => −{p}%
Conversion… => Converting…
Échec de la conversion. => The conversion failed.
Conversion annulée. => Conversion cancelled.
Sera téléchargé depuis {site} puis converti en {target}. => Will be downloaded from {site}, then converted to {target}.
Sera téléchargé depuis {site} puis converti. => Will be downloaded from {site}, then converted.
le site => the site
En {n} étapes : => In {n} steps:
Terminé => Done
dossier => folder
Gain de taille par rapport à l'original => Size saved compared with the original
Ouvrir => Open
Afficher dans le dossier => Show in folder
Afficher ou masquer => Show or hide
Aucun réglage pour cette sortie. => No settings for this output.
Enregistrer ces réglages en favori => Save these settings as a favorite
Lien ou texte => Link or text
E-mail => Email
Téléphone => Phone
https://… ou n'importe quel texte => https://… or any text
Nom du réseau => Network name
ex. Maison => e.g. Home
Mot de passe => Password
Sécurité => Security
Aucune => None
Prénom => First name
Nom => Last name
Entreprise => Company
Site web => Website
Adresse => Address
nom@exemple.com => name@example.com
Objet => Subject
Numéro => Number
Petite => Small
Moyenne => Medium
Grande => Large
SVG (vectoriel) => SVG (vector)
Faible (plus compact) => Low (more compact)
Élevée => High
Maximale (logo par-dessus) => Maximum (logo on top)
Créer le QR code => Create the QR code
Apparence => Appearance
Couleur => Color
Fond => Background
Fond transparent => Transparent background
Taille => Size
Correction d'erreurs => Error correction
Code 128 (texte, chiffres) => Code 128 (text, digits)
EAN-13 (produits) => EAN-13 (products)
UPC-A (Amérique du Nord) => UPC-A (North America)
ISBN-13 (livres) => ISBN-13 (books)
ex. 590123412345 => e.g. 590123412345
Créer le code-barres => Create the barcode
Contenu => Content
EAN et UPC : la clé de contrôle (dernier chiffre) est calculée si vous ne la donnez pas. => EAN and UPC: the check digit (last digit) is calculated if you leave it out.
Tapez ou collez votre texte ici… => Type or paste your text here…
{n} caractère => {n} character
{n} caractères => {n} characters
Automatique => Automatic
Normale => Normal
Créer l'audio => Create the audio
Texte => Text
Voix => Voice
Vitesse => Speed
L'audio apparaît dans la liste ci-dessous. Vous pouvez aussi déposer un document (TXT, DOCX, PDF, EPUB…) pour le faire lire. => The audio appears in the list below. You can also drop a document (TXT, DOCX, PDF, EPUB…) to have it read aloud.
Chargement des micros… => Loading microphones…
Sans micro => No microphone
30 images/s => 30 fps
60 images/s (fluide) => 60 fps (smooth)
15 images/s (léger) => 15 fps (light)
Prêt => Ready
Arrêter et enregistrer => Stop and save
Démarrer l'enregistrement => Start recording
Démarrer l'enregistrement de l'écran => Start screen recording
Enregistrement en cours… => Recording…
Un autre enregistrement est en cours. => Another recording is in progress.
Finalisation du fichier… => Finishing the file…
Enregistré. => Saved.
Aucun micro détecté => No microphone detected
Micro => Microphone
Micro (facultatif) => Microphone (optional)
Fluidité => Smoothness
Le fichier MP3 est enregistré dans votre dossier de sortie. => The MP3 file is saved in your output folder.
Tout l'écran est filmé (tous les moniteurs). Le son de l'ordinateur n'est pas capté : seulement le micro choisi. => The whole screen is recorded (all monitors). The computer's own sound is not captured: only the chosen microphone.
Les conversions en cours ont été conservées. => Conversions in progress were kept.
{n} fichiers, dans l'ordre de la liste (glissez les lignes par la poignée à gauche pour changer l'ordre). => {n} files, in list order (drag the rows by the handle on the left to change the order).
1 fichier. => 1 file.
Créer => Create
Retirer => Remove
Rechercher un format… (ex. mp3, pdf, jpg) => Search formats… (e.g. mp3, pdf, jpg)
Rechercher un format => Search formats
Format de sortie => Output format
naviguer => navigate
Entrée => Enter
choisir => choose
Échap => Esc
fermer => close
{label} — passe par {route} => {label} — goes through {route}
Aucun format ne correspond. => No matching format.
Les plus utilisés => Most used
Aucun fichier prêt. => No file ready.
{n} fichier réglé sur {label}. => {n} file set to {label}.
{n} fichiers réglés sur {label}. => {n} files set to {label}.
Le nombre entre parenthèses indique combien de fichiers acceptent ce format. => The number in brackets shows how many files accept this format.
Fermer => Close
Dossier d'enregistrement => Save folder
Sélecteur de dossier indisponible. => Folder picker unavailable.
Changer… => Change…
Enregistrer à côté du fichier d'origine (fichiers choisis avec « Parcourir ») => Save next to the original file (files chosen with “Browse”)
Ouvrir le dossier à la fin de chaque conversion => Open the folder after each conversion
Accélération matérielle : vidéos ({gpu}) et transcription (CUDA) => Hardware acceleration: videos ({gpu}) and transcription (CUDA)
Accélération matérielle : vidéos ({gpu}) => Hardware acceleration: videos ({gpu})
Accélération matérielle (aucune carte compatible détectée) => Hardware acceleration (no compatible graphics card detected)
Conversions simultanées => Simultaneous conversions
Session du navigateur pour les sites qui exigent une connexion (Instagram, Facebook…) => Browser session for sites that require signing in (Instagram, Facebook…)
Aucune (contenus publics seulement) => None (public content only)
Module de téléchargement => Download module
yt-dlp non installé => yt-dlp not installed
Mise à jour… => Updating…
yt-dlp est à jour ({v}). => yt-dlp is up to date ({v}).
Mettre à jour => Update
Moteurs installés => Installed engines
vidéo, audio, GIF => video, audio, GIF
mise en page HTML → PDF => HTML → PDF layout
archives RAR, 7Z, ISO… => RAR, 7Z, ISO… archives
téléchargement YouTube, SoundCloud, Instagram, Facebook… => YouTube, SoundCloud, Instagram, Facebook… downloads
installez Node.js pour YouTube => install Node.js for YouTube
Voix Windows => Windows voices
lecture vocale => read aloud
OCR Windows => Windows OCR
reconnaissance de texte ({langs}) => text recognition ({langs})
reconnaissance de texte => text recognition
transcription de la parole ({device}) => speech transcription ({device})
transcription de la parole => speech transcription
carte NVIDIA => NVIDIA card
processeur => processor
— modèle(s) : {list} => — model(s): {list}
— modèle téléchargé au 1er usage => — model downloaded on first use
Raccourcis => Shortcuts
Raccourci « Convertisseur » créé sur le Bureau (vous pouvez y glisser des fichiers). => “Convertisseur” shortcut created on the desktop (you can drop files on it).
Raccourci sur le Bureau => Desktop shortcut
Ajouté au menu clic droit → « Envoyer vers » de l'Explorateur. => Added to File Explorer's right-click → “Send to” menu.
Menu « Envoyer vers » => “Send to” menu
Enregistrer => Save
Réglages enregistrés. => Settings saved.
Langue => Language
Automatique (langue de Windows) => Automatic (Windows language)
Thème => Theme
Automatique (comme Windows) => Automatic (same as Windows)
Clair => Light
Sombre => Dark
Passer au thème clair => Switch to the light theme
Passer au thème sombre => Switch to the dark theme
déplacé ou supprimé => moved or deleted
Aucune conversion pour l'instant. => No conversions yet.
Historique des conversions => Conversion history
Effacer l'historique => Clear history
Historique effacé. => History cleared.
depuis {names} => from {names}
Favoris => Favorites
Favori : {label} => Favorite: {label}
Règle les fichiers compatibles sur {target} avec vos réglages enregistrés. => Sets compatible files to {target} with your saved settings.
Nouveau favori => New favorite
Nom du favori (il apparaîtra dans la barre latérale) : => Favorite name (it will appear in the sidebar):
Favori « {label} » ajouté. => Favorite “{label}” added.
Le format est reconnu tout seul => The format is detected automatically
Supprimer ce favori => Delete this favorite
Aucun outil ne correspond. => No matching tool.
« Tous les fichiers » accepte tout. => “All files” accepts everything.
Atelier universel => Universal workshop
Outil => Tool
FFmpeg introuvable => FFmpeg not found
Documents Office => Office documents
Non installé => Not installed
Dossier de sortie => Output folder
Ouvrir le dossier où sont enregistrés les fichiers convertis => Open the folder where converted files are saved
Historique => History
Tout convertir en… => Convert all to…
Vider la liste => Clear the list
Capture => Screenshot
Image collée depuis le presse-papiers. => Image pasted from the clipboard.
{n} fichier ajouté. => {n} file added.
{n} fichiers ajoutés. => {n} files added.
Serveur injoignable : {msg} => Server unreachable: {msg}
`;

  const EN = {};
  for (const line of RAW.split("\n")) {
    const at = line.indexOf(" => ");
    if (at > 0) EN[line.slice(0, at).trim()] = line.slice(at + 4).trim();
  }

  const fill = (s, vars) => (vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s);
  /** Texte traduit (inchangé en français ou s'il n'est pas connu), avec ses {variables} remplacées. */
  function t(s, vars) {
    return fill(LANG === "en" && EN[s] !== undefined ? EN[s] : s, vars);
  }
  /** Singulier ou pluriel selon n (français : 0 et 1 au singulier ; anglais : seulement 1). */
  function tn(n, one, many, vars) {
    const single = LANG === "en" ? n === 1 : n < 2;
    return t(single ? one : many, { n, ...vars });
  }
  /** Traduit le HTML fixe de la page (textes et attributs title, placeholder, aria-label). */
  function translateDom(root) {
    if (LANG === "fr") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const key = n.nodeValue.replace(/\s+/g, " ").trim();
      if (key && EN[key] !== undefined) n.nodeValue = n.nodeValue.replace(/\S[\s\S]*\S|\S/, EN[key]);
    }
    for (const el of root.querySelectorAll("[title],[placeholder],[aria-label]")) {
      for (const a of ["title", "placeholder", "aria-label"]) {
        const v = el.getAttribute(a);
        if (v && EN[v.trim()] !== undefined) el.setAttribute(a, EN[v.trim()]);
      }
    }
  }

  window.I18N = { lang: LANG, locale: LANG === "en" ? "en-CA" : "fr-CA", t, tn, translateDom, has: (s) => EN[s] !== undefined };
})();

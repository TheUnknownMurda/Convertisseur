; Convertisseur : installateur Windows (Inno Setup 6.7 ou plus récent).
; Compiler avec installer\build.ps1, qui reprend la version de convertisseur\__init__.py.
;
; L'application est installée pour l'utilisateur courant (sans droits administrateur), puis
; l'assistant propose les logiciels nécessaires ; ceux déjà présents sont détectés et décochés.
; Les installations sont faites par installer\setup.ps1 (winget, pip) et notées dans installation.log.

#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif
#define AppName "Convertisseur"
#define RepoUrl "https://github.com/TheUnknownMurda/Convertisseur"
#define PowerShell "{sys}\WindowsPowerShell\v1.0\powershell.exe"
; guillemets simples : les guillemets doublés restent tels quels pour le paramètre Inno
#define Step '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\installer\setup.ps1"" -Step'

[Setup]
AppId={{6E1F3A52-7C4B-4D9E-A8B1-2F5C9D3E7A41}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=TheUnknownMurda
AppPublisherURL={#RepoUrl}
AppSupportURL={#RepoUrl}/issues
AppUpdatesURL={#RepoUrl}/releases
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DisableWelcomePage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
WizardStyle=modern dynamic
WizardBackColor=#f3f2ee
WizardBackColorDynamicDark=#101115
WizardImageFile=assets\wizard-light-164.bmp,assets\wizard-light-246.bmp,assets\wizard-light-328.bmp
WizardImageFileDynamicDark=assets\wizard-dark-164.bmp,assets\wizard-dark-246.bmp,assets\wizard-dark-328.bmp
WizardSmallImageFile=assets\small-light-55.bmp,assets\small-light-83.bmp,assets\small-light-110.bmp
WizardSmallImageFileDynamicDark=assets\small-dark-55.bmp,assets\small-dark-83.bmp,assets\small-dark-110.bmp
SetupIconFile=..\web\logo.ico
UninstallDisplayIcon={app}\web\logo.ico
UninstallDisplayName={#AppName}
OutputDir=..\dist
OutputBaseFilename=Convertisseur-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
ShowLanguageDialog=no

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Messages]
WelcomeLabel1=Bienvenue dans l'installation de Convertisseur
WelcomeLabel2=Convertisseur transforme vidéos, musiques, images, PDF, documents, ebooks et bien plus, directement sur cet ordinateur.%n%nL'assistant installe l'application puis vous propose les logiciels dont elle a besoin : Python, FFmpeg, LibreOffice, Calibre… Ceux qui sont déjà présents sont détectés automatiquement.%n%nUne connexion Internet est nécessaire.
SelectComponentsLabel2=Cochez ce qu'il faut installer. Ce qui est déjà sur cet ordinateur est décoché et marqué « déjà installé ».%nWindows demandera une seule autorisation pour LibreOffice, Calibre, 7-Zip et Node.js.
FinishedHeadingLabel=Convertisseur est installé
FinishedLabel=Convertisseur est prêt : vous le trouverez dans le menu Démarrer.

[Types]
Name: "full"; Description: "Installation complète (recommandée)"
Name: "custom"; Description: "Installation personnalisée"; Flags: iscustom

[Components]
Name: "app"; Description: "Convertisseur"; Types: full custom; Flags: fixed
Name: "python"; Description: "Python 3.13 et modules Python (obligatoire)"; Types: full custom; Flags: fixed; ExtraDiskSpaceRequired: 650000000
Name: "ffmpeg"; Description: "FFmpeg : vidéo, audio et GIF"; Types: full; ExtraDiskSpaceRequired: 210000000
Name: "libreoffice"; Description: "LibreOffice : documents Word, Excel et PowerPoint"; Types: full; ExtraDiskSpaceRequired: 1100000000
Name: "calibre"; Description: "Calibre : ebooks (EPUB, MOBI, AZW3…)"; Types: full; ExtraDiskSpaceRequired: 520000000
Name: "sevenzip"; Description: "7-Zip : archives RAR, 7Z et ISO"; Types: full; ExtraDiskSpaceRequired: 6000000
Name: "node"; Description: "Node.js : téléchargements depuis YouTube"; Types: full; ExtraDiskSpaceRequired: 100000000
Name: "gpu"; Description: "Accélération NVIDIA de la transcription"; Types: full; ExtraDiskSpaceRequired: 1800000000
Name: "model"; Description: "Modèle de transcription « Équilibré » (fonctionne hors ligne)"; Types: full; ExtraDiskSpaceRequired: 490000000

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "sendto"; Description: "Ajouter Convertisseur au menu « Envoyer vers » (clic droit sur un fichier)"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Convertisseur.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements-lock.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\convertisseur\*.py"; DestDir: "{app}\convertisseur"; Flags: ignoreversion recursesubdirs
Source: "..\web\*"; DestDir: "{app}\web"; Excludes: "_t_*"; Flags: ignoreversion recursesubdirs
Source: "setup.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; IconFilename: "{app}\web\logo.ico"; Comment: "Convertir vos fichiers sur cet ordinateur"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; IconFilename: "{app}\web\logo.ico"; Comment: "Convertir vos fichiers sur cet ordinateur"; Tasks: desktopicon
Name: "{usersendto}\{#AppName}"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; IconFilename: "{app}\web\logo.ico"; Comment: "Convertir ces fichiers"; Tasks: sendto

[Run]
Filename: "{#PowerShell}"; Parameters: "{#Step} python"; StatusMsg: "Installation de Python et des modules Python (quelques minutes)…"; Flags: runhidden waituntilterminated
Filename: "{#PowerShell}"; Parameters: "{#Step} ffmpeg"; StatusMsg: "Installation de FFmpeg…"; Components: ffmpeg; Flags: runhidden waituntilterminated
Filename: "{#PowerShell}"; Parameters: "{#Step} tools -Names {code:MachineTools}"; StatusMsg: "{code:ToolsStatus}"; Check: AnyMachineTool; Flags: runhidden waituntilterminated
Filename: "{#PowerShell}"; Parameters: "{#Step} gpu"; StatusMsg: "Installation de l'accélération NVIDIA (1,8 Go à télécharger)…"; Components: gpu; Flags: runhidden waituntilterminated
Filename: "{#PowerShell}"; Parameters: "{#Step} model"; StatusMsg: "Téléchargement du modèle de transcription (480 Mo)…"; Components: model; Flags: runhidden waituntilterminated
Filename: "{#PowerShell}"; Parameters: "{#Step} summary"; StatusMsg: "Vérification…"; Flags: runhidden waituntilterminated
Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; Description: "Lancer Convertisseur"; Check: PythonReady; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\modeles"
Type: filesandordirs; Name: "{app}\bin"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\convertisseur\__pycache__"
Type: filesandordirs; Name: "{app}\convertisseur\engines\__pycache__"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\historique.json"
Type: files; Name: "{app}\convertisseur.log"
Type: files; Name: "{app}\installation.log"
Type: files; Name: "{app}\installation-resume.txt"
Type: files; Name: "{app}\.instance.json"
Type: filesandordirs; Name: "{localappdata}\Convertisseur"
Type: dirifempty; Name: "{app}"

[Code]
const
  IdxFFmpeg = 2;
  IdxLibreOffice = 3;
  IdxCalibre = 4;
  Idx7Zip = 5;
  IdxNode = 6;
  IdxGpu = 7;
  IdxModel = 8;

{ PATH du processus + PATH enregistré (des logiciels ont pu être installés depuis l'ouverture de session) }
function PathList: String;
var
  S: String;
begin
  Result := GetEnv('PATH');
  if RegQueryStringValue(HKCU, 'Environment', 'Path', S) then
    Result := Result + ';' + S;
  if RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', S) then
    Result := Result + ';' + S;
end;

function OnPath(const Exe: String): Boolean;
begin
  Result := FileSearch(Exe, PathList) <> '';
end;

function InProgramFiles(const Rel: String): Boolean;
begin
  Result := FileExists(ExpandConstant('{commonpf64}\') + Rel) or FileExists(ExpandConstant('{commonpf32}\') + Rel)
    or FileExists(ExpandConstant('{localappdata}\') + Rel);
end;

function HasFFmpeg: Boolean;
begin
  Result := OnPath('ffmpeg.exe') or FileExists(ExpandConstant('{localappdata}\Microsoft\WinGet\Links\ffmpeg.exe'));
end;

function HasLibreOffice: Boolean;
begin
  Result := InProgramFiles('LibreOffice\program\soffice.exe');
end;

function HasCalibre: Boolean;
begin
  Result := InProgramFiles('Calibre2\ebook-convert.exe') or InProgramFiles('Calibre\ebook-convert.exe');
end;

function Has7Zip: Boolean;
begin
  Result := InProgramFiles('7-Zip\7z.exe');
end;

function HasNode: Boolean;
begin
  Result := OnPath('node.exe') or InProgramFiles('nodejs\node.exe');
end;

function HasNvidia: Boolean;
begin
  Result := FileExists(ExpandConstant('{sys}\nvidia-smi.exe'));
end;

function HasModel: Boolean;
begin
  Result := DirExists(AddBackslash(WizardDirValue) + 'modeles\whisper\models--Systran--faster-whisper-small');
end;

{ Ce qui est déjà là est décoché d'emblée }
procedure InitializeWizard;
var
  Off: String;
begin
  Off := '';
  if HasFFmpeg then Off := Off + ',!ffmpeg';
  if HasLibreOffice then Off := Off + ',!libreoffice';
  if HasCalibre then Off := Off + ',!calibre';
  if Has7Zip then Off := Off + ',!sevenzip';
  if HasNode then Off := Off + ',!node';
  if not HasNvidia then Off := Off + ',!gpu';
  if HasModel then Off := Off + ',!model';
  if Off <> '' then
    WizardSelectComponents(Copy(Off, 2, Length(Off)));
end;

procedure Mark(Index: Integer; Installed: Boolean);
begin
  if Installed then
    WizardForm.ComponentsList.ItemSubItem[Index] := 'déjà installé';
end;

function MachineTools(Param: String): String;
begin
  Result := '';
  if WizardIsComponentSelected('libreoffice') then Result := Result + ',libreoffice';
  if WizardIsComponentSelected('calibre') then Result := Result + ',calibre';
  if WizardIsComponentSelected('sevenzip') then Result := Result + ',sevenzip';
  if WizardIsComponentSelected('node') then Result := Result + ',node';
  if Result <> '' then
    Delete(Result, 1, 1);
end;

function AnyMachineTool: Boolean;
begin
  Result := MachineTools('') <> '';
end;

function ToolsStatus(Param: String): String;
var
  Names: String;
begin
  Names := '';
  if WizardIsComponentSelected('libreoffice') then Names := Names + ', LibreOffice';
  if WizardIsComponentSelected('calibre') then Names := Names + ', Calibre';
  if WizardIsComponentSelected('sevenzip') then Names := Names + ', 7-Zip';
  if WizardIsComponentSelected('node') then Names := Names + ', Node.js';
  Delete(Names, 1, 2);
  Result := 'Installation de ' + Names + '… (Windows peut demander une autorisation)';
end;

function PythonReady: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\.venv\Scripts\pythonw.exe'));
end;

function SummaryValue(const Lines: TArrayOfString; const Key: String): String;
var
  I: Integer;
begin
  Result := '';
  for I := 0 to GetArrayLength(Lines) - 1 do
    if Pos(Key + '=', Lines[I]) = 1 then
    begin
      Result := Copy(Lines[I], Length(Key) + 2, MaxInt);
      Exit;
    end;
end;

procedure CheckTool(const Lines: TArrayOfString; const Component, Key, Name: String; var Missing: String);
begin
  if WizardIsComponentSelected(Component) and (SummaryValue(Lines, Key) <> 'ok') then
    Missing := Missing + #13#10 + '• ' + Name;
end;

{ Dernière page : ce qui n'a pas pu être installé }
procedure ShowSummary;
var
  Lines: TArrayOfString;
  Missing, Text: String;
begin
  if not LoadStringsFromFile(ExpandConstant('{app}\installation-resume.txt'), Lines) then
    Exit;
  Missing := '';
  if SummaryValue(Lines, 'python') <> 'ok' then
    Missing := Missing + #13#10 + '• Python et ses modules : relancez l''installateur ou exécutez Convertisseur.bat';
  CheckTool(Lines, 'ffmpeg', 'ffmpeg', 'FFmpeg', Missing);
  CheckTool(Lines, 'libreoffice', 'libreoffice', 'LibreOffice', Missing);
  CheckTool(Lines, 'calibre', 'calibre', 'Calibre', Missing);
  CheckTool(Lines, 'sevenzip', 'sevenzip', '7-Zip', Missing);
  CheckTool(Lines, 'node', 'node', 'Node.js', Missing);
  if Missing = '' then
    Text := 'Tous les logiciels choisis sont prêts.'
  else
    Text := 'À vérifier :' + Missing + #13#10#13#10 + 'Détails dans installation.log, dans le dossier de l''application.';
  WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 + Text;
  WizardForm.FinishedLabel.AdjustHeight;
  WizardForm.RunList.Top := WizardForm.FinishedLabel.Top + WizardForm.FinishedLabel.Height + ScaleY(16);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectComponents then
  begin
    Mark(IdxFFmpeg, HasFFmpeg);
    Mark(IdxLibreOffice, HasLibreOffice);
    Mark(IdxCalibre, HasCalibre);
    Mark(Idx7Zip, Has7Zip);
    Mark(IdxNode, HasNode);
    Mark(IdxModel, HasModel);
    if not HasNvidia then
      WizardForm.ComponentsList.ItemSubItem[IdxGpu] := 'aucune carte NVIDIA';
  end
  else if CurPageID = wpFinished then
    ShowSummary;
end;

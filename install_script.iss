; Housoft Meta-Automation — Inno Setup installer script.
; Build:  ISCC.exe install_script.iss   (after PyInstaller has produced dist\HousoftMeta\)
; Output: HousoftMeta_Setup.exe in the project root.

[Setup]
AppName=Housoft Meta
AppId={{8B6E2A1A-7C31-4F44-9A20-HOUSOFTMETA01}}
AppVersion=1.0.1
AppPublisher=James (Workana)
DefaultDirName={localappdata}\HousoftMeta
DefaultGroupName=Housoft Meta
OutputDir=.
OutputBaseFilename=HousoftMeta_Setup
UninstallDisplayIcon={app}\HousoftMeta.exe
UninstallDisplayName=Housoft Meta
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=auto
DisableProgramGroupPage=yes
WizardStyle=modern
ShowLanguageDialog=yes
InfoBeforeFile=LEIA-ME.txt

[Languages]
Name: "brazilian"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

[Files]
; PyInstaller bundle — the frozen Python app + its private _internal/ runtime.
Source: "dist\HousoftMeta\HousoftMeta.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\HousoftMeta\_internal\*";     DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Project data — these live next to the .exe (not inside _internal) so users
; can edit them, add their own template captures, etc.
Source: "templates\*.png";        DestDir: "{app}\templates"; Flags: ignoreversion
Source: "config\schedule.json";   DestDir: "{app}\config";    Flags: onlyifdoesntexist
Source: "LEIA-ME.txt";            DestDir: "{app}";            Flags: ignoreversion

; First-run .env (placeholder values, user fills in ANTHROPIC_API_KEY).
; onlyifdoesntexist preserves the user's edits on re-install.
Source: ".env.example";           DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

[Dirs]
Name: "{app}\logs"
Name: "{app}\config"
Name: "{app}\templates"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueName: "HousoftMeta"; ValueType: String; \
    ValueData: """{app}\HousoftMeta.exe"""; \
    Tasks: autostart; Flags: uninsdeletevalue

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart";   Description: "Iniciar o Housoft Meta junto com o Windows"; GroupDescription: "Inicializacao:"

[Icons]
Name: "{group}\Housoft Meta";            Filename: "{app}\HousoftMeta.exe"; WorkingDir: "{app}"
Name: "{group}\Pasta de Instalacao";     Filename: "{app}"
Name: "{group}\LEIA-ME";                 Filename: "{app}\LEIA-ME.txt"
Name: "{group}\Desinstalar Housoft Meta"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Housoft Meta";      Filename: "{app}\HousoftMeta.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\LEIA-ME.txt";      Description: "Abrir instrucoes (LEIA-ME)";   Flags: shellexec postinstall unchecked skipifsilent nowait
Filename: "{app}\HousoftMeta.exe";  Description: "Iniciar o Housoft Meta agora"; Flags: postinstall unchecked skipifsilent nowait

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"

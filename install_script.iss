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

; ─── Custom wizard: ask the user for their Anthropic API key, then patch .env ──
[Code]
var
  ApiKeyPage: TWizardPage;
  ApiKeyEdit: TPasswordEdit;
  ApiKeyLink: TNewStaticText;

procedure ApiKeyLinkClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', 'https://console.anthropic.com/', '', '', SW_SHOW, ewNoWait, ErrorCode);
end;

procedure InitializeWizard();
var
  IntroLabel: TNewStaticText;
  EditLabel: TNewStaticText;
  HintLabel: TNewStaticText;
begin
  ApiKeyPage := CreateCustomPage(
    wpSelectTasks,
    'Chave da API Anthropic',
    'Cole sua chave Claude para o reconhecimento de tela do Housoft.'
  );

  IntroLabel := TNewStaticText.Create(ApiKeyPage);
  IntroLabel.Parent := ApiKeyPage.Surface;
  IntroLabel.Caption :=
    'O Housoft Meta usa a API da Anthropic (Claude) para identificar os' + #13#10 +
    'botoes do Housoft em qualquer resolucao de tela. Sem a chave o robo' + #13#10 +
    'nao consegue clicar com precisao.';
  IntroLabel.AutoSize := True;
  IntroLabel.Top := 8;
  IntroLabel.Left := 0;

  ApiKeyLink := TNewStaticText.Create(ApiKeyPage);
  ApiKeyLink.Parent := ApiKeyPage.Surface;
  ApiKeyLink.Caption := 'Obter uma chave em https://console.anthropic.com/';
  ApiKeyLink.Font.Color := clBlue;
  ApiKeyLink.Font.Style := [fsUnderline];
  ApiKeyLink.Cursor := crHand;
  ApiKeyLink.OnClick := @ApiKeyLinkClick;
  ApiKeyLink.AutoSize := True;
  ApiKeyLink.Top := IntroLabel.Top + IntroLabel.Height + 16;
  ApiKeyLink.Left := 0;

  EditLabel := TNewStaticText.Create(ApiKeyPage);
  EditLabel.Parent := ApiKeyPage.Surface;
  EditLabel.Caption := 'ANTHROPIC_API_KEY (comeca com "sk-ant-"):';
  EditLabel.AutoSize := True;
  EditLabel.Top := ApiKeyLink.Top + ApiKeyLink.Height + 18;
  EditLabel.Left := 0;

  ApiKeyEdit := TPasswordEdit.Create(ApiKeyPage);
  ApiKeyEdit.Parent := ApiKeyPage.Surface;
  ApiKeyEdit.Top := EditLabel.Top + EditLabel.Height + 4;
  ApiKeyEdit.Left := 0;
  ApiKeyEdit.Width := ApiKeyPage.SurfaceWidth - 20;

  HintLabel := TNewStaticText.Create(ApiKeyPage);
  HintLabel.Parent := ApiKeyPage.Surface;
  HintLabel.Caption :=
    'Pode deixar em branco e editar depois em:' + #13#10 +
    '   %LOCALAPPDATA%\HousoftMeta\.env';
  HintLabel.AutoSize := True;
  HintLabel.Top := ApiKeyEdit.Top + ApiKeyEdit.Height + 14;
  HintLabel.Left := 0;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ApiKeyPage.ID then begin
    // Allow blank (user will fill in later); only warn on obviously bad input.
    if (Length(ApiKeyEdit.Text) > 0) and (Pos('sk-ant-', ApiKeyEdit.Text) <> 1) then begin
      if MsgBox(
          'A chave normalmente comeca com "sk-ant-". A chave digitada nao parece valida.' + #13#10 +
          'Deseja continuar mesmo assim?',
          mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
end;

procedure PatchEnvFile(NewKey: String);
var
  Lines: TArrayOfString;
  I: Integer;
  EnvPath: String;
  Patched: Boolean;
begin
  EnvPath := ExpandConstant('{app}\.env');
  if not FileExists(EnvPath) then Exit;
  if not LoadStringsFromFile(EnvPath, Lines) then Exit;

  Patched := False;
  for I := 0 to GetArrayLength(Lines) - 1 do begin
    if Pos('ANTHROPIC_API_KEY=', Lines[I]) = 1 then begin
      Lines[I] := 'ANTHROPIC_API_KEY=' + NewKey;
      Patched := True;
    end;
  end;
  // If the line didn't exist (custom .env from previous install), append it.
  if not Patched then begin
    SetArrayLength(Lines, GetArrayLength(Lines) + 1);
    Lines[GetArrayLength(Lines) - 1] := 'ANTHROPIC_API_KEY=' + NewKey;
  end;

  SaveStringsToFile(EnvPath, Lines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    if Length(ApiKeyEdit.Text) > 0 then
      PatchEnvFile(ApiKeyEdit.Text);
  end;
end;

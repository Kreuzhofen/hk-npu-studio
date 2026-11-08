#ifndef AppName
  #error AppName define missing. Run tools/build_installer.py.
#endif
#ifndef AppVersion
  #error AppVersion define missing. Run tools/build_installer.py.
#endif
#ifndef Publisher
  #error Publisher define missing. Run tools/build_installer.py.
#endif
#ifndef ExecutableName
  #error ExecutableName define missing. Run tools/build_installer.py.
#endif

[Setup]
AppId={{8D9D455C-4C15-4A61-9685-21F67C5D4A44}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName=HK NPU STUDIO 2.1.0 – Phoenix Evolution
AppPublisher={#Publisher}
AppCopyright=© 2026 Holger Kreuzhofen
DefaultDirName={localappdata}\Programs\HK NPU STUDIO
DefaultGroupName={#AppName}
OutputDir=..\dist\installer
OutputBaseFilename=HKNPUStudio-{#AppVersion}-ARM64-Setup
SetupIconFile=..\assets\brand\icons\app.ico
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=arm64
ArchitecturesInstallIn64BitMode=arm64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#ExecutableName}
WizardStyle=modern
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
english.NPUCheckFailed=Qualcomm Snapdragon X NPU Hardware Requirement Check Failed:%n%nHK NPU STUDIO requires a Qualcomm Snapdragon X Series processor with Hexagon HTP NPU and active FastRPC driver (qcadsprpc).%n%nThe required Qualcomm FastRPC service was not detected on this system.%nSetup cannot continue without compatible Qualcomm NPU hardware.
german.NPUCheckFailed=Qualcomm Snapdragon X NPU Hardware-Voraussetzungsprüfung fehlgeschlagen:%n%nHK NPU STUDIO erfordert einen Qualcomm Snapdragon X Prozessor mit Hexagon HTP NPU und aktivem FastRPC-Treiber (qcadsprpc).%n%nDer erforderliche Qualcomm FastRPC-Dienst wurde auf diesem System nicht gefunden.%nDie Installation kann auf inkompatibler Hardware nicht fortgesetzt werden.
spanish.NPUCheckFailed=Error en la verificación de hardware Qualcomm Snapdragon X NPU:%n%nHK NPU STUDIO requiere un procesador Qualcomm Snapdragon X Series con NPU Hexagon HTP y controlador FastRPC activo (qcadsprpc).%n%nNo se detectó el servicio Qualcomm FastRPC requerido en este sistema.%nLa instalación no puede continuar sin hardware Qualcomm NPU compatible.

[Messages]
english.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
english.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nSelect the installation language:
english.WelcomeLabel1=Welcome to HK NPU STUDIO
english.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nIndependent open-source project for Windows on Snapdragon. Not an official Qualcomm product.%n%n© 2026 Holger Kreuzhofen
english.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution has been installed successfully
english.FinishedLabel=Setup has finished installing HK NPU STUDIO 2.1.0 – Phoenix Evolution.

german.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
german.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nInstallationssprache auswählen:
german.WelcomeLabel1=Willkommen bei HK NPU STUDIO
german.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nUnabhängiges Open-Source-Projekt für Windows auf Snapdragon. Kein offizielles Qualcomm-Produkt.%n%n© 2026 Holger Kreuzhofen
german.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution wurde erfolgreich installiert
german.FinishedLabel=Die Installation von HK NPU STUDIO 2.1.0 – Phoenix Evolution wurde erfolgreich abgeschlossen.

spanish.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
spanish.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nSeleccione el idioma de instalación:
spanish.WelcomeLabel1=Bienvenido a HK NPU STUDIO
spanish.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nProyecto independiente de código abierto para Windows en Snapdragon. No es un producto oficial de Qualcomm.%n%n© 2026 Holger Kreuzhofen
spanish.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution se ha instalado correctamente
spanish.FinishedLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution se ha instalado correctamente.

[Files]
Source: "..\dist\HKNPUStudio\*"; DestDir: "{app}"; Excludes: "output\*,models\photo_restore\*,models\photo_restore_context\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExecutableName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExecutableName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\{#ExecutableName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  DriverFound: Boolean;
  IgnoreCheck: Boolean;
  I: Integer;
begin
  Result := True;
  IgnoreCheck := False;
  for I := 1 to ParamCount do
  begin
    if CompareText(ParamStr(I), '/IGNORENPUCHECK') = 0 then
      IgnoreCheck := True;
  end;

  DriverFound := RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\qcadsprpc');
  if (not DriverFound) and (not IgnoreCheck) then
  begin
    MsgBox(CustomMessage('NPUCheckFailed'), mbCriticalError, MB_OK);
    Result := False;
    Exit;
  end;
end;

procedure InitializeLanguagePreferences;
var
  PreferencesDir: String;
  PreferencesPath: String;
  LegacyPreferencesPath: String;
  Language: String;
  PreferencesJson: String;
begin
  PreferencesDir := ExpandConstant('{localappdata}\HK NPU STUDIO\data');
  PreferencesPath := AddBackslash(PreferencesDir) + 'preferences.json';
  if FileExists(PreferencesPath) then
    Exit;

  LegacyPreferencesPath := ExpandConstant(
    '{localappdata}\Snapdragon AI Studio\data\preferences.json'
  );
  if FileExists(LegacyPreferencesPath) then
  begin
    if ForceDirectories(PreferencesDir) then
      FileCopy(LegacyPreferencesPath, PreferencesPath, False);
    if FileExists(PreferencesPath) then
      Exit;
  end;

  Language := 'Deutsch';
  if ActiveLanguage = 'english' then
    Language := 'English'
  else if ActiveLanguage = 'spanish' then
    Language := 'Espa\u00f1ol';

  if ForceDirectories(PreferencesDir) then
  begin
    PreferencesJson := '{"language":"' + Language + '"}';
    SaveStringToFile(PreferencesPath, PreferencesJson, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    InitializeLanguagePreferences;
end;

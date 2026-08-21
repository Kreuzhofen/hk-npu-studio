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
AppVerName=Snapdragon AI Studio 2.0 RC2
AppPublisher={#Publisher}
AppCopyright=© 2026 Holger Kreuzhofen
DefaultDirName={localappdata}\Programs\Snapdragon AI Studio
DefaultGroupName={#AppName}
OutputDir=..\dist\installer
OutputBaseFilename=SnapdragonAIStudio-{#AppVersion}-ARM64-Setup
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

[Messages]
english.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC2
english.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 2%nSelect the installation language:
english.WelcomeLabel1=Welcome to Snapdragon AI Studio
english.WelcomeLabel2=Phoenix Engine · Version 2.0 RC2%n%nProfessional local AI platform for image generation and%nSnapdragon NPU acceleration on Windows on ARM.%n%nPre-release version for testing and evaluation purposes.%n%nIndependent open-source project for Windows on Snapdragon. Not an official Qualcomm product.%n%n© 2026 Holger Kreuzhofen
english.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC2 has been installed successfully
english.FinishedLabel=Setup has finished installing Snapdragon AI Studio 2.0 RC2.%n%nThank you for testing Snapdragon AI Studio RC2.

german.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC2
german.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 2%nInstallationssprache auswählen:
german.WelcomeLabel1=Willkommen bei Snapdragon AI Studio
german.WelcomeLabel2=Phoenix Engine · Version 2.0 RC2%n%nProfessionelle lokale KI-Plattform für Bildgenerierung und%nSnapdragon NPU-Beschleunigung unter Windows on ARM.%n%nVorabversion zu Test- und Evaluierungszwecken.%n%nUnabhängiges Open-Source-Projekt für Windows auf Snapdragon. Kein offizielles Qualcomm-Produkt.%n%n© 2026 Holger Kreuzhofen
german.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC2 wurde erfolgreich installiert
german.FinishedLabel=Die Installation von Snapdragon AI Studio 2.0 RC2 wurde erfolgreich abgeschlossen.%n%nVielen Dank, dass Sie Snapdragon AI Studio RC2 testen.

spanish.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC2
spanish.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 2%nSeleccione el idioma de instalación:
spanish.WelcomeLabel1=Bienvenido a Snapdragon AI Studio
spanish.WelcomeLabel2=Phoenix Engine · Versión 2.0 RC2%n%nPlataforma profesional de IA local para generación de imágenes y%naceleración Snapdragon NPU en Windows on ARM.%n%nVersión preliminar para fines de prueba y evaluación.%n%nProyecto independiente de código abierto para Windows en Snapdragon. No es un producto oficial de Qualcomm.%n%n© 2026 Holger Kreuzhofen
spanish.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC2 se ha instalado correctamente
spanish.FinishedLabel=Snapdragon AI Studio 2.0 RC2 se ha instalado correctamente.%n%nGracias por probar Snapdragon AI Studio RC2.

[Files]
Source: "..\dist\SnapdragonAIStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExecutableName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExecutableName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\{#ExecutableName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeLanguagePreferences;
var
  PreferencesDir: String;
  PreferencesPath: String;
  Language: String;
  PreferencesJson: String;
begin
  PreferencesDir := ExpandConstant('{localappdata}\Snapdragon AI Studio\data');
  PreferencesPath := AddBackslash(PreferencesDir) + 'preferences.json';
  if FileExists(PreferencesPath) then
    Exit;

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

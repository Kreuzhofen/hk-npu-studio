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
AppVerName=Snapdragon AI Studio 2.0 RC1
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
english.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC1
english.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 1%nSelect the installation language:
english.WelcomeLabel1=Welcome to Snapdragon AI Studio
english.WelcomeLabel2=Phoenix Engine · Version 2.0 RC1%n%nProfessional local AI platform for image generation and%nSnapdragon NPU acceleration on Windows on ARM.%n%nPre-release version for testing and evaluation purposes.%n%n© 2026 Holger Kreuzhofen
english.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC1 has been installed successfully
english.FinishedLabel=Setup has finished installing Snapdragon AI Studio 2.0 RC1.%n%nThank you for testing Snapdragon AI Studio RC1.

german.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC1
german.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 1%nInstallationssprache auswählen:
german.WelcomeLabel1=Willkommen bei Snapdragon AI Studio
german.WelcomeLabel2=Phoenix Engine · Version 2.0 RC1%n%nProfessionelle lokale KI-Plattform für Bildgenerierung und%nSnapdragon NPU-Beschleunigung unter Windows on ARM.%n%nVorabversion zu Test- und Evaluierungszwecken.%n%n© 2026 Holger Kreuzhofen
german.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC1 wurde erfolgreich installiert
german.FinishedLabel=Die Installation von Snapdragon AI Studio 2.0 RC1 wurde erfolgreich abgeschlossen.%n%nVielen Dank, dass Sie Snapdragon AI Studio RC1 testen.

spanish.SelectLanguageTitle=Snapdragon AI Studio · Version 2.0 RC1
spanish.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 1%nSeleccione el idioma de instalación:
spanish.WelcomeLabel1=Bienvenido a Snapdragon AI Studio
spanish.WelcomeLabel2=Phoenix Engine · Versión 2.0 RC1%n%nPlataforma profesional de IA local para generación de imágenes y%naceleración Snapdragon NPU en Windows on ARM.%n%nVersión preliminar para fines de prueba y evaluación.%n%n© 2026 Holger Kreuzhofen
spanish.FinishedHeadingLabel=Snapdragon AI Studio 2.0 RC1 se ha instalado correctamente
spanish.FinishedLabel=Snapdragon AI Studio 2.0 RC1 se ha instalado correctamente.%n%nGracias por probar Snapdragon AI Studio RC1.

[Files]
Source: "..\dist\SnapdragonAIStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExecutableName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExecutableName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\{#ExecutableName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

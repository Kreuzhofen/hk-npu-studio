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
AppPublisher={#Publisher}
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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\dist\SnapdragonAIStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExecutableName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExecutableName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\{#ExecutableName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

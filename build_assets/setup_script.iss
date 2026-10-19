[Setup]
SourceDir=..
AppName=DrawMotion
AppVersion=1.7.10
AppPublisher=EASY SOFT TEAM (Mohamed Fadl)
AppPublisherURL=https://github.com/DMotionX/DrawMotion
AppSupportURL=https://drawmotion-web.vercel.app/
AppUpdatesURL=https://github.com/DMotionX/DrawMotion/releases
DefaultDirName={autopf}\EASY SOFT\DrawMotion
DefaultGroupName=DrawMotion
OutputDir=build_out
OutputBaseFilename=DrawMotion_Setup
SetupIconFile=resources\branding\ICO\DrawMotion.ico
Compression=lzma
SolidCompression=yes
LicenseFile=build_assets\EULA.txt
InfoBeforeFile=build_assets\PrivacyPolicy.txt
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\DrawMotion\DrawMotion.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DrawMotion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build_assets\PrivacyPolicy.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DrawMotion"; Filename: "{app}\DrawMotion.exe"
Name: "{group}\{cm:UninstallProgram,DrawMotion}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DrawMotion"; Filename: "{app}\DrawMotion.exe"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.wip"; ValueType: string; ValueName: ""; ValueData: "DrawMotionProject"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\DrawMotionProject"; ValueType: string; ValueName: ""; ValueData: "DrawMotion Project"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\DrawMotionProject\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\resources\branding\ICO\DrawMotion.ico,0"
Root: HKA; Subkey: "Software\Classes\DrawMotionProject\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DrawMotion.exe"" ""%1"""

[Run]
Filename: "{app}\DrawMotion.exe"; Description: "{cm:LaunchProgram,DrawMotion}"; Flags: nowait runasoriginaluser

[InstallDelete]
Type: files; Name: "{localappdata}\DrawMotion\boot_health.json"

[UninstallDelete]
Type: files; Name: "{localappdata}\DrawMotion\boot_health.json"

[Setup]
SourceDir=..
AppName=DrawMotion
AppVersion=1.7.8
AppPublisher=EASY SOFT TEAM
DefaultDirName={pf}\DrawMotion
DefaultGroupName=DrawMotion
OutputDir=build_out
OutputBaseFilename=DrawMotion_Setup
SetupIconFile=resources\branding\ICO\DrawMotion.ico
Compression=lzma
SolidCompression=yes
LicenseFile=build_assets\EULA.txt
InfoBeforeFile=build_assets\PrivacyPolicy.txt
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\DrawMotion\DrawMotion.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DrawMotion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build_assets\PrivacyPolicy.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DrawMotion"; Filename: "{app}\DrawMotion.exe"
Name: "{group}\{cm:UninstallProgram,DrawMotion}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\DrawMotion"; Filename: "{app}\DrawMotion.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DrawMotion.exe"; Description: "{cm:LaunchProgram,DrawMotion}"; Flags: nowait runasoriginaluser

[InstallDelete]
Type: files; Name: "{localappdata}\DrawMotion\boot_health.json"

[UninstallDelete]
Type: files; Name: "{localappdata}\DrawMotion\boot_health.json"

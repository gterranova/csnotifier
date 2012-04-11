; -- Example1.iss --
; Demonstrates copying 3 files and creating an icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=CouchSurfing Notifier
AppVerName=CouchSurfing Notifier 1.2 (beta)
DefaultDirName={pf}\CouchSurfing Notifier
DefaultGroupName=CouchSurfing Notifier
UninstallDisplayIcon={app}\csnotifier.ico
Compression=lzma
SolidCompression=yes
;OutputDir=userdocs:Inno Setup Examples Output

[Files]
Source: "../csnotifier.pyw"; DestDir: "{app}"
Source: "../csnotifier.py"; DestDir: "{app}"
Source: "../cslib.py"; DestDir: "{app}"
Source: "../resources.py"; DestDir: "{app}"
Source: "../settings.py"; DestDir: "{app}"
Source: "../toasterbox.py"; DestDir: "{app}"
Source: "../autoupdate.py"; DestDir: "{app}"
Source: "../csnotifier.ico"; DestDir: "{app}"
Source: "../GPL.txt"; DestDir: "{app}"
Source: "../README.txt"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{group}\CouchSurfing Notifier"; Filename: "{app}\csnotifier.pyw"; IconFilename: "{app}\csnotifier.ico"; WorkingDir: "{app}"
Name: "{group}\Edit Settings"; Filename: "{win}\notepad.exe"; Parameters: """{app}\settings.py"""; IconFilename: "{app}\csnotifier.ico"; WorkingDir: "{app}"
Name: "{group}\Uninstall CouchSurfing Notifier"; Filename: "{uninstallexe}"

[UninstallDelete]
Type: files; Name: "{app}\csnotifier.pyc"
Type: files; Name: "{app}\cslib.pyc"
Type: files; Name: "{app}\autoupdate.pyc"
Type: files; Name: "{app}\settings.pyc"
Type: files; Name: "{app}\resources.pyc"
Type: files; Name: "{app}\toasterbox.pyc"
Type: files; Name: "{app}\current.dat"


Unicode True
RequestExecutionLevel user
!define PRODUCT_NAME "KMZ Preview"
!define PRODUCT_VERSION "0.3.0"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\KMZPreview"
!define CONTEXT_MENU_KEY "Software\Classes\SystemFileAssociations\.kmz\shell\KMZPreview"
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\release\install.exe"
InstallDir "$LOCALAPPDATA\Programs\KMZPreview"
InstallDirRegKey HKCU "Software\KMZPreview" "InstallDir"
ShowInstDetails show
ShowUninstDetails show
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "..\dist\KMZPreview\*"
  File "install-marker.txt"

  ; Save the previous class association only on the first installation.
  ReadRegStr $0 HKCU "Software\KMZPreview" "InstallDir"
  IfErrors 0 association_saved
  ReadRegStr $0 HKCU "Software\Classes\.kmz" ""
  WriteRegStr HKCU "Software\KMZPreview" "PreviousKmzAssociation" "$0"
  association_saved:
  WriteRegStr HKCU "Software\KMZPreview" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Classes\.kmz" "" "KMZPreviewFile"
  WriteRegStr HKCU "Software\Classes\KMZPreviewFile" "" "DJI KMZ route file"
  WriteRegStr HKCU "Software\Classes\KMZPreviewFile\DefaultIcon" "" "$INSTDIR\KMZPreview.exe,0"
  WriteRegStr HKCU "Software\Classes\KMZPreviewFile\shell\open\command" "" '"$INSTDIR\KMZPreview.exe" "%1"'

  ; This context-menu verb works even when Windows keeps another default app.
  WriteRegStr HKCU "${CONTEXT_MENU_KEY}" "" "Preview KMZ with KMZ Preview"
  WriteRegStr HKCU "${CONTEXT_MENU_KEY}" "Icon" "$INSTDIR\KMZPreview.exe,0"
  WriteRegStr HKCU "${CONTEXT_MENU_KEY}\command" "" '"$INSTDIR\KMZPreview.exe" "%1"'

  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\KMZPreview.exe,0"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1

  CreateDirectory "$SMPROGRAMS\KMZ Preview"
  CreateShortcut "$SMPROGRAMS\KMZ Preview\KMZ Preview.lnk" "$INSTDIR\KMZPreview.exe"
  CreateShortcut "$SMPROGRAMS\KMZ Preview\Uninstall KMZ Preview.lnk" "$INSTDIR\uninstall.exe"
  System::Call 'shell32::SHChangeNotify(i 0x8000000, i 0, p 0, p 0)'
SectionEnd

Section "Uninstall"
  IfFileExists "$INSTDIR\install-marker.txt" 0 abort_uninstall
  DeleteRegKey HKCU "${CONTEXT_MENU_KEY}"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"

  ; Restore the old association only if ours is still the registered class.
  ReadRegStr $0 HKCU "Software\Classes\.kmz" ""
  StrCmp $0 "KMZPreviewFile" 0 association_done
  ReadRegStr $0 HKCU "Software\KMZPreview" "PreviousKmzAssociation"
  StrCmp $0 "" 0 restore_kmz_association
  DeleteRegValue HKCU "Software\Classes\.kmz" ""
  DeleteRegKey /ifempty HKCU "Software\Classes\.kmz"
  Goto association_done
  restore_kmz_association:
    WriteRegStr HKCU "Software\Classes\.kmz" "" "$0"
  association_done:
  DeleteRegKey HKCU "Software\Classes\KMZPreviewFile"
  DeleteRegKey HKCU "Software\KMZPreview"
  Delete "$SMPROGRAMS\KMZ Preview\KMZ Preview.lnk"
  Delete "$SMPROGRAMS\KMZ Preview\Uninstall KMZ Preview.lnk"
  RMDir "$SMPROGRAMS\KMZ Preview"
  Delete "$INSTDIR\KMZPreview.exe"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$INSTDIR\install-marker.txt"
  RMDir /r "$INSTDIR\web"
  RMDir /r "$INSTDIR\_internal"
  RMDir "$INSTDIR"
  System::Call 'shell32::SHChangeNotify(i 0x8000000, i 0, p 0, p 0)'
  Goto done_uninstall
  abort_uninstall:
    MessageBox MB_ICONSTOP "Install marker was not found; uninstall was stopped to protect this folder."
  done_uninstall:
SectionEnd

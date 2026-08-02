; 覆盖 electron-builder 内置的进程检查宏
; 原因: nsProcess 插件有时会误判进程存在（即使程序根本没运行过）
; 安装器直接跳过进程检查，不再提示"请关闭应用"
!macro customCheckAppRunning
  ; 不做任何操作，直接跳过进程检查
  DetailPrint "跳过进程检查..."
!macroend
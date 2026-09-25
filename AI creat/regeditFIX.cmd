@echo off
chcp 65001 >nul
title IFEO 威胁扫描与修复工具
setlocal EnableDelayedExpansion

:: ========== 配置 ==========
set "reportFile=%USERPROFILE%\Desktop\IFEO_Threat_Report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "reportFile=%reportFile: =0%"
set "tempList=%TEMP%\ifeo_suspicious.tmp"
set "policyList=%TEMP%\policy_suspicious.tmp"
set "suspiciousFound=0"

echo ============================================
echo     IFEO 威胁扫描与修复工具
echo     扫描路径: HKLM\...\Image File Execution Options
echo     策略检查: 本地组策略异常
echo ============================================
echo.

:: ========== 扫描 IFEO ==========
echo [*] 正在扫描 Image File Execution Options...
echo.

if exist "%tempList%" del "%tempList%"

for /f "tokens=*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options" 2^>nul') do (
    set "keyPath=%%a"
    
    :: 跳过 IFEO 根键本身
    echo !keyPath! | findstr /I /C:"Image File Execution Options$" >nul
    if !errorlevel! neq 0 (
        
        :: 提取条目名（最后一个反斜杠后的内容）
        for %%b in ("!keyPath!") do set "entryName=%%~nxb"
        
        :: 检查是否有 Debugger 键
        reg query "!keyPath!" /v "Debugger" >nul 2>&1
        if !errorlevel! equ 0 (
            for /f "tokens=2,*" %%c in ('reg query "!keyPath!" /v "Debugger" 2^>nul ^| findstr /I "Debugger"') do (
                set "debuggerValue=%%d"
                
                :: 判断 Debugger 是否可疑
                set "isSuspicious=0"
                
                :: 规则1: Debugger 指向非系统目录
                echo !debuggerValue! | findstr /I /V /C:"C:\Windows\System32" /C:"C:\Windows\SysWOW64" /C:"C:\Program Files" >nul
                if !errorlevel! equ 0 set "isSuspicious=1"
                
                :: 规则2: 可疑文件名
                echo !entryName! | findstr /I /C:"ExtExport" /C:"mshta" /C:"spoolsv" /C:"svchost" /C:"lsass" /C:"csrss" >nul
                if !errorlevel! equ 0 set "isSuspicious=1"
                
                :: 规则3: Debugger 指向 .tmp, .temp, .dat, 无扩展名文件
                echo !debuggerValue! | findstr /I /E /C:".tmp" /C:".temp" /C:".dat" >nul
                if !errorlevel! equ 0 set "isSuspicious=1"
                
                if !isSuspicious! equ 1 (
                    echo   [!!] 威胁发现: !entryName!
                    echo        Debugger = !debuggerValue!
                    echo !entryName!^|!debuggerValue!>>"%tempList%"
                    set "suspiciousFound=1"
                ) else (
                    echo   [OK] 正常条目: !entryName! (Debugger: !debuggerValue!)
                )
            )
        ) else (
            :: 无 Debugger 键，检查是否是已知恶意占位
            echo !entryName! | findstr /I /C:"ExtExport" >nul
            if !errorlevel! equ 0 (
                echo   [!!] 可疑占位: !entryName! (无Debugger键，但名称异常)
                echo !entryName!^|占位条目>>"%tempList%"
                set "suspiciousFound=1"
            )
        )
    )
)

echo.
echo [*] IFEO 扫描完成。
echo.

:: ========== 检查组策略限制 ==========
echo [*] 正在检查组策略异常...
echo.

if exist "%policyList%" del "%policyList%"

:: 检查常见被篡改的策略路径
set "policyPaths=HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System HKLM\SOFTWARE\Policies\Microsoft\Windows\System HKLM\SOFTWARE\Policies\Microsoft\Windows Defender"

for %%p in (%policyPaths%) do (
    reg query "%%p" >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=1,2,*" %%a in ('reg query "%%p" 2^>nul ^| findstr /V "HKEY_" ^| findstr /V "^\s*$"') do (
            set "policyName=%%a"
            set "policyType=%%b"  
            set "policyValue=%%c"
            
            :: 检测禁用安全中心的策略
            echo !policyName! | findstr /I /C:"DisableAntiSpyware" /C:"DisableRealtimeMonitoring" /C:"DisableBehaviorMonitoring" /C:"DisableOnAccessProtection" /C:"DisableTaskMgr" /C:"DisableRegistryTools" /C:"DisableCMD" >nul
            if !errorlevel! equ 0 (
                echo   [!!] 策略威胁: %%p\!policyName! = !policyValue!
                echo %%p\!policyName!^|!policyValue!>>"%policyList%"
                set "suspiciousFound=1"
            )
        )
    )
)

echo.
echo [*] 策略检查完成。
echo.

:: ========== 结果汇总 ==========
if !suspiciousFound! equ 0 (
    echo ============================================
    echo [✓] 未发现可疑威胁。系统干净。
    echo ============================================
    pause
    exit /b 0
)

echo ============================================
echo [!] 发现可疑威胁，共需处理以下条目：
echo.
if exist "%tempList%" (
    echo --- IFEO 劫持条目 ---
    for /f "tokens=1,2 delims=|" %%a in (%tempList%) do (
        echo   [IFEO] %%a
        if not "%%b"=="占位条目" echo        Debugger: %%b
    )
)
if exist "%policyList%" (
    echo.
    echo --- 异常组策略 ---
    for /f "tokens=1,2 delims=|" %%a in (%policyList%) do (
        echo   [POLICY] %%a = %%b
    )
)
echo.
echo ============================================

:: ========== 用户确认 ==========
echo.
echo 是否执行自动修复？
echo [Y] 是 - 删除可疑 IFEO 条目并清理异常策略
echo [N] 否 - 仅生成报告，不修改系统
echo.
set /p userChoice="请输入 Y 或 N: "

if /I "!userChoice!"=="Y" goto :DO_FIX
if /I "!userChoice!"=="y" goto :DO_FIX

:: ========== 仅标记模式 ==========
echo.
echo [*] 用户选择不修复，正在生成威胁报告...
echo.

(
    echo ============================================
    echo   IFEO 威胁扫描报告
    echo   扫描时间: %date% %time%
    echo   计算机名: %COMPUTERNAME%
    echo   用户名:   %USERNAME%
    echo ============================================
    echo.
    echo [警告] 以下条目被标记为可疑，但未执行修复
    echo        请手动审查后决定是否删除
    echo.
    
    if exist "%tempList%" (
        echo ---------- IFEO 劫持条目 ----------
        echo.
        for /f "tokens=1,2 delims=|" %%a in (%tempList%) do (
            echo [威胁] 条目名: %%a
            if not "%%b"=="占位条目" (
                echo        Debugger: %%b
            ) else (
                echo        类型: 异常占位条目
            )
            echo        完整路径: HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\%%a
            echo.
        )
    )
    
    if exist "%policyList%" (
        echo ---------- 异常组策略 ----------
        echo.
        for /f "tokens=1,2 delims=|" %%a in (%policyList%) do (
            echo [威胁] 策略路径: %%a
            echo        当前值: %%b
            echo.
        )
    )
    
    echo ============================================
    echo   建议操作:
    echo   1. 对 IFEO 条目: 在注册表编辑器中手动删除对应子键
    echo   2. 对策略条目: 使用 gpedit.msc 或 regedit 恢复默认值
    echo   3. 运行 sfc /scannow 检查系统文件完整性
    echo ============================================
) > "%reportFile%"

echo [✓] 报告已保存至: %reportFile%
echo.
pause
exit /b 0

:: ========== 自动修复模式 ==========
:DO_FIX
echo.
echo [*] 开始自动修复...
echo [!] 正在删除可疑 IFEO 条目...
echo.

if exist "%tempList%" (
    for /f "tokens=1 delims=|" %%a in (%tempList%) do (
        echo   [-] 删除: HKLM\...\Image File Execution Options\%%a
        reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\%%a" /f >nul 2>&1
        if !errorlevel! equ 0 (
            echo       [OK] 已删除
        ) else (
            echo       [FAIL] 删除失败，可能需要管理员权限
        )
    )
)

echo.
echo [!] 正在清理异常组策略...
echo.

if exist "%policyList%" (
    for /f "tokens=1 delims=|" %%a in (%policyList%) do (
        echo   [-] 删除策略值: %%a
        reg delete "%%a" /f >nul 2>&1
        if !errorlevel! equ 0 (
            echo       [OK] 已清理
        ) else (
            echo       [FAIL] 清理失败
        )
    )
)

echo.
echo [*] 修复完成。正在生成修复报告...
echo.

(
    echo ============================================
    echo   IFEO 威胁修复报告
    echo   扫描时间: %date% %time%
    echo   操作类型: 自动修复
    echo ============================================
    echo.
    
    if exist "%tempList%" (
        echo [已删除的 IFEO 条目]
        for /f "tokens=1 delims=|" %%a in (%tempList%) do (
            echo   - %%a
        )
    )
    
    if exist "%policyList%" (
        echo.
        echo [已清理的组策略]
        for /f "tokens=1 delims=|" %%a in (%policyList%) do (
            echo   - %%a
        )
    )
    
    echo.
    echo ============================================
    echo   后续建议:
    echo   1. 重启系统确保更改生效
    echo   2. 运行 sfc /scannow 检查系统完整性
    echo   3. 使用卡巴斯基急救盘进行离线深度扫描
    echo ============================================
) > "%reportFile%"

echo [✓] 修复报告已保存至: %reportFile%
echo.
echo [!] 建议立即重启系统。
echo.
pause
exit /b 0
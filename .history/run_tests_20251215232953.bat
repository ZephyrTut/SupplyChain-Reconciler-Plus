@echo off
REM ======================================================================
REM 模板删除功能自动化测试脚本
REM 用途：一键运行所有测试，确保功能正常
REM ======================================================================

echo.
echo ======================================================================
echo   SupplyChain-Reconciler-Plus 自动化测试
echo ======================================================================
echo.

REM 运行测试（直接指定测试文件）
python tests\test_template_standalone.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 测试通过！可以安全部署
    echo.
    pause
    exit /b 0
) else (
    echo.
    echo ❌ 测试失败！请检查错误后重试
    echo.
    pause
    exit /b 1
)

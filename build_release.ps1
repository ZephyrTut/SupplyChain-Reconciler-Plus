name: Build and Release Windows Executable

on:
  push:
    tags:
      - 'v*.*.*'  # 匹配 v1.4.3, v2.0.0 等版本标签
  workflow_dispatch:  # 允许手动触发
    inputs:
      version:
        description: '版本号 (例如: v1.4.3)'
        required: true
        default: 'v1.0.0'

jobs:
  build-windows:
    runs-on: windows-latest
    
    permissions:
      contents: write  # 必须的权限
    
    outputs:
      version: ${{ steps.get_version.outputs.version }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      with:
        fetch-depth: 0  # 获取所有历史记录，用于标签检测
    
    - name: Determine version
      id: get_version
      run: |
        # 如果是标签触发，使用标签名
        if [ "${{ github.event_name }}" = "push" ] && [[ "${{ github.ref }}" == refs/tags/* ]]; then
          VERSION="${GITHUB_REF#refs/tags/}"
        # 如果是手动触发，使用输入参数
        elif [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
          VERSION="${{ github.event.inputs.version }}"
        # 默认从脚本获取或使用git describe
        else
          # 尝试从您的脚本中获取默认版本
          VERSION="v1.0.0"
        fi
        echo "version=$VERSION" >> $GITHUB_OUTPUT
        echo "Building version: $VERSION"
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        architecture: 'x64'
    
    - name: Run your build script
      env:
        VERSION: ${{ steps.get_version.outputs.version }}
      run: |
        # 直接运行您的PowerShell脚本
        powershell -ExecutionPolicy Bypass -File ./build_release.ps1 -Version "$env:VERSION"
    
    - name: List build artifacts
      run: |
        echo "Built artifacts in dist/:"
        dir dist/
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: SupplyChain-Reconciler-Plus-${{ steps.get_version.outputs.version }}
        path: |
          dist/SupplyChain-Reconciler-Plus.exe
          dist/reconciler-${{ steps.get_version.outputs.version }}-windows.zip
    
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
      with:
        tag_name: ${{ steps.get_version.outputs.version }}
        name: Release ${{ steps.get_version.outputs.version }}
        body: |
          # Supply Chain Reconciler Plus ${{ steps.get_version.outputs.version }}
          
          ## 🚀 新增功能
          - [在此处添加版本说明]
          
          ## 📦 下载
          - **SupplyChain-Reconciler-Plus.exe**: 单个可执行文件，无需安装Python环境
          - **reconciler-${{ steps.get_version.outputs.version }}-windows.zip**: 完整压缩包
          
          ## ⚙️ 系统要求
          - Windows 10 或更高版本
          - .NET Framework 4.5+ (如果使用了相关组件)
          
          ## 🔧 使用说明
          1. 下载并解压文件
          2. 双击 `SupplyChain-Reconciler-Plus.exe` 运行
          3. 按照界面提示操作
          
          ## 📝 更新日志
          - 版本 ${{ steps.get_version.outputs.version }} 初始发布
          
          ## 🤝 反馈
          如有问题，请在 Issues 中反馈。
        draft: false
        prerelease: false
        files: |
          dist/SupplyChain-Reconciler-Plus.exe
          dist/reconciler-${{ steps.get_version.outputs.version }}-windows.zip
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
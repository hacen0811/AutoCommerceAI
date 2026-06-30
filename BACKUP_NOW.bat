@echo off
chcp 65001 >nul
python -c "from modules.system.project_backup import ProjectBackup; print(ProjectBackup().export_all(include_assets=True))"
pause

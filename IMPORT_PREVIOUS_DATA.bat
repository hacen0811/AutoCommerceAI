@echo off
chcp 65001 >nul
echo 이전 AutoCommerceAI 폴더 경로를 입력하세요.
set /p PREV=이전 폴더 경로: 
python -c "from modules.system.data_migration import DataMigration; import json; print(json.dumps(DataMigration().import_data(r'%PREV%', copy_exports=False, overwrite=True), ensure_ascii=False, indent=2))"
pause

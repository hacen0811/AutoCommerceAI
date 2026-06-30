# AutoCommerceAI 2.1 Easy Start Recovery Test Report

## Syntax Check
PASS

## Pytest
PASS

## stdout
```
[1m============================= test session starts ==============================[0m
platform linux -- Python 3.13.5, pytest-9.0.2, pluggy-1.6.0
rootdir: /mnt/data/AutoCommerceAI_2.1_EasyStartRecovery
configfile: pyproject.toml
plugins: Faker-40.1.2, metadata-3.1.1, json-report-1.5.0, cov-7.0.0, asyncio-1.3.0, anyio-4.13.0, ddtrace-4.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 29 items

tests/test_backup_restore.py [32m.[0m[32m.[0m[32m                                          [  6%][0m
tests/test_core_engines.py [32m.[0m[32m.[0m[32m.[0m[32m                                           [ 17%][0m
tests/test_data_migration.py [32m.[0m[32m.[0m[32m                                          [ 24%][0m
tests/test_media_info_ffmpeg.py [32m.[0m[32m.[0m[32m.[0m[32m                                      [ 34%][0m
tests/test_product_engine_20.py [32m.[0m[32m.[0m[32m                                       [ 41%][0m
tests/test_product_keyword_quality.py [32m.[0m[32m.[0m[32m.[0m[32m                                [ 51%][0m
tests/test_project_recovery.py [32m.[0m[32m.[0m[32m                                        [ 58%][0m
tests/test_project_selector_video_service.py [32m.[0m[32m.[0m[32m                          [ 65%][0m
tests/test_source_video_ai.py [32m.[0m[32m.[0m[32m.[0m[32m                                        [ 75%][0m
tests/test_video_path_resolver.py [32m.[0m[32m                                      [ 79%][0m
tests/test_vision_score_engine.py [32m.[0m[32m.[0m[32m                                     [ 86%][0m
tests/test_workflow_engine.py [32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                       [100%][0m

[32m============================== [32m[1m29 passed[0m[32m in 1.07s[0m[32m ==============================[0m

```

## stderr
```
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/spreadsheet_warmup.py", line 720, in _warm_feature_flows
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/spreadsheet_warmup.py", line 704, in _warm_collaboration_flows
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/generated/interface/models.py", line 30820, in hydrate_crdt_from_proto
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/rpc/remote.py", line 749, in __call__
  File "/tmp/tmp.yTcnQsZYiA/artifact_tool_v2-2.8.4/artifact_tool/rpc/client.py", line 150, in call
artifact_tool.rpc.client.RemoteError: hydrateCrdtFromProto requires an empty collaborative document.

```

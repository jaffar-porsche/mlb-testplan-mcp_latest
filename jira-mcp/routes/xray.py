"""xRay routes — aggregator that combines all xRay category sub-routers.

Sub-modules:
  xray_models.py       - Shared Pydantic request/response models
  xray_tests.py        - Test step CRUD (/xray/test/*)
  xray_testplan.py     - Test Plan management + async aggregation (/xray/testplan/*)
  xray_testexecution.py - Test Execution listing (/xray/testexecution/*)
  xray_testrun.py      - Test Run management, iterations, resets (/xray/testrun/*, /xray/testruns)
  xray_testset.py      - Test Set listing (/xray/testset/*)
  xray_settings.py     - License, statuses, datasets, project config, issue types
"""
from fastapi import APIRouter

from routes.xray_tests import router as _tests_router
from routes.xray_testplan import router as _testplan_router
from routes.xray_testexecution import router as _testexecution_router
from routes.xray_testrun import router as _testrun_router
from routes.xray_testset import router as _testset_router
from routes.xray_settings import router as _settings_router

router = APIRouter()
router.include_router(_tests_router)
router.include_router(_testplan_router)
router.include_router(_testexecution_router)
router.include_router(_testrun_router)
router.include_router(_testset_router)
router.include_router(_settings_router)

export TARGET_ARCHIVE="../stage1/adsy1100.zip"
export MAX_USE_CASES_TO_TEST=10
export HDL_BUILD_ID="ID_T50_R50_LR20625"
export TARGET_BIN_FILE="vu11p.bin"
touch $TARGET_BIN_FILE

# export TARGET_ARCHIVE="test/adsy1100/profiles_testing/stage1/adsy1100.zip"
# export MAX_USE_CASES_TO_TEST=10
# export HDL_BUILD_ID="ID_T50_R50_LR20625"
# export TARGET_BIN_FILE="test/adsy1100/profiles_testing/stage3/vu11p.bin"


if [ ! -f "$TARGET_ARCHIVE" ]; then
    echo "Target archive $TARGET_ARCHIVE not found. Please run the script from the correct directory."
    exit 1
fi

python generate_pytest_tests.py


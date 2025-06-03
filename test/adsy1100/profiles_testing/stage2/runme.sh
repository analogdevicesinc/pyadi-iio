export TARGET_ARCHIVE="adsy1100.zip"
export HDL_BUILD_ID="ID_T50_R50_LR20625"


if [ ! -f "$TARGET_ARCHIVE" ]; then
    echo "Target archive $TARGET_ARCHIVE not found. Please run the script from the correct directory."
    exit 1
fi

python update_tables_bitstreams.py


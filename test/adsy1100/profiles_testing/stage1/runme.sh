#!/bin/bash
set -xe

export MAX_MODE_PAIRS=10
export MAX_ALLOWED_COMMON_LANE_RATE_HZ=21000000000
export KERNEL_CLONE="GIT_GHE"
# LINUX_BRANCH
export NUGET_PROFILES="AnalogDevices.Apollo.Profiles.9.6.0.nupkg"

# Checks
if [ ! -f "$NUGET_PROFILES" ]; then
    echo "NuGet package $NUGET_PROFILES not found. Please run the script from the correct directory."
    exit 1
fi

# Go go go
rm -rf dl || true
mkdir dl
cd dl
cp ../$NUGET_PROFILES AnalogDevices.Apollo.Profiles.zip
unzip AnalogDevices.Apollo.Profiles.zip
mv content/resources/AnalogDevices.Apollo.Profiles ../
cd ..

rm -rf dl

python generate_test_configs.py



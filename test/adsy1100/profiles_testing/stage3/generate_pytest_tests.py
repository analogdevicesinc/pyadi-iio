import time
import os
import zipfile

import pandas as pd

def get_test_boot_files_from_archive():
    """
    This function extracts the test boot files from the archive.
    It checks if the archive is present, extracts it if not already done,
    and returns the path to the extracted files.
    """
    target_bin_file = os.getenv("TARGET_BIN_FILE", False)
    if not target_bin_file:
        raise ValueError("TARGET_BIN_FILE environment variable is not set. Please set it to the path of the target binary file.")
    if not os.path.isfile(target_bin_file):
        raise FileNotFoundError(f"Target binary file {target_bin_file} not found. Please set the TARGET_BIN_FILE environment variable to the correct path.")

    target_archive = os.getenv("TARGET_ARCHIVE", "archive.zip")
    if not os.path.isfile(target_archive):
        raise FileNotFoundError(f"Target archive {target_archive} not found. Please run the script to extract the file.")

    target_archive_dir = os.path.join(os.path.dirname(__file__), "archive")
    if not os.path.isdir(target_archive_dir):
        os.makedirs(target_archive_dir)
    with zipfile.ZipFile(target_archive, 'r') as zip_ref:
        zip_ref.extractall(target_archive_dir)
    os.system(f'ls "{target_archive_dir}"')

    max_use_cases_to_test = os.getenv("MAX_USE_CASES_TO_TEST", None)
    if max_use_cases_to_test is not None:
        max_use_cases_to_test = int(max_use_cases_to_test)

    dataset_filename = "adsy1100_profiles_final_summary.xlsx"
    dataset = os.path.join(target_archive_dir, dataset_filename)
    if not os.path.isfile(dataset):
        raise FileNotFoundError(f"File {dataset} not found. Please run the script to extract the file.")

    dataset = pd.read_excel(dataset)

    hdl_build_id = os.getenv("HDL_BUILD_ID", None)
    if hdl_build_id is None:
        raise ValueError("HDL_BUILD_ID environment variable is not set. Please set it to the HDL build ID you want to test.")

    print(f"Filtering dataset for HDL build ID: {hdl_build_id}")
    dataset = dataset[dataset["hdl_build_id"] == hdl_build_id]
    if dataset.empty:
        raise ValueError(f"No entries found for HDL build ID: {hdl_build_id}")
    print(f"Filtered dataset contains {len(dataset)} entries.")
    common_boot_files_folder = os.path.join(os.path.dirname(__file__), "..", "..", "bootfiles", "b0_main")
    bootbin = os.path.join(common_boot_files_folder, "BOOT.BIN")

    # Shared components
    image = os.path.join(target_archive_dir, "Image")
    zynq_dtb_file = os.path.join(target_archive_dir, "zynqmp-vpx-apollo.dtb")
    if not os.path.isfile(zynq_dtb_file):
        raise FileNotFoundError(f"Device tree file {zynq_dtb_file} not found. Please run the script to extract the file.")
    # Copy and overwrite to system.dtb for compatibility
    system_dtb = os.path.join(target_archive_dir, "system.dtb")
    os.system(f'cp "{zynq_dtb_file}" "{system_dtb}"')

    # Build the test configurations
    configs = []
    for index, row in dataset.iterrows():
        configs.append({
            "name": row["id"],
            "BOOT.BIN": bootbin,
            "Kernel": image,
            "devicetree": system_dtb,
            "selmap_overlay": os.path.join(target_archive_dir, row["dtb_file"]),
            "selmap_bin": target_bin_file,
            "extras": [
                {"src": os.path.join(target_archive_dir, row["bin_filename"]), "dst": "/lib/firmware/"}
            ],
        })

        if max_use_cases_to_test and len(configs) >= max_use_cases_to_test:
            break


    # Check if the boot files are present
    print("Checking if boot files are present...")
    for cfg in configs:
        for key in cfg:
            if key != "name" and key != "extras":
                assert os.path.isfile(
                    os.path.join(cfg[key])
                ), f"File {key} not found at {os.path.join(cfg[key])}"
            if key == "extras":
                for extra in cfg[key]:
                    assert os.path.isfile(
                        os.path.join(extra["src"])
                    ), f"File {extra['src']} not found at {os.path.join(extra['src'])}"


    return configs

if __name__ == "__main__":
    # This is just a test to ensure the function works correctly
    try:
        configs = get_test_boot_files_from_archive()
        print(f"Found {len(configs)} configurations.")
    except Exception as e:
        print(f"Error: {e}")
    else:
        for cfg in configs:
            print(cfg)

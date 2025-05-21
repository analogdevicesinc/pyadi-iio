import os
import shutil
import re
import pandas as pd
import zipfile
import sys

# Drop archive from Jenkins builds to extract the files and generate the final summary

filename = 'archive.zip'
target_dir_outputs = 'test_boot_files'

def handle_jenkins_zip(filename):
    global target_dir_outputs

    # target_dir_outputs full path
    here = os.path.dirname(os.path.abspath(__file__))
    target_dir_outputs = os.path.join(here, target_dir_outputs)

    # Unzip the file
    print(f"Unzipping '{filename}' to 'extracted_files' directory")
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall('extracted_files')
        print(f"Extracted files from {filename} to 'extracted_files' directory.")

    here = os.path.dirname(os.path.abspath(__file__))
    extracted_files = os.path.join(here, 'extracted_files')

    # Find "ads1100_profiles_final_summary.xlsx" within the extracted files
    def find_file_in_extracted_dir(directory, filename):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if re.search(filename, file):
                    # Get the full path of the file
                    root = os.path.abspath(root)
                    return os.path.join(root, file)
        return None
    filename_to_find = "ads1100_profiles_final_summary.xlsx"
    found_file = find_file_in_extracted_dir(extracted_files, filename_to_find)

    if not found_file:
        print(f"File '{filename_to_find}' not found in the extracted directory.")
        raise FileNotFoundError(f"File '{filename_to_find}' not found in the extracted directory.")
    print(f"File '{filename_to_find}' found at: {found_file}")

    # Read the Excel file
    excel_file = pd.ExcelFile(found_file)

    # Sheet1
    sheet1_name = 'Sheet1'
    sheet1 = pd.read_excel(excel_file, sheet_name=sheet1_name)
    # print(sheet1.head())

    def handle_hdl_zip(filename, target_dir):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Find the system_top.bin file within the extracted files
        system_top_bin_file = find_file_in_extracted_dir(target_dir, "system_top.bin")
        if not system_top_bin_file:
            print(f"File 'system_top.bin' not found in the extracted directory.")
            # raise FileNotFoundError(f"File 'system_top.bin' not found in the extracted directory.")
            return None
        print(f"File 'system_top.bin' found at: {system_top_bin_file}")

        return system_top_bin_file


    # Add column for vu11pbinfile
    sheet1['vu11pbinfile'] = None

    hdl_modes_parsed = {}
    for row in sheet1.iterrows():
        # print(row)
        hdl_build_id = row[1]['hdl_build_id']

        if hdl_build_id not in hdl_modes_parsed.keys():
            hdl_modes_parsed[hdl_build_id] = None
            zip_filename = f"apollo_som_vu11p_{hdl_build_id}.zip"
            # Check if the zip file exists
            zip_file_path = os.path.join(extracted_files, 'archive', zip_filename)
            if os.path.exists(zip_file_path):
                ...
            else:
                print(f"Zip file '{zip_filename}' does not exist.")
                raise FileNotFoundError(f"Zip file '{zip_filename}' does not exist.")
            # Unzip the file
            target_dir = os.path.join(extracted_files, 'archive', hdl_build_id)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            print(f"hdl_build_id: {hdl_build_id}")
            vu11pbinfile = handle_hdl_zip(zip_file_path, target_dir)

            # Move to the target directory
            if not os.path.exists(target_dir_outputs):
                os.makedirs(target_dir_outputs)
            # Move the file to the target directory
            if vu11pbinfile:
                target_path = os.path.join(target_dir_outputs, hdl_build_id)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)
                target_file_path = os.path.join(target_path, 'system_top.bin')
                print(f"Moving {vu11pbinfile} to {target_file_path}")
                shutil.copy(vu11pbinfile, target_file_path)
            else:
                sheet1.at[row[0], 'vu11pbinfile'] = None
                hdl_modes_parsed[hdl_build_id] = None
                continue

            vu11pbinfile = os.path.join(target_dir_outputs, hdl_build_id, 'system_top.bin')
            sheet1.at[row[0], 'vu11pbinfile'] = vu11pbinfile
            hdl_modes_parsed[hdl_build_id] = vu11pbinfile
        else:
            print(f"hdl_build_id: {hdl_build_id} already parsed, using cached value.")
            sheet1.at[row[0], 'vu11pbinfile'] = hdl_modes_parsed[hdl_build_id]
            # print(f"sheet1.at[{row[0]}, 'vu11pbinfile']: {sheet1.at[row[0], 'vu11pbinfile']}")


    ############### HANDLE DTBs
    zip_with_dtbs = 'adsy1100_boot_files.zip'
    zip_with_dtbs_path = os.path.join(extracted_files, 'archive', zip_with_dtbs)
    if os.path.exists(zip_with_dtbs_path):
        print(f"Zip file '{zip_with_dtbs}' exists.")
    else:
        print(f"Zip file '{zip_with_dtbs}' does not exist.")
        raise FileNotFoundError(f"Zip file '{zip_with_dtbs}' does not exist.")
    # Unzip the file
    target_dir = os.path.join(extracted_files, 'archive', 'sw_side')
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    print(f"Unzipping '{zip_with_dtbs}' to '{target_dir}'")
    with zipfile.ZipFile(zip_with_dtbs_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    # Remap file locations in the sheet1 for the dtb and bins (not system_top.bin)
    # Add dtb_file column
    sheet1['dtb_file'] = None
    for row in sheet1.iterrows():
        dts_file = row[1]['dts_file']
        # Get the dts file name
        dtb_file_name = os.path.basename(dts_file).replace('.dts', '.dtb')
        # Find the dtb file in the extracted directory
        dtb_file = find_file_in_extracted_dir(target_dir, dtb_file_name)
        if not dtb_file:
            print(f"File '{dtb_file_name}' not found in the extracted directory.")
            raise FileNotFoundError(f"File '{dtb_file_name}' not found in the extracted directory.")
        print(f"File '{dtb_file_name}' found at: {dtb_file}")
        # Move the file to the target directory
        target_path = os.path.join(target_dir_outputs, 'sw_side')
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        target_file_path = os.path.join(target_path, dtb_file_name)
        print(f"Moving {dtb_file} to {target_file_path}")
        shutil.copy(dtb_file, target_file_path)
        # Update the sheet1 with the dtb file path
        sheet1.at[row[0], 'dtb_file'] = target_file_path
        # Find the bin file in the extracted directory
        bin_file_name = os.path.basename(dts_file).replace('.dts', '.bin')
        bin_file_name = bin_file_name.replace('vu11p_', '')
        bin_file = find_file_in_extracted_dir(target_dir, bin_file_name)
        if not bin_file:
            print(f"File '{bin_file_name}' not found in the extracted directory.")
            # raise FileNotFoundError(f"File '{bin_file_name}' not found in the extracted directory.")
            sheet1.at[row[0], 'bin_file'] = None
            continue
        print(f"File '{bin_file_name}' found at: {bin_file}")
        # Move the file to the target directory
        target_path = os.path.join(target_dir_outputs, 'sw_side')
        target_file_path = os.path.join(target_path, bin_file_name)
        print(f"Moving {bin_file} to {target_file_path}")
        shutil.copy(bin_file, target_file_path)
        # Update the sheet1 with the bin file path
        sheet1.at[row[0], 'bin_file'] = target_file_path

    # Remove rows with empty vu11pbinfile or dtb_file or bin_file
    rows_to_remove = []
    print("\n\n")
    for index, row in sheet1.iterrows():
        if pd.isna(row['vu11pbinfile']) or pd.isna(row['dtb_file']) or pd.isna(row['bin_file']):
            print(f"id: {row['id']} missing vu11pbinfile or dtb_file or bin_file")
            # Remove the row
            rows_to_remove.append(index)
    # Remove the rows
    sheet1.drop(rows_to_remove, inplace=True)
    # Reset the index
    sheet1.reset_index(drop=True, inplace=True)

    # Get Image and Zynq DTB
    filename = "Image"
    image_file = find_file_in_extracted_dir(target_dir, filename)
    if not image_file:
        print(f"File '{filename}' not found in the extracted directory.")
        raise FileNotFoundError(f"File '{filename}' not found in the extracted directory.")
    
    target_path = os.path.join(target_dir_outputs, 'sw_side')
    target_file_path = os.path.join(target_path, "Image")
    print(f"Moving {image_file} to {target_file_path}")
    shutil.copy(image_file, target_file_path)
    image_file = os.path.join(target_dir_outputs, 'sw_side', 'Image')

    filename = "zynqmp-vpx-apollo.dtb"
    zynq_dtb_file = find_file_in_extracted_dir(target_dir, filename)
    if not zynq_dtb_file:
        print(f"File '{filename}' not found in the extracted directory.")
        raise FileNotFoundError(f"File '{filename}' not found in the extracted directory.")
    
    target_path = os.path.join(target_dir_outputs, 'sw_side')
    target_file_path = os.path.join(target_path, "devicetree.dtb")
    print(f"Moving {zynq_dtb_file} to {target_file_path}")
    shutil.copy(zynq_dtb_file, target_file_path)
    zynq_dtb_file = os.path.join(target_dir_outputs, 'sw_side', 'devicetree.dtb')

    # Update the sheet1 with the image and zynq dtb file paths to each row
    # Add columns for image and zynq dtb
    sheet1['image_file'] = None
    sheet1['zynq_dtb_file'] = None
    for row in sheet1.iterrows():
        sheet1.at[row[0], 'image_file'] = image_file
        sheet1.at[row[0], 'zynq_dtb_file'] = zynq_dtb_file

    # Save the modified sheet1 to a new Excel file
    output_file = os.path.join(target_dir_outputs, 'ads1100_profiles_final_summary_parsed.xlsx')
    print(f"Saving the modified sheet1 to '{output_file}'")
    sheet1.to_excel(output_file, index=False)

    # Cleanup
    shutil.rmtree(extracted_files)

    return sheet1

if __name__ == "__main__":

    # Check if the file exists
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive_05212025.zip")
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        sys.exit(1)

    # Check if the target directory exists, if not create it
    if not os.path.exists(target_dir_outputs):
        os.makedirs(target_dir_outputs)

    # Handle the zip file
    handle_jenkins_zip(filename)
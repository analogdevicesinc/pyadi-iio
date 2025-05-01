"""Generate JESD config, profiles, and devicetrees for ADSY1100 JESD204B IP core."""

# Requirements:
# uv pip install "git+https://github.com/analogdevicesinc/pyadi-jif.git@tfcollins/ad9084[cplex]"
# uv pip install git+https://github.com/analogdevicesinc/pyadi-dt.git@tfcollins/adsy1100

import os
import sys
import json
import glob
import pandas as pd

# Configs

max_mode_pairs = 4  # Pick the most common pairs of JESD modes
max_allowed_common_lane_rate_Hz = int(21.0e9)  # 21.0 GHz

################################################################################

here = os.path.dirname(os.path.abspath(__file__))
profiles_root_dir = os.path.join(here, "AnalogDevices.Apollo.Profiles")

profile_sub_folders = os.listdir(profiles_root_dir)

df = pd.DataFrame(
    columns=[
        "id",
        "profile_name",
        "bin_filename",
        "device_clock_Hz",
        "core_clock_Hz",
        "common_lane_rate_Hz",
        "rx_jesd_mode",
        "tx_jesd_mode",
        "failed_reason",
        "is_8t8r",
        "jesd_settings",
        "datapath",
        "jif_model",
        "dts_file",
    ]
)

for profile_sub_folder in profile_sub_folders:
    # Find summary.json files in the subfolder
    summary_files = glob.glob(
        os.path.join(profiles_root_dir, profile_sub_folder, "**", "*summary.json"),
        recursive=True,
    )
    for summary_file in summary_files:
        print(f"Processing {summary_file}")
        with open(summary_file, "r") as f:
            summary_data = json.load(f)

        iduc = os.path.basename(summary_file)
        iduc = iduc.replace("_summary.json", "")

        df_row = {
            "id": iduc,
            "profile_name": None,
            "device_clock_Hz": None,
            "core_clock_Hz": None,
            "common_lane_rate_Hz": None,
            "rx_jesd_mode": None,
            "tx_jesd_mode": None,
            "failed_reason": None,
            "is_8t8r": None,
            "jesd_settings": None,
            "datapath": None,
            "jif_model": None,
            "dts_file": None,
            "bin_filename": None,
            "hdl_build_id": None,
        }

        bin_filename = summary_file.replace("_summary.json", ".bin")
        bin_filename = os.path.basename(bin_filename)
        bin_filename_full_path = os.path.join(
            os.path.dirname(summary_file), "blob", bin_filename
        )
        if not os.path.exists(bin_filename_full_path):
            df_row["failed_reason"] = "bin file does not exist"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(
                f"Skipping {summary_file} because bin file does not exist: {bin_filename_full_path}"
            )
            continue
        df_row["bin_filename"] = bin_filename_full_path

        if "is_8t8r" not in summary_data:
            df_row["failed_reason"] = "is_8t8r key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because 'is_8t8r' key is missing")
            continue

        df_row["is_8t8r"] = summary_data["is_8t8r"]

        if summary_data["is_8t8r"]:
            df_row["failed_reason"] = "is_8t8r is True"
            # df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            # Use concat instead of append for better performance
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because it is 8T8R")
            continue

        device_clock_Hz = summary_data["general_info"]["device_clock_Hz"]
        if device_clock_Hz is None:
            df_row["failed_reason"] = "device_clock_Hz key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because 'device_clock_Hz' key is missing")
            continue
        df_row["device_clock_Hz"] = device_clock_Hz

        core_clock_Hz = summary_data["general_info"]["fpga_clock_Hz"]
        if core_clock_Hz is None:
            df_row["failed_reason"] = "core_clock_Hz key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because 'core_clock_Hz' key is missing")
            continue
        df_row["core_clock_Hz"] = core_clock_Hz

        full_profile_filename = summary_file.replace("_summary", "")
        if not os.path.exists(full_profile_filename):
            df_row["failed_reason"] = "full profile file does not exist"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(
                f"Skipping {summary_file} because full profile file does not exist: {full_profile_filename}"
            )
            continue

        common_lane_rate_Hz = summary_data["general_info"]["common_lane_rate_Hz"]
        if common_lane_rate_Hz is None:
            df_row["failed_reason"] = "common_lane_rate_Hz key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(
                f"Skipping {summary_file} because 'common_lane_rate_Hz' key is missing"
            )
            continue
        df_row["common_lane_rate_Hz"] = common_lane_rate_Hz

        with open(full_profile_filename, "r") as f:
            profile_data = json.load(f)

        # Parse datapath config
        path = 0
        cddc_decimation = summary_data["rx_routes"][path]["cdrc"]
        fddc_decimation = summary_data["rx_routes"][path]["fdrc"]
        cduc_interpolation = summary_data["tx_routes"][path]["cdrc"]
        fdrc_interpolation = summary_data["tx_routes"][path]["fdrc"]
        df_row["datapath"] = {
            "cddc_decimation": cddc_decimation,
            "fddc_decimation": fddc_decimation,
            "cduc_interpolation": cduc_interpolation,
            "fdrc_interpolation": fdrc_interpolation,
        }

        # Parse JESD204 config
        link_index = 0
        lane_index = 0
        rx_jesd_mode = profile_data["jtx"][link_index]["tx_link_cfg"][lane_index][
            "quick_mode_id"
        ]
        tx_jesd_mode = profile_data["jrx"][link_index]["rx_link_cfg"][lane_index][
            "quick_mode_id"
        ]

        # "l_minus1": 7,
        #   "f_minus1": 0,
        #   "m_minus1": 3,
        #   "s_minus1": 0,
        #   "high_dens": true,
        #   "k_minus1": 255,
        #   "n_minus1": 15,
        #   "np_minus1": 15,
        df_row["jesd_settings"] = {}
        for rtx, cfg in zip(["jtx", "jrx"], ["tx_link_cfg", "rx_link_cfg"]):
            df_row["jesd_settings"][rtx] = {}
            for setting, jesd_setting_key in zip(
                ["L", "F", "M", "S", "HD", "K", "N", "NP"],
                [
                    "l_minus1",
                    "f_minus1",
                    "m_minus1",
                    "s_minus1",
                    "high_dens",
                    "k_minus1",
                    "n_minus1",
                    "np_minus1",
                ],
            ):
                if (
                    jesd_setting_key
                    not in profile_data[rtx][link_index][cfg][lane_index]
                ):
                    df_row["failed_reason"] = (
                        f"{jesd_setting_key} key missing in tx_link_cfg"
                    )
                    df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
                    print(
                        f"Skipping {summary_file} because '{jesd_setting_key}' key is missing in tx_link_cfg"
                    )
                    continue
                if setting == "HD":
                    df_row["jesd_settings"][rtx][setting] = profile_data[rtx][
                        link_index
                    ][cfg][lane_index][jesd_setting_key]
                else:
                    df_row["jesd_settings"][rtx][setting] = (
                        int(
                            profile_data[rtx][link_index][cfg][lane_index][
                                jesd_setting_key
                            ]
                        )
                        + 1
                    )
        print(f"JESD settings: {df_row['jesd_settings']}")

        if rx_jesd_mode is None:
            df_row["failed_reason"] = "rx_jesd_mode key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because 'rx_jesd_mode' key is missing")
            continue
        df_row["rx_jesd_mode"] = rx_jesd_mode
        if tx_jesd_mode is None:
            df_row["failed_reason"] = "tx_jesd_mode key missing"
            df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
            print(f"Skipping {summary_file} because 'tx_jesd_mode' key is missing")
            continue
        df_row["tx_jesd_mode"] = tx_jesd_mode
        profile_name = os.path.basename(full_profile_filename)
        df_row["profile_name"] = profile_name
        df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)

# Remove any rows where 'failed_reason' is not None
df = df[df["failed_reason"].isnull()]

# Save the DataFrame to a CSV file
output_csv_path = os.path.join(here, "ads1100_profiles_summary.csv")
df.to_csv(output_csv_path, index=False)
print(f"Summary CSV file created at: {output_csv_path}")

# Save the DataFrame to a Excel file
output_excel_path = os.path.join(here, "ads1100_profiles_summary.xlsx")
df.to_excel(output_excel_path, index=False)
print(f"Summary Excel file created at: {output_excel_path}")


# # Count occurrences of each JESD mode
# tx_jesd_mode_counts = df['tx_jesd_mode'].value_counts()
# rx_jesd_mode_counts = df['rx_jesd_mode'].value_counts()
# print("\nTX JESD Mode Counts:")
# print(tx_jesd_mode_counts)
# print("\nRX JESD Mode Counts:")
# print(rx_jesd_mode_counts)

# # Max JESD modes to support
# max_jesd_modes = 4
# # Pick the most common JESD modes
# top_tx_jesd_modes = tx_jesd_mode_counts.nlargest(max_jesd_modes).index.tolist()
# top_rx_jesd_modes = rx_jesd_mode_counts.nlargest(max_jesd_modes).index.tolist()
# print(f"\nTop {max_jesd_modes} TX JESD Modes: {top_tx_jesd_modes}")
# print(f"Top {max_jesd_modes} RX JESD Modes: {top_rx_jesd_modes}")

# # Filter the DataFrame to only include the top JESD modes
# df_filtered = df[df['tx_jesd_mode'].isin(top_tx_jesd_modes) & df['rx_jesd_mode'].isin(top_rx_jesd_modes)]

# Count occurrences of pairs (tx_jesd_mode, rx_jesd_mode) of JESD modes
mode_pairs = (
    df.groupby(["tx_jesd_mode", "rx_jesd_mode"]).size().reset_index(name="count")
)
# sort the pairs by count in descending order
mode_pairs = mode_pairs.sort_values(by="count", ascending=False)
print("\nJESD Mode Pairs Counts:")
print(mode_pairs)

top_mode_pairs = mode_pairs.nlargest(max_mode_pairs, "count")
print(f"\nTop {max_mode_pairs} JESD Mode Pairs:")
print(top_mode_pairs)

# Filter the DataFrame to only include the top JESD mode pairs
df_filtered = df[
    df.set_index(["tx_jesd_mode", "rx_jesd_mode"]).index.isin(
        top_mode_pairs.set_index(["tx_jesd_mode", "rx_jesd_mode"]).index
    )
]

# Determine max common_lane_rate_Hz for each pair of JESD modes
# Filter the DataFrame to only include rows where common_lane_rate_Hz is less than or equal to max_allowed_common_lane_rate_Hz
df_filtered = df_filtered[
    df_filtered["common_lane_rate_Hz"] <= max_allowed_common_lane_rate_Hz
]
max_common_lane_rate_Hz = df_filtered["common_lane_rate_Hz"].max()
print(f"\nMax common_lane_rate_Hz after filtering: {max_common_lane_rate_Hz}")

print("\nFiltered DataFrame after applying max common_lane_rate_Hz:")
print(df_filtered)


# Add make commands for each row
def gen_make_cmd(row):
    mode = "64B66B"
    make_cmd = (
        f"JESD_MODE={mode} "
        + f"RX_RATE={row['common_lane_rate_Hz']/1e9:.4f} TX_RATE={row['common_lane_rate_Hz']/1e9:.4f} "
        + f"RX_JESD_M={row['jesd_settings']['jrx']['M']} TX_JESD_M={row['jesd_settings']['jtx']['M']} "
        + f"RX_JESD_L={row['jesd_settings']['jrx']['L']} TX_JESD_L={row['jesd_settings']['jtx']['L']} "
        + f"RX_JESD_S={row['jesd_settings']['jrx']['S']} TX_JESD_S={row['jesd_settings']['jtx']['S']} "
        + f"RX_JESD_NP={row['jesd_settings']['jrx']['NP']} TX_JESD_NP={row['jesd_settings']['jtx']['NP']} "
        + f"RX_B_RATE={row['common_lane_rate_Hz']/1e9:.4f} TX_B_RATE={row['common_lane_rate_Hz']/1e9:.4f} "
        + f"RX_B_JESD_M={row['jesd_settings']['jrx']['M']} TX_B_JESD_M={row['jesd_settings']['jtx']['M']} "
        + f"RX_B_JESD_L={row['jesd_settings']['jrx']['L']} TX_B_JESD_L={row['jesd_settings']['jtx']['L']} "
        + f"RX_B_JESD_S={row['jesd_settings']['jrx']['S']} TX_B_JESD_S={row['jesd_settings']['jtx']['S']} "
        + f"RX_B_JESD_NP={row['jesd_settings']['jrx']['NP']} TX_B_JESD_NP={row['jesd_settings']['jtx']['NP']}"
    )

    print("Make command:")
    print(make_cmd)
    return make_cmd


# Add make commands to the DataFrame
df_filtered["make_command"] = df_filtered.apply(gen_make_cmd, axis=1)
print("\nFiltered DataFrame with make commands:")
print(df_filtered)

################################################################################
# Generate DT files for each profile

def generate_jif_model(df_filtered):
    import adijif

    # df_filtered

    vcxo = int(125e6)
    cddc_dec = df_filtered.iloc[0]["datapath"]["cddc_decimation"]
    fddc_dec = df_filtered.iloc[0]["datapath"]["fddc_decimation"]
    converter_rate = int(df_filtered.iloc[0]["device_clock_Hz"])

    sys = adijif.system("ad9084_rx", "ltc6952", "xilinx", vcxo, solver="CPLEX")

    sys.fpga.setup_by_dev_kit_name("adsy1100")
    sys.converter.sample_clock = converter_rate / (cddc_dec * fddc_dec)
    sys.converter.datapath.cddc_decimations = [cddc_dec] * 4
    sys.converter.datapath.fddc_decimations = [fddc_dec] * 8
    sys.converter.datapath.fddc_enabled = [True] * 8

    sys.converter.clocking_option = "direct"
    sys.add_pll_inline("adf4382", vcxo, sys.converter)
    # sys.add_pll_sysref("adf4030", vcxo, sys.converter, sys.fpga)

    sys.clock.minimize_feedback_dividers = False
    M = df_filtered.iloc[0]["jesd_settings"]["jrx"]["M"]
    L = df_filtered.iloc[0]["jesd_settings"]["jrx"]["L"]
    S = df_filtered.iloc[0]["jesd_settings"]["jrx"]["S"]
    Np = df_filtered.iloc[0]["jesd_settings"]["jrx"]["NP"]

    mode_rx = adijif.utils.get_jesd_mode_from_params(
        sys.converter, M=M, L=L, S=S, Np=Np, jesd_class="jesd204c"
    )
    # print(f"RX JESD Mode: {mode_rx}")
    assert mode_rx
    mode_rx = mode_rx[0]["mode"]

    sys.converter.set_quick_configuration_mode(mode_rx, "jesd204c")

    # print(f"Lane rate: {sys.converter.bit_clock/1e9} Gbps")
    # print(f"Needed Core clock: {sys.converter.bit_clock/66} MHz")

    sys.converter._check_clock_relations()

    cfg = sys.solve()

    del sys

    # pprint(cfg)

    return cfg


###############################################
for row in df_filtered.itertuples():
    print(f"Generating JIF model for profile: {row.profile_name}")
    cfg = generate_jif_model(df_filtered)
    # Add cfg to the DataFrame
    row_index = row.Index
    df_filtered.at[row_index, "jif_model"] = cfg


def generate_dt_files(row, folder="dts_files"):
    from pprint import pprint
    import adidt

    print(f"Generating DT for profile: {row['profile_name']}")
    converter = {
        "device_profile_name": row["profile_name"],
        "device_clock_Hz": row["device_clock_Hz"],
        "core_clock_Hz": row["core_clock_Hz"],
        "common_lane_rate_Hz": row["common_lane_rate_Hz"],
        "rx_jesd_mode": row["rx_jesd_mode"],
        "tx_jesd_mode": row["tx_jesd_mode"],
        "jesd_settings": row["jesd_settings"],
    }

    if not os.path.exists(folder):
        os.makedirs(folder)

    som = adidt.adsy1100_vu11p()
    som.output_filename = os.path.join(
        folder, f"vu11p_{row['profile_name'].replace('.json','')}.dts"
    )

    jif_profile = row["jif_model"]
    clock, fpga = som.map_clocks_to_board_layout(jif_profile)

    pprint(clock)
    pprint(fpga)

    som.gen_dt(clock=clock, fpga=fpga, converter=converter)

    return som.output_filename


for index, row in df_filtered.iterrows():
    dt_file = generate_dt_files(row)
    print(f"Device tree file generated: {dt_file}")
    df_filtered.at[index, "dts_file"] = dt_file


################################################################################

# Save the filtered DataFrame to a CSV file
output_filtered_csv_path = os.path.join(here, "ads1100_profiles_filtered_summary.csv")
df_filtered.to_csv(output_filtered_csv_path, index=False)
print(f"Filtered summary CSV file created at: {output_filtered_csv_path}")
# Save the filtered DataFrame to a Excel file
output_filtered_excel_path = os.path.join(
    here, "ads1100_profiles_filtered_summary.xlsx"
)
df_filtered.to_excel(output_filtered_excel_path, index=False)
print(f"Filtered summary Excel file created at: {output_filtered_excel_path}")

# Generate the simplified list of unique JESD mode pairs using the max lane rate for that pair
unique_mode_pairs = (
    df_filtered.groupby(["tx_jesd_mode", "rx_jesd_mode"])
    .agg({"common_lane_rate_Hz": "max"})
    .reset_index()
)
print("\nUnique JESD Mode Pairs with Max Lane Rate:")
print(unique_mode_pairs)


# Generate groovy Jenkinsfile structure to build variants in parallel
IDs = []
txt = "def boardNames = [\n"
txt += '    "apollo_som_vu11p": [\n'
for row in unique_mode_pairs.itertuples():
    is_last = row.Index == len(unique_mode_pairs) - 1
    row = row._asdict()  # Convert namedtuple to a regular dict
    print(f"Processing profile: {row}")
    # Get make command that matches the JESD mode pair
    tx_mode = row["tx_jesd_mode"]
    rx_mode = row["rx_jesd_mode"]
    common_lane_rate_Hz = row["common_lane_rate_Hz"]
    make_command = df_filtered[
        (df_filtered["tx_jesd_mode"] == tx_mode)
        & (df_filtered["rx_jesd_mode"] == rx_mode)
        & (df_filtered["common_lane_rate_Hz"] == common_lane_rate_Hz)
    ]["make_command"].values
    if len(make_command) > 0:
        make_command = make_command[0]
        # Generate a unique identifier for the board and JESD mode pair
        board_id = f"ID_T{tx_mode}_R{rx_mode}_LR{int(common_lane_rate_Hz/1e6)}"
        txt += f'       "{board_id}": "{make_command}"' + ("" if is_last else ",\n")
        IDs.append(board_id)

txt += """
    ],
    "apollo_som_zu4eg": [
        "ALL": ""
    ]
]
"""

print(txt)

# Add IDs which config can use
for index, row in df_filtered.iterrows():
    # Get the index of unique_mode_pairs that matches the tx_jesd_mode and rx_jesd_mode
    tx_mode = row["tx_jesd_mode"]
    rx_mode = row["rx_jesd_mode"]
    index_of_pair = unique_mode_pairs[
        (unique_mode_pairs["tx_jesd_mode"] == tx_mode)
        & (unique_mode_pairs["rx_jesd_mode"] == rx_mode)
    ].index

    u_row = None if index_of_pair.empty else unique_mode_pairs.loc[index_of_pair[0]]
    if u_row is None:
        raise ValueError(
            f"No matching JESD mode pair found for tx_mode={tx_mode}, rx_mode={rx_mode}"
        )

    hd_build_id = f"ID_T{tx_mode}_R{rx_mode}_LR{int(u_row['common_lane_rate_Hz']/1e6)}"

    # Add the hd_build_id to the DataFrame
    print(f"Assigning hd_build_id: {hd_build_id} to profile: {row['profile_name']}")
    df_filtered.at[index, "hdl_build_id"] = hd_build_id

################################################################################
# Move things to common place
# Move the folder
import shutil

target_folder = os.path.join(here, "adsy1100_configs")
if os.path.exists(target_folder):
    shutil.rmtree(target_folder)
os.makedirs(target_folder)

# Move the generated device tree files to the target folder
shutil.move("dts_files", target_folder)
os.makedirs(os.path.join(target_folder, "bin_files"), exist_ok=True)
# Copy the generated bin files to the target folder
for index, row in df_filtered.iterrows():
    bin_file_path = row["bin_filename"]
    if os.path.exists(bin_file_path):
        shutil.copy(bin_file_path, os.path.join(target_folder, "bin_files"))
    else:
        raise FileNotFoundError(f"Bin file does not exist: {bin_file_path}")

# Save the final DataFrame with hd_build_id to a CSV file in the target folder
output_final_csv_path = os.path.join(
    target_folder, "ads1100_profiles_final_summary.csv"
)
df_filtered.to_csv(output_final_csv_path, index=False)
print(f"Final summary CSV file created at: {output_final_csv_path}")
# Save the final DataFrame with hd_build_id to a Excel file in the target folder
output_final_excel_path = os.path.join(
    target_folder, "ads1100_profiles_final_summary.xlsx"
)
df_filtered.to_excel(output_final_excel_path, index=False)
print(f"Final summary Excel file created at: {output_final_excel_path}")

# Save text to a file in the target folder
output_jenkinsfile_path = os.path.join(target_folder, "Jenkinsfile_part.groovy")
with open(output_jenkinsfile_path, "w") as f:
    f.write(txt)
print(f"Jenkinsfile part created at: {output_jenkinsfile_path}")

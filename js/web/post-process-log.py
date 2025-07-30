import re
import time
import sys
import pandas as pd
import json

def extract_log_error(log_file, output_file):
    try:
        with open(log_file, 'r',encoding='utf-8') as file:
            lines = file.readlines()

        log_pattern = re.compile(r'LOG: ')
        error_pattern = re.compile(r'ERROR: ')
        webnn_test_model_name_pattern = re.compile(r'\[webnn\]\s+(.*)')
        pass_status = re.compile(r'.+\×')
        model_test_opset_pattern =  re.compile(r'#ModelTest#.*(opset\d+).*')
        case_results = {}

        for i in range(2, len(lines)):
            if webnn_test_model_name_pattern.search(lines[i]) and log_pattern.search(lines[i-1]) and pass_status.search(lines[i+1]):
                error_message = ""
                opset_match = re.search(r'opset(\d+)', lines[i-1])
                case = webnn_test_model_name_pattern.search(lines[i]).group(1)

                if opset_match:
                    # cases during loading model process
                    opset = opset_match.group(0)
                    error_message = lines[i-2].strip()

                else:
                    # cases during running test model
                    j = i-1
                    opset = "_"
                    while j >= 0 and (log_pattern.search(lines[j]) or not error_pattern.search(lines[j])):
                        error_message = lines[j].strip() + "\n" + error_message
                        j -= 1

                    # loop to find the opset of this test model
                    while j >= 0:
                        opset_match = model_test_opset_pattern.search(lines[j])
                        if opset_match:
                            opset = opset_match.group(1)
                            break
                        j -= 1

                # remove color codes from error message
                error_message = re.sub(r'\x1b\[[0-9;]*m', '', error_message)
                # remove the unused string
                error_message = re.sub(r'LOG: \'e ', '\'', error_message)
                # remove date message in format
                error_message = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}', '', error_message)
                if case not in case_results:
                    case_results[case] = {}
                case_results[case][opset] = error_message

        case_results["total"] = len(case_results)

        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(case_results, json_file, ensure_ascii=False, indent=4)
        print(f"Test results are successfully written to '{output_file}'")

        # Convert the JSON into a flat structure for easier table representation
        flattened_data = []
        for test_case, opsets in case_results.items():
            # Check if the opsets is a dictionary before trying to access its items
            if isinstance(opsets, dict):
                for opset, error_message in opsets.items():
                    flattened_data.append([test_case, opset, error_message])
            else:
                print(f"Warning: The value for test case '{test_case}' is not a dictionary. Skipping.")

        # Create a DataFrame
        df = pd.DataFrame(flattened_data, columns=["Test Case", "Opset", "Error Message"])
        excel_output_file = output_file.replace('.json', '.xlsx')

        # Export to Excel
        df.to_excel(excel_output_file, index=False, engine="openpyxl")
        print(f"Test results are successfully written to '{excel_output_file}'")

    except Exception as e:
        print(f"Error occurred: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python post_process_log.py <log_file_path>")
        sys.exit(1)

    log_file = sys.argv[1]
    output_path = sys.argv[2]
    print("Prepare to post process the log")
    start_time = time.time()
    extract_log_error(log_file, output_path)
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"Post process time elapsed: {elapsed_time} s")

if __name__ == "__main__":
    main()

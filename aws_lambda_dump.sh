#!/bin/bash

# Script: aws_lambda_dump.sh
# Description: Downloads the code packages (.zip files) for all AWS Lambda functions
#              in a specified region.
# Dependencies: aws-cli, curl, jq (optional, but recommended for robust JSON parsing if needed)
# Usage: ./aws_lambda_dump.sh [aws-region] [output-directory]
#        Example: ./aws_lambda_dump.sh us-west-2 ./lambda_backups
#        If arguments are omitted, defaults will be used.

# --- Configuration ---
# Default AWS Region (can be overridden by the first command-line argument)
DEFAULT_REGION="us-west-2"
# Default Output Directory (can be overridden by the second command-line argument)
# Creates a timestamped directory inside the default base directory.
DEFAULT_BASE_OUTPUT_DIR="lambda_function_code_dumps"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Determine Region and Output Directory from arguments or defaults
REGION="${1:-$DEFAULT_REGION}"
BASE_OUTPUT_DIR="${2:-$DEFAULT_BASE_OUTPUT_DIR}"
OUTPUT_DIR="${BASE_OUTPUT_DIR}/dump_${REGION}_${TIMESTAMP}"

# --- Check Dependencies ---
if ! command -v aws &> /dev/null; then
    echo "Error: aws-cli is not installed or not in PATH."
    echo "Please install it and configure your AWS credentials."
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed or not in PATH."
    exit 1
fi

echo "Starting AWS Lambda Function Code Dump"
echo "----------------------------------------"
echo "AWS Region:       $REGION"
echo "Output Directory: $OUTPUT_DIR"
echo "----------------------------------------"

# Create the main output directory
mkdir -p "$OUTPUT_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create output directory '$OUTPUT_DIR'."
    exit 1
fi
echo "Created base output directory: $OUTPUT_DIR"
echo "" # Newline for readability

# --- Get List of Function Names ---
echo "Fetching list of function names from region '$REGION'..."
# Using process substitution <(...) and 'while read' loop for robustness
# Handles function names with spaces or special characters correctly.
function_list_command="aws lambda list-functions --query 'Functions[*].FunctionName' --output text --region \"$REGION\""
mapfile -t function_names < <(eval "$function_list_command") # Read names into an array

# Check if the command failed or returned no functions
if [ $? -ne 0 ]; then
    echo "Error: Failed to list Lambda functions. Check AWS credentials and region."
    # Attempt to clean up the created directory
    rmdir "$OUTPUT_DIR" 2>/dev/null
    exit 1
fi

if [ ${#function_names[@]} -eq 0 ]; then
    echo "No Lambda functions found in region '$REGION'."
     # Attempt to clean up the created directory
    rmdir "$OUTPUT_DIR" 2>/dev/null
    exit 0
fi

echo "Found ${#function_names[@]} functions. Starting download process..."
echo ""

# --- Loop Through Each Function Name ---
processed_count=0
skipped_count=0
for func_name in "${function_names[@]}"; do
    echo "--- Processing function: '$func_name' ---"

    # 1. Create a directory for the function's code
    # Replace characters potentially problematic for filenames/directories (like '/')
    safe_func_name=$(echo "$func_name" | tr '/' '_')
    func_dir="$OUTPUT_DIR/$safe_func_name"
    mkdir -p "$func_dir"
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to create directory '$func_dir' for function '$func_name'. Skipping."
        ((skipped_count++))
        continue
    fi
    echo "Created directory: $func_dir"

    # 2. Get the pre-signed S3 URL for the function's code package
    echo "Getting download URL..."
    # Capture stderr to check for AWS CLI errors, redirect actual URL to stdout
    url_output=$(aws lambda get-function --function-name "$func_name" --query 'Code.Location' --output text --region "$REGION" 2>&1)
    aws_exit_code=$?

    # Check if AWS CLI command failed or returned an empty/invalid URL
    if [ $aws_exit_code -ne 0 ] || [ -z "$url_output" ] || [[ ! "$url_output" =~ ^https?:// ]]; then
        echo "Warning: Failed to get a valid download URL for function '$func_name'."
        echo "         AWS CLI Output/Error: $url_output"
        echo "         Skipping this function."
        # Optional: remove the directory created for this function if it's empty
        rmdir "$func_dir" 2>/dev/null
        ((skipped_count++))
        continue
    fi
    download_url="$url_output"
    echo "Download URL obtained."

    # 3. Download the code package using curl
    output_zip_path="$func_dir/$safe_func_name.zip"
    echo "Downloading code to '$output_zip_path'..."
    # Use -L to follow redirects (important for S3 presigned URLs)
    # Use -f to fail silently on server errors (HTTP errors) but return non-zero exit code
    # Use -s for silent mode (no progress meter)
    # Use -S to show errors even with -s
    # Use --connect-timeout and --max-time for robustness
    curl -f -s -S -L "$download_url" --connect-timeout 15 --max-time 300 -o "$output_zip_path"
    curl_exit_code=$?

    if [ $curl_exit_code -ne 0 ]; then
        echo "Warning: Failed to download code for '$func_name' (curl exit code: $curl_exit_code)."
        echo "         URL: $download_url"
        echo "         Skipping this function."
        # Optional: remove potentially incomplete zip file
        rm -f "$output_zip_path" 2>/dev/null
        # Optional: remove the directory
        rmdir "$func_dir" 2>/dev/null
        ((skipped_count++))
    else
        echo "Successfully downloaded '$safe_func_name.zip'."
        ((processed_count++))
    fi
    echo "" # Newline for readability between functions

done

echo "----------------------------------------"
echo "Lambda function code dump completed."
echo "Summary:"
echo "  Total functions found:   ${#function_names[@]}"
echo "  Successfully downloaded: $processed_count"
echo "  Skipped / Errors:      $skipped_count"
echo "  Code saved in:         '$OUTPUT_DIR'"
echo "----------------------------------------"

exit 0
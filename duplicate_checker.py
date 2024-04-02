import os
import hashlib
import json


def calculate_hash(filepath):
    """
    Calculate the SHA-256 hash of the file.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def remove_duplicates(directory):
    """
    Remove duplicate PDFs and record their information.
    """
    records = {}
    directory_info = {}
    total_original_count = 0
    total_deleted_count = 0
    total_remaining_count = 0

    for root, dirs, files in os.walk(directory):
        pdf_files = [file for file in files if file.endswith(".pdf")]
        total_files = len(pdf_files)
        deleted_files = []

        for file in pdf_files:
            filepath = os.path.join(root, file)
            file_hash = calculate_hash(filepath)

            # Check for duplicates
            if file in records and records[file] == file_hash:
                # Record the deleted file's info
                deleted_file_info = {
                    "file_name": file,
                    "file_path": os.path.relpath(filepath, start=directory)
                }
                deleted_files.append(deleted_file_info)

                # Delete the file
                print(f"Deleting duplicate file: {filepath}")
                os.remove(filepath)
            else:
                records[file] = file_hash

        if total_files > 0:
            dir_key = os.path.relpath(root, start=directory)
            directory_info[dir_key] = {
                "original_count": total_files,
                "deleted_count": len(deleted_files),
                "remaining_count": total_files - len(deleted_files),
                "deleted_files": deleted_files
            }
            total_original_count += total_files
            total_deleted_count += len(deleted_files)
            total_remaining_count += total_files - len(deleted_files)

    return directory_info, total_original_count, total_deleted_count, total_remaining_count


def save_to_json(data, filename):
    """Save the data to a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


# Directory containing the PDFs
pdf_directory = "pdfs"

# Remove duplicates and get info about directories
directories_info, total_original, total_deleted, total_remaining = remove_duplicates(pdf_directory)

# Prepare JSON structure
json_data = {
    "total_original_count": total_original,
    "total_deleted_count": total_deleted,
    "total_remaining_count": total_remaining,
    "directories": directories_info
}

# Save to JSON file
json_filename = "deleted_pdfs_record.json"
save_to_json(json_data, json_filename)

print(f"Record of deleted files saved to {json_filename}")

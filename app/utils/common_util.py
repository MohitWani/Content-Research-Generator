import os


def truncate_filename(original_file_name: str, max_length: int = 200) -> str:
    filename_without_ext, ext = os.path.splitext(
        original_file_name
    )  # Split filename into name and extension
    if len(filename_without_ext) < max_length:
        return original_file_name
    truncated_name = filename_without_ext[:max_length]  # Truncate only the name part
    new_filename = truncated_name + ext  # Add the extension back
    print(
        'Original filename was too long: ',
        original_file_name,
        ' Truncated to: ',
        new_filename,
    )
    return new_filename

#!/usr/bin/env python3
"""
Filename Converter Script
Converts all filenames in a folder to slug-case (kebab-case) or snake_case
"""

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple


def to_slug_case(text: str) -> str:
    """
    Convert text to slug-case (kebab-case)
    Example: "Hello World.txt" -> "hello-world.txt"
    """
    # Split filename and extension
    name, ext = os.path.splitext(text)

    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", name.lower())  # Remove special chars except hyphens
    slug = re.sub(
        r"[-\s]+", "-", slug
    )  # Replace spaces and multiple hyphens with single hyphen
    slug = slug.strip("-")  # Remove leading/trailing hyphens

    return slug + ext.lower()


def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case
    Example: "Hello World.txt" -> "hello_world.txt"
    """
    # Split filename and extension
    name, ext = os.path.splitext(text)

    # Convert to lowercase and replace spaces/special chars with underscores
    snake = re.sub(
        r"[^\w\s_]", "", name.lower()
    )  # Remove special chars except underscores
    snake = re.sub(
        r"[_\s]+", "_", snake
    )  # Replace spaces and multiple underscores with single underscore
    snake = snake.strip("_")  # Remove leading/trailing underscores

    return snake + ext.lower()


def get_files_in_directory(directory: str) -> List[str]:
    """Get all files (not directories) in the specified directory"""
    try:
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory '{directory}' does not exist")

        files = [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
        return files
    except Exception as e:
        print(f"Error reading directory: {e}")
        return []


def preview_changes(directory: str, conversion_type: str) -> List[Tuple[str, str]]:
    """Preview what the filenames will look like after conversion"""
    files = get_files_in_directory(directory)
    changes = []

    converter = to_slug_case if conversion_type == "slug" else to_snake_case

    for filename in files:
        new_name = clean_filename(converter(filename))
        if filename != new_name:
            changes.append((filename, new_name))

    return changes


def rename_files(directory: str, conversion_type: str, dry_run: bool = False) -> None:
    """Rename files in the directory"""
    changes = preview_changes(directory, conversion_type)

    if not changes:
        print("No files need to be renamed.")
        return

    print(f"\nFiles to be renamed ({conversion_type}-case):")
    print("-" * 60)
    for old_name, new_name in changes:
        print(f"{old_name} -> {new_name}")

    if dry_run:
        print(f"\nDry run complete. {len(changes)} files would be renamed.")
        return

    # Ask for confirmation
    response = (
        input(f"\nDo you want to rename {len(changes)} files? (y/N): ").strip().lower()
    )
    if response not in ["y", "yes"]:
        print("Operation cancelled.")
        return

    # Perform the renaming
    success_count = 0
    error_count = 0

    for old_name, new_name in changes:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)

        try:
            # Check if target file already exists
            if os.path.exists(new_path):
                print(f"Warning: '{new_name}' already exists. Skipping '{old_name}'")
                continue

            os.rename(old_path, new_path)
            print(f"✓ Renamed: {old_name} -> {new_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ Error renaming '{old_name}': {e}")
            error_count += 1

    print(f"\nRenaming complete!")
    print(f"Successfully renamed: {success_count} files")
    if error_count > 0:
        print(f"Errors encountered: {error_count} files")


def remove_vietnamese_accents(text):
    """Remove Vietnamese accents and convert to ASCII"""
    # Vietnamese character mapping
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
        'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
        'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
        'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
        'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
        'đ': 'd',
        # Uppercase versions
        'À': 'A', 'Á': 'A', 'Ạ': 'A', 'Ả': 'A', 'Ã': 'A',
        'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ậ': 'A', 'Ẩ': 'A', 'Ẫ': 'A',
        'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ặ': 'A', 'Ẳ': 'A', 'Ẵ': 'A',
        'È': 'E', 'É': 'E', 'Ẹ': 'E', 'Ẻ': 'E', 'Ẽ': 'E',
        'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ệ': 'E', 'Ể': 'E', 'Ễ': 'E',
        'Ì': 'I', 'Í': 'I', 'Ị': 'I', 'Ỉ': 'I', 'Ĩ': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ọ': 'O', 'Ỏ': 'O', 'Õ': 'O',
        'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ộ': 'O', 'Ổ': 'O', 'Ỗ': 'O',
        'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ợ': 'O', 'Ở': 'O', 'Ỡ': 'O',
        'Ù': 'U', 'Ú': 'U', 'Ụ': 'U', 'Ủ': 'U', 'Ũ': 'U',
        'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ự': 'U', 'Ử': 'U', 'Ữ': 'U',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỵ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y',
        'Đ': 'D'
    }
    
    # Replace Vietnamese characters
    result = ''
    for char in text:
        result += vietnamese_map.get(char, char)
    
    return result

def clean_filename(filename):
    """Clean filename for cloud storage compatibility"""
    # Split name and extension
    name, ext = os.path.splitext(filename)
    
    # Remove double extensions
    if name.endswith('.txt'):
        name = name[:-4]
        if not ext:
            ext = '.txt'
    
    # Remove Vietnamese accents
    clean_name = remove_vietnamese_accents(name)
    
    # Replace special characters with hyphens
    clean_name = re.sub(r'[^\w\s-]', '', clean_name)
    
    # Replace spaces and underscores with hyphens
    clean_name = re.sub(r'[\s_]+', '-', clean_name)
    
    # Remove multiple consecutive hyphens
    clean_name = re.sub(r'-+', '-', clean_name)
    
    # Remove leading/trailing hyphens
    clean_name = clean_name.strip('-')
    
    # Convert to lowercase
    clean_name = clean_name.lower()
    
    return clean_name + ext.lower()


def main():
    parser = argparse.ArgumentParser(
        description="Convert filenames to slug-case or snake_case",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python filename_converter.py /path/to/folder --type slug
  python filename_converter.py . --type snake --dry-run
  python filename_converter.py ~/Documents --type slug
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing files to rename (default: current directory)",
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=["slug", "snake"],
        default="slug",
        help="Conversion type: slug (kebab-case) or snake (snake_case) (default: slug)",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview changes without actually renaming files",
    )

    args = parser.parse_args()

    # Convert to absolute path
    directory = os.path.abspath(args.directory)

    print(f"Directory: {directory}")
    print(f"Conversion type: {args.type}-case")
    print(f"Mode: {'Dry run' if args.dry_run else 'Live rename'}")

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        return

    rename_files(directory, args.type, args.dry_run)


if __name__ == "__main__":
    main()

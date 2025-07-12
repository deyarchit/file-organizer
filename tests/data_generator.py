import os
import random
import shutil


def create_themed_test_files_with_nesting(
    base_dir="test_files_with_nesting",
    themes=None,
    num_files_per_theme=3,
    min_file_size_kb=1,
    max_file_size_kb=10,
    file_extensions=None,
    max_nesting_depth=3,  # NEW: Maximum depth of folder nesting
    min_nesting_depth=0,  # NEW: Minimum depth (0 for files directly in base_dir)
    seed=42,
):
    """
    Creates a directory containing dummy files with names based on specified themes,
    including various levels of folder nesting.

    Args:
        base_dir (str): The name of the directory where test files will be created.
                        If it exists, it will be recreated (contents deleted).
        themes (list): A list of theme names to use in file names. If None,
                       a default list of common themes will be used.
        num_files_per_theme (int): Number of files to create for each theme.
        min_file_size_kb (int): Minimum size of each dummy file in KB.
        max_file_size_kb (int): Maximum size of each dummy file in KB.
        file_extensions (list): A list of file extensions to use. If None,
                                a default list of common extensions will be used.
        max_nesting_depth (int): Maximum number of subdirectories to create.
                                 e.g., 0 = no subfolders, 1 = one level, 2 = two levels.
        min_nesting_depth (int): Minimum number of subdirectories (0 for direct files).
        seed (int): Seed for the random number generator to ensure reproducible results.
    """
    random.seed(seed)

    if themes is None:
        themes = [
            "documents",
            "photos",
            "videos",
            "music",
            "work",
            "personal",
            "downloads",
            "archives",
            "notes",
            "reports",
            "travel",
            "recipes",
        ]

    if file_extensions is None:
        file_extensions = [
            ".txt",
            ".pdf",
            ".docx",
            ".xlsx",
            ".jpg",
            ".png",
            ".mp4",
            ".mp3",
            ".zip",
            ".rar",
            ".md",
            ".py",
            ".json",
        ]

    # --- Setup the base directory ---
    if os.path.exists(base_dir):
        print(f"Removing existing directory: {base_dir}")
        shutil.rmtree(base_dir)  # DANGER: This deletes the directory and its contents!
        # Use with caution in production code.
    os.makedirs(base_dir)
    print(f"Created base directory: {os.path.abspath(base_dir)}")

    created_files_list = []

    # --- Create files with varying nesting ---
    for theme in themes:
        for i in range(num_files_per_theme):
            # Determine random nesting depth for this file
            current_depth = random.randint(min_nesting_depth, max_nesting_depth)

            # Build the nested path
            current_dir = base_dir
            for d in range(current_depth):
                # Use a random subfolder name, possibly related to theme or just generic
                subfolder_name = random.choice(
                    [
                        theme.replace(" ", "_") + "_sub",
                        "subfolder_"
                        + str(random.randint(1, 5)),  # Generic subfolder names
                        random.choice(["alpha", "beta", "gamma"]),  # More generic
                    ]
                )
                current_dir = os.path.join(current_dir, subfolder_name)
                os.makedirs(
                    current_dir, exist_ok=True
                )  # Create directory if it doesn't exist

            # Randomly pick an extension
            extension = random.choice(file_extensions)

            # Generate a more descriptive and theme-related name
            file_name_parts = [
                theme.replace(" ", "_"),  # Replace spaces for cleaner filenames
                str(i + 1),  # Add a number to make files unique within a theme
                random.choice(
                    ["draft", "final", "temp", "review", "backup", "version"]
                ),  # Add some variety
            ]
            file_name = "_".join(file_name_parts) + extension

            file_path = os.path.join(current_dir, file_name)

            # Generate random file size
            file_size_bytes = random.randint(min_file_size_kb, max_file_size_kb) * 1024

            # Write dummy content to the file
            try:
                with open(file_path, "wb") as f:  # 'wb' for binary write
                    f.write(os.urandom(file_size_bytes))  # Write random bytes
                created_files_list.append(file_path)
                # print(f"Created: {file_path} ({file_size_bytes / 1024:.2f} KB)")
            except IOError as e:
                print(f"Error creating file {file_path}: {e}")

    print(
        f"\nSuccessfully created {len(created_files_list)} dummy files in '{base_dir}/' with nesting."
    )
    print("Example files:")
    for _ in range(min(5, len(created_files_list))):  # Print up to 5 random files
        print(random.choice(created_files_list))

    return created_files_list


if __name__ == "__main__":
    print("--- Generating custom test files with deeper nesting (max depth 5) ---")
    custom_themes = ["client_data", "financial_records", "marketing_materials"]
    custom_extensions = [".csv", ".xml", ".json", ".zip"]
    custom_files_dir = os.path.join(os.getcwd(), "tests/data/integration")

    custom_files_nested = create_themed_test_files_with_nesting(
        base_dir=custom_files_dir,
        themes=custom_themes,
        num_files_per_theme=4,
        min_file_size_kb=20,
        max_file_size_kb=100,
        file_extensions=custom_extensions,
        max_nesting_depth=5,  # Deeper nesting
        min_nesting_depth=1,  # Ensure at least one level of nesting
        seed=200,
    )

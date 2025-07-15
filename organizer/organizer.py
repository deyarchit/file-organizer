from litellm import completion
from typing import List
from organizer.disk_operations import DiskOperations
from dotenv import load_dotenv
from organizer.models import FlatFileItem, LLMResponseSchema

load_dotenv()


def organize(path: str) -> None:
    disk_ops = DiskOperations(path)

    dir_json: List[FlatFileItem] | None = DiskOperations.create_snapshot(path)
    if dir_json:
        print(f"Loaded dir_json: {dir_json}")
    else:
        return

    try:
        response = completion(
            model="gemini/gemini-2.5-flash",
            response_format=LLMResponseSchema,
            messages=[
                {"content": system_prompt, "role": "system"},
                {"content": str(dir_json), "role": "user"},
            ],
            temperature=0.0,
        )

        parsed_response: LLMResponseSchema = LLMResponseSchema.model_validate_json(
            response.choices[0].message.content
        )

        for strategy in parsed_response.strategies:
            print(f"Evaluating strategy: {strategy.name}")
            missing, added = DiskOperations.compare_structures(
                dir_json, strategy.items, files_only=True
            )
            if len(missing) > 0 or len(added) > 0:
                print(
                    f"Files added/removed from proposed strategy, skipping. Added: {added} Removed: {missing}"
                )
                continue

            for item in strategy.items:
                print(f"  Path: {item.path}")

        # Choose strategy
        selected_strategy = str(input("Select the reorganization strategy name: "))
        # Print the user's input back to them
        print("You entered:", selected_strategy)
        for strategy in parsed_response.strategies:
            if strategy.name == selected_strategy:
                print(f"Applying reorganization strategy: {selected_strategy}")
                disk_ops.sync(dir_json, strategy.items)

    except Exception as e:
        print(f"An error occurred: {e}")


system_prompt = """
You are an expert file system organizer. Your task is to analyze the provided directory structure and propose up to three distinct, logical, and practical reorganization plans. Each plan should aim to improve clarity, accessibility, and reduce clutter.

For each proposed plan, you must output a JSON object that adheres strictly to the defined `response_schema`.

Your proposed plans could provide suggestions that:
* **Group similar file types** (e.g., all `.csv` files, all `.xml` files).
* **Consolidate files related to the same project or client**
* **Reduce unnecessary nested subfolders.**
* **You are encouraged to rename folders to improve organization but do not rename files.**


Present your suggestions as a JSON array, where each element is one of your proposed organization strategy JSON object.
    """

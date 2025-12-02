import pandas as pd
import os
import sys

def load_data(filepath: str) -> pd.DataFrame:
    """
    Loads the dataset from the specified CSV file path.

    Args:
        filepath (str): The absolute path to the CSV file.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        FileNotFoundError: If the file is not found at the specified path.
    """
    try:
        print(f"Attempting to load data from: {filepath}")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found at {filepath}")
        
        df = pd.read_csv(filepath)
        print("Data loaded successfully.")
        return df
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please check the file path. Ensure the folder 'Reserach Paper' is spelled correctly as per the instructions (or 'Research Paper' if that was a typo in the instruction, but following strict instruction to use 'Reserach').")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Specific local path provided in the prompt
    DATASET_PATH = r"C:\TANISH WORK\Msc CS\Semester 03\Reserach Paper\logs\logs.csv"
    
    df = load_data(DATASET_PATH)
    
    print("\nDataset Shape:")
    print(df.shape)
    
    print("\nDataset Head:")
    print(df.head())

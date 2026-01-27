
import sys
import os
import pandas as pd
import shutil

# Add src to path
sys.path.append(os.getcwd())

from src.engine.storage import ArchiveManager

def test_archive():
    print("Testing ArchiveManager...")
    
    # Setup Test Dir
    test_dir = "tests/data/archive_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    manager = ArchiveManager(storage_dir=test_dir)
    
    # Create Mock Data
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["A", "B", "C", "D", "E"],
        "is_alive": [True, False, True, False, False]
    })
    
    print(f"Initial DF:\n{df}")
    
    # Run Archive
    cleaned_df = manager.archive_dead(df)
    
    print(f"Cleaned DF:\n{cleaned_df}")
    
    # Assertions
    assert len(cleaned_df) == 2, "Should have 2 living agents left"
    assert cleaned_df['is_alive'].all(), "All remaining should be alive"
    
    # Check File
    assert os.path.exists(manager.graveyard_path), "Graveyard file should exist"
    
    csv_content = pd.read_csv(manager.graveyard_path)
    print(f"Graveyard CSV:\n{csv_content}")
    
    assert len(csv_content) == 3, "Graveyard should have 3 dead agents"
    assert not csv_content['is_alive'].any(), "All in graveyard should be dead"
    
    # Clean up
    shutil.rmtree("tests/data")
    print("✅ Test Passed!")

if __name__ == "__main__":
    test_archive()

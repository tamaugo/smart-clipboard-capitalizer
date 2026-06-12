import sys
import os

# Add the project root directory to sys.path so we can import packages correctly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from src.clipboard_capitalizer import engine

def run_tests():
    # Format of each test case:
    # (input_text, expected_output, custom_uppercase_list)
    test_cases = [
        # Standard Title Case checks
        ("the", "The", []),
        ("cat", "Cat", []),
        ("THE CAT", "The Cat", []),
        ("the cat", "The Cat", []),
        ("hello world", "Hello World", []),
        ("HELLO WORLD", "Hello World", []),
        
        # Part Number checks (default settings)
        ("xy2594yx684", "XY2594YX684", []),
        ("XY2594YX684", "XY2594YX684", []),
        ("9-ycc142", "9-YCC142", []),
        ("9-YCC142", "9-YCC142", []),
        
        # Mixed standard text and part numbers
        ("the cat needs part xy2594yx684 and 9-ycc142.", "The Cat Needs Part XY2594YX684 And 9-YCC142.", []),
        
        # Standard Title Case for consecutive string (former exclusion words now capitalized)
        ("the cat in the hat with a bat", "The Cat In The Hat With A Bat", []),
        
        # Custom uppercase words overrides (e.g. hyphenated custom word)
        ("check part reference abc-def and normal text.", "Check Part Reference ABC-DEF And Normal Text.", ["abc-def"]),
        
        # Compound words title casing
        ("well-being", "Well-Being", []),
        ("mother-in-law", "Mother-In-Law", []),
    ]
    
    print("Running Corporate Capitalization Logic Unit Tests...")
    print("=" * 60)
    
    passed_count = 0
    for i, (input_text, expected_output, upper_list) in enumerate(test_cases, 1):
        # Process text
        result = engine.capitalize_text(
            input_text,
            min_part_len=4,
            auto_detect_parts=True,
            custom_uppercase_list=upper_list
        )
        
        if result == expected_output:
            print(f"Test {i}: PASSED")
            print(f"  Input:    {repr(input_text)}")
            print(f"  Output:   {repr(result)}")
            passed_count += 1
        else:
            print(f"Test {i}: FAILED")
            print(f"  Input:    {repr(input_text)}")
            print(f"  Expected: {repr(expected_output)}")
            print(f"  Got:      {repr(result)}")
            
        print("-" * 60)
        
    print(f"Summary: {passed_count}/{len(test_cases)} tests passed.")
    if passed_count == len(test_cases):
        print("All tests passed successfully! Project packaging is correct.")
        sys.exit(0)
    else:
        print("Some tests failed. Please check the engine.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

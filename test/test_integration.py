#!/usr/bin/env python3
"""
Integration test for multi-pass processor.
Compares PROCESSED_OUTPUT.txt against expected OUTPUT.txt.
"""

from pathlib import Path
from test_multi_pass_processor import OCRTestFramework, run_test
from multi_pass_processor import MultiPassOCRProcessor

def test_multi_pass_processor():
    """Test the multi-pass processor against expected output."""
    input_path = Path("/home/user/prep-text-for-tts/INPUT.txt")
    expected_output_path = Path("/home/user/prep-text-for-tts/OUTPUT.txt")

    # Create processor function
    def processor_func(text: str) -> str:
        processor = MultiPassOCRProcessor(enable_logging=False)
        processed_text, state = processor.process(text)
        return processed_text

    # Run test
    print("Testing multi-pass processor...")
    print("=" * 80)
    metrics = run_test(processor_func, input_path, expected_output_path)

    # Print report
    print(metrics.get_report())

    # Additional details
    print("\nDETAILED ANALYSIS:")
    print(f"Production Ready: {metrics.is_production_ready()}")
    print(f"Threshold: 85.0%")
    print(f"Gap to production: {85.0 - metrics.overall_score:.2f}%")

    return metrics

if __name__ == "__main__":
    metrics = test_multi_pass_processor()

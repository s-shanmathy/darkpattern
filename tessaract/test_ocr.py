import os
import cv2
import pytesseract
import json
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Paths
PROCESSED_PATH = r"D:\SEM6\DL\DARK\processed_images"
ANNOTATED_PATH = r"D:\SEM6\DL\DARK\training\annotated_images"
RESULTS_PATH = r"D:\SEM6\DL\DARK\training\ocr_results"

def test_ocr_accuracy(sample_images=5):
    """Test OCR accuracy on a few sample images"""
    print("="*60)
    print("TESTING TESSERACT OCR ACCURACY")
    print("="*60)

    # Get sample images
    image_files = sorted([f for f in os.listdir(PROCESSED_PATH) if f.endswith('.png')])[:sample_images]

    for img_file in image_files:
        print(f"\n🔍 Testing: {img_file}")
        print("-" * 40)

        # Load processed image
        img_path = os.path.join(PROCESSED_PATH, img_file)
        image = cv2.imread(img_path)

        if image is None:
            print("❌ Could not load image")
            continue

        # Convert to RGB for OCR
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Perform OCR
        text = pytesseract.image_to_string(rgb_image, config=r'--psm 3 --oem 3')
        data = pytesseract.image_to_data(rgb_image, config=r'--psm 3 --oem 3', output_type=pytesseract.Output.DICT)

        # Extract confidence scores
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Count text regions
        text_regions = sum(1 for t in data['text'] if t.strip())

        print(f"📝 Detected text: {text[:200]}{'...' if len(text) > 200 else ''}")
        print(f"🎯 Text regions found: {text_regions}")
        print(f"📊 Average confidence: {avg_confidence:.1f}%")
        print(f"📈 High confidence regions (>70%): {sum(1 for c in confidences if c > 70)}")

        # Check if annotated image exists
        annotated_path = os.path.join(ANNOTATED_PATH, img_file)
        if os.path.exists(annotated_path):
            print("✅ Annotated image available")
        else:
            print("❌ Annotated image missing")

        # Check if JSON results exist
        json_path = os.path.join(RESULTS_PATH, img_file.replace('.png', '.json'))
        if os.path.exists(json_path):
            print("✅ Detailed results available")
        else:
            print("❌ Detailed results missing")

def show_statistics():
    """Show overall statistics from the training results"""
    print("\n" + "="*60)
    print("OVERALL TRAINING STATISTICS")
    print("="*60)

    # Load summary CSV
    csv_path = r"D:\SEM6\DL\DARK\training\ocr_results_summary.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"📊 Total images processed: {len(df)}")
        print(f"📝 Total text regions detected: {df['text_regions'].sum()}")
        print(f"📈 Average regions per image: {df['text_regions'].mean():.1f}")
        print(f"🎯 Average confidence: {df['avg_confidence'].mean():.1f}%")
        print(f"🏆 High confidence images (>80%): {(df['avg_confidence'] > 80).sum()}")
        print(f"⚠️  Low confidence images (<50%): {(df['avg_confidence'] < 50).sum()}")

        # Show top 3 performing images
        top_3 = df.nlargest(3, 'avg_confidence')
        print("\n🏅 Top 3 performing images:")
        for _, row in top_3.iterrows():
            print(f"   {row['image_id']}: {row['avg_confidence']:.1f}% confidence, {row['text_regions']} regions")
    else:
        print("❌ Summary CSV not found")

def visualize_sample_results():
    """Show visualization of sample results"""
    print("\n" + "="*60)
    print("SAMPLE VISUALIZATION")
    print("="*60)

    # Load a sample annotated image
    sample_files = [f for f in os.listdir(ANNOTATED_PATH) if f.endswith('.png')][:3]

    for img_file in sample_files:
        img_path = os.path.join(ANNOTATED_PATH, img_file)
        if os.path.exists(img_path):
            print(f"🖼️  Annotated image available: {img_file}")

            # Load and display basic info
            img = cv2.imread(img_path)
            h, w = img.shape[:2]
            print(f"   Image size: {w}x{h} pixels")
        else:
            print(f"❌ Annotated image missing: {img_file}")

if __name__ == "__main__":
    # Run all tests
    test_ocr_accuracy(3)  # Test 3 images
    show_statistics()
    visualize_sample_results()

    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\n📋 Summary:")
    print("✅ OCR is working if you see detected text above")
    print("✅ High confidence (>70%) indicates good detection")
    print("✅ Annotated images show bounding boxes around detected text")
    print("✅ JSON files contain detailed coordinates and confidence scores")
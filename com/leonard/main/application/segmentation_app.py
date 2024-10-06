import streamlit as st
import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.segmentation_service import SegmentationService

def main():
    st.title("认知的本质是词汇量！")

    # Initialize SegmentationService
    segmentation_service = SegmentationService()

    # Text input
    text = st.text_area("Enter your text here:", height=300)

    # Input fields for Anki
    tag = st.text_input("Enter tag for Anki cards:")
    deck_name = st.text_input("Enter Anki deck name:", value="cognition")
    model_name = st.text_input("Enter Anki model name:", value="cognitive_vocabulary")

    if st.button("Process and Add to Anki"):
        if text and tag and deck_name and model_name:
            with st.spinner("Processing text and adding to Anki..."):
                processed_words = segmentation_service.segment_and_add_to_anki(text, tag, deck_name, model_name)
                st.success(f"Added {len(processed_words)} words to Anki!")
                st.write("Processed words:")
                st.write(", ".join(processed_words))
        else:
            st.error("Please fill in all fields.")

if __name__ == "__main__":
    main()
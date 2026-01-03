import streamlit as st
import pypdf
import io


def merge_pdfs_stream(front_file, back_file):
    """Merges PDF streams without saving to local disk."""
    reader_front = pypdf.PdfReader(front_file)
    reader_back = pypdf.PdfReader(back_file)
    writer = pypdf.PdfWriter()

    if len(reader_front.pages) != len(reader_back.pages):
        st.error(
            f"Mismatch: Front ({len(reader_front.pages)}) vs Back ({len(reader_back.pages)})"
        )
        return None

    for f_page, b_page in zip(reader_front.pages, reversed(reader_back.pages)):
        writer.add_page(f_page)
        writer.add_page(b_page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream


# --- Streamlit UI ---
st.set_page_config(page_title="PDF Interleave Merger", page_icon="📄")
st.title("📄 PDF Interleave Merger")
st.markdown(
    "Upload your front and back scans to merge them into a single interleaved document."
)

col1, col2 = st.columns(2)

with col1:
    front_pdf = st.file_uploader("Upload Front Pages", type="pdf")
with col2:
    back_pdf = st.file_uploader("Upload Back Pages (Reverse Order)", type="pdf")

if front_pdf and back_pdf:
    if st.button("Merge PDFs", type="primary"):
        with st.spinner("Processing..."):
            merged_result = merge_pdfs_stream(front_pdf, back_pdf)

            if merged_result:
                st.success("Merge Complete!")
                st.download_button(
                    label="Download Merged PDF",
                    data=merged_result,
                    file_name="merged_document.pdf",
                    mime="application/pdf",
                )

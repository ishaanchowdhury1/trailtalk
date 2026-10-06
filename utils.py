import os
from datetime import datetime

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

def ensure_upload_dir():
    """Ensure uploads directory exists."""
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)

def save_uploaded_image(file_buffer):
    """Save an uploaded image file to the local uploads directory and return file path."""
    ensure_upload_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sighting_{timestamp}.jpg"
    filepath = os.path.join(UPLOADS_DIR, filename)
    
    # Read bytes from file buffer (BytesIO or UploadedFile)
    if hasattr(file_buffer, 'getvalue'):
        data = file_buffer.getvalue()
    elif hasattr(file_buffer, 'read'):
        data = file_buffer.read()
    else:
        data = file_buffer
        
    with open(filepath, "wb") as f:
        f.write(data)
    
    return filepath

def export_journal_markdown(sightings_list):
    """Export sightings list of dicts to formatted Markdown for DEV Community post attachment."""
    if not sightings_list:
        return "# TrailTalk Walk Journal\n\nNo sightings recorded yet."
        
    md = "# 🌿 TrailTalk Walk Journal\n\n"
    md += f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n"
    md += f"**Total Sightings:** {len(sightings_list)}\n\n"
    md += "--- \n\n"
    
    for idx, row in enumerate(sightings_list):
        md += f"### {idx+1}. {row['species_name']} (`{row['category']}`)\n"
        md += f"- **Logged at:** {row['timestamp']}\n"
        md += f"- **Confidence:** {row['confidence']}\n"
        md += f"- **AI Model:** `{row['ai_model_used']}`\n"
        md += f"- **Location / Note:** {row['location_note'] or 'On trail'}\n"
        md += f"- **Fun Fact:** {row['fun_fact']}\n\n"
        md += "---\n"
        
    return md

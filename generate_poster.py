from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

prs = Presentation()
# Set slide dimensions to 48x36 inches
prs.slide_width = Inches(48)
prs.slide_height = Inches(36)

blank_slide_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_slide_layout)

def add_box(left, top, width, height, title, body_text):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    text_frame = txBox.text_frame
    text_frame.word_wrap = True
    
    p = text_frame.add_paragraph()
    p.text = title
    p.font.bold = True
    p.font.name = 'Cambria'
    p.font.size = Pt(40)
    p.font.color.rgb = RGBColor(128, 0, 0) # Dark red for headers
    
    for paragraph in body_text:
        p = text_frame.add_paragraph()
        p.text = paragraph
        p.font.name = 'Cambria'
        p.font.size = Pt(24)
        p.space_after = Pt(10)

# Add Title
txBox = slide.shapes.add_textbox(Inches(2), Inches(1), Inches(44), Inches(3))
tf = txBox.text_frame
p = tf.add_paragraph()
p.text = "PROJECT TITLE: ChaosLab: Interactive Open-Source Pipeline Resilience Lab"
p.font.bold = True
p.font.name = 'Cambria'
p.font.size = Pt(60)
p.font.color.rgb = RGBColor(128, 0, 0)

# Define content
intro = [
    "• Motivation: Pipeline failures and queuing behaviors are difficult to understand through static diagrams.",
    "• System Purpose: An interactive, educational data engineering environment designed to help users experiment with pipeline failures, backlogs, and recovery mechanisms in real-time.",
    "• Core Approach: A deliberately bounded software system that generates synthetic shopping orders, processes them using an independent background worker, and maintains state in a shared transactional datastore.",
    "• Application: Provides a safe, reproducible workspace to visualize cause-and-effect relationships during data ingestion without risking production infrastructure."
]

problem = [
    "Problem Statement:",
    "It is challenging for students and developers to experiment with pipeline bottlenecks, malformed data, and retry exhaustion without relying on complex, costly, or rigid production architectures.",
    "Objectives:",
    "• Automated Generation: Stream reproducible synthetic shopping orders into a queue.",
    "• Simulate Disruptions: Allow users to pause workers, inject malformed schemas, and trigger temporary processing errors.",
    "• Real-time Visualization: Display actual backend state transitions instead of fabricated front-end animations.",
    "• Ensure State Integrity: Implement safe, concurrent state mutation between the web API and the background worker."
]

methodology = [
    "• Architecture: Decoupled multi-container app orchestrated via Docker Compose & Render.",
    "   - Frontend: React TypeScript Single Page Application.",
    "   - API: FastAPI web server and REST endpoints.",
    "   - Processor: Independent Python Worker loop.",
    "   - Datastore: PostgreSQL relational database.",
    "• Concurrency Control: Uses SKIP LOCKED row-level locking for safe job claims.",
    "• Simulation Engine: Deterministic pipeline state transitions.",
]

dataset = [
    "• Source: Synthetically generated locally via a seeded Random Number Generator.",
    "• Modality: JSON payloads.",
    "• Details: Imaginary shopping orders containing:",
    "   - category (books, stationery, electronics, essentials)",
    "   - quantity (integer bounds: 1 to 5)",
    "   - unit_price_paise (integer bounds: 5000 to 200000)",
    "• Chaos Data: Deliberately malformed inputs (e.g., negative quantities) are injected on-demand."
]

results = [
    "• Queue Management: Dashboard accurately reflects backlog accumulation when processing is paused and drains upon restoration.",
    "• Error Handling: Injected malformed data is successfully flagged and pushed to a 'Rejected' state instantly.",
    "• Retry Behavior: Temporary errors demonstrate retry delays, successfully recovering on the 3rd attempt without data loss.",
    "• Transaction Safety: The application handles high-frequency polling and worker updates concurrently without dropping state transitions."
]

conclusions = [
    "• ChaosLab successfully isolates data ingestion from processing, providing a tangible way to study architectural resilience.",
    "• The strict use of optimistic locking ensures that educational chaos testing is both predictable and robust.",
    "• Future Scope: Expanding the queue to a genuine message broker (like Kafka), adding multi-node worker autoscaling, and simulating packet-level network latency."
]

# Layout boxes (left, top, width, height)
# Column 1
add_box(2, 5, 14, 12, "INTRODUCTION", intro)
add_box(2, 18, 14, 14, "PROBLEM STATEMENT & OBJECTIVES", problem)

# Column 2 (Methodology and flowchart)
add_box(17, 5, 14, 10, "METHODOLOGY", methodology)

# Draw flowchart in Col 2
flowchart_top = 16
steps = ["React Web Dashboard", "FastAPI Server", "PostgreSQL Datastore", "Python Worker Process"]
for i, step in enumerate(steps):
    shape = slide.shapes.add_shape(1, Inches(18), Inches(flowchart_top + i*3), Inches(12), Inches(2)) # MSO_SHAPE.RECTANGLE is 1
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(220, 230, 240)
    p = shape.text_frame.add_paragraph()
    p.text = step
    p.font.color.rgb = RGBColor(0, 0, 0)
    p.font.name = 'Cambria'
    p.font.size = Pt(28)
    p.alignment = PP_ALIGN.CENTER
    # Add arrow if not last
    if i < len(steps)-1:
        arrow = slide.shapes.add_shape(33, Inches(23.5), Inches(flowchart_top + i*3 + 2), Inches(1), Inches(1)) # MSO_SHAPE.DOWN_ARROW is 33
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = RGBColor(100, 100, 100)

# Column 3
add_box(32, 5, 14, 8, "DATASET", dataset)
add_box(32, 14, 14, 10, "RESULTS AND DISCUSSION", results)
add_box(32, 25, 14, 7, "CONCLUSIONS", conclusions)

# Footer
txBox = slide.shapes.add_textbox(Inches(2), Inches(33), Inches(22), Inches(2))
p = txBox.text_frame.add_paragraph()
p.text = "GROUP MEMBERS: Shivam Kore"
p.font.bold = True
p.font.name = 'Cambria'
p.font.size = Pt(36)

txBox2 = slide.shapes.add_textbox(Inches(32), Inches(33), Inches(14), Inches(2))
p2 = txBox2.text_frame.add_paragraph()
p2.text = "PROJECT MENTOR: [Add Mentor Name Here]"
p2.font.bold = True
p2.font.name = 'Cambria'
p2.font.size = Pt(36)

prs.save('/Users/shivamkore/Desktop/ChaosLab_Poster.pptx')

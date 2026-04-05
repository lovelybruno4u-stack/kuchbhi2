import re

with open('templates/teacher/quiz.html', 'r') as f:
    content = f.read()

# Replace the header of the Questions section
old_header = """<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: var(--text-primary);">2. Questions</h4>
                    <button type="button" class="btn btn-outline" onclick="addQuestionBlock()" style="padding: 4px 10px; font-size: 0.85rem;">
                        <i class="fas fa-plus"></i> Add Question Field
                    </button>
                </div>"""

new_header = """<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: var(--text-primary);">2. Questions</h4>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="number" id="bulk-q-count" class="form-control" value="10" min="1" max="100" style="width: 80px; padding: 4px; height: 32px;" title="Number of questions to generate">
                        <button type="button" class="btn btn-primary" onclick="generateQuestionBlocks()" style="padding: 4px 10px; font-size: 0.85rem; height: 32px;">
                            <i class="fas fa-magic"></i> Generate Fields
                        </button>
                        <button type="button" class="btn btn-outline" onclick="addQuestionBlock()" style="padding: 4px 10px; font-size: 0.85rem; height: 32px;">
                            <i class="fas fa-plus"></i> Add 1
                        </button>
                    </div>
                </div>"""

if old_header in content:
    content = content.replace(old_header, new_header)

# Add the generateQuestionBlocks function
js_to_add = """
    function generateQuestionBlocks() {
        const count = parseInt(document.getElementById('bulk-q-count').value);
        if(isNaN(count) || count < 1 || count > 100) {
            alert('Please enter a valid number between 1 and 100.');
            return;
        }

        const container = document.getElementById('questions-container');
        // Clear existing to prevent appending hundreds by accident, or ask confirmation
        if(container.children.length > 0) {
            if(!confirm('This will clear existing empty fields. Keep going?')) return;
        }

        container.innerHTML = ''; // Clear
        qCount = 0;

        for(let i=0; i<count; i++) {
            addQuestionBlock();
        }
    }
"""

if "function generateQuestionBlocks()" not in content:
    content = content.replace("function renumberQuestions()", js_to_add + "\n    function renumberQuestions()")

with open('templates/teacher/quiz.html', 'w') as f:
    f.write(content)

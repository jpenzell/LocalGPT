import gradio as gr
import requests
from typing import List, Tuple
import os
from PyPDF2 import PdfReader
import docx
import json

def read_pdf(file_path):
    """Extract text from PDF"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_docx(file_path):
    """Extract text from DOCX"""
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def read_txt(file_path):
    """Read text from TXT"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def process_uploaded_file(file_obj):
    """Process uploaded file and return its content"""
    if file_obj is None:
        return ""
    
    file_name = file_obj.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    try:
        if file_extension == '.pdf':
            return read_pdf(file_obj.name)
        elif file_extension == '.docx':
            return read_docx(file_obj.name)
        elif file_extension == '.txt':
            return read_txt(file_obj.name)
        else:
            return "Unsupported file format"
    except Exception as e:
        return f"Error processing file: {str(e)}"

def generate_response(prompt, history, system_prompt, temperature, model):
    """Send a request to Ollama and get the response"""
    try:
        # Construct context from history
        context = ""
        for msg in history:
            context += f"User: {msg[0]}\nAssistant: {msg[1]}\n"
        
        # Add current prompt
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser: {prompt}\nAssistant:"
        
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": model,
                                   "prompt": full_prompt,
                                   "temperature": float(temperature),
                                   "stream": False
                               })
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def chat_interface(message: str, 
                  history: List[Tuple[str, str]], 
                  system_prompt: str,
                  temperature: float,
                  model: str,
                  uploaded_file = None,
                  projects_dict = None,
                  current_project = None):
    if not message.strip():  # Skip empty messages
        return history, history, ""
    
    # Process uploaded file if present
    if uploaded_file is not None:
        file_content = process_uploaded_file(uploaded_file)
        if file_content:
            message = f"Context from uploaded file:\n{file_content}\n\nUser query: {message}"
    
    # Generate response with selected model
    response = generate_response(message, history, system_prompt, temperature, model)
    
    # Update history
    history = history or []
    history.append((message, response))
    
    # Save updated history to projects if available
    if projects_dict is not None and current_project is not None:
        if current_project in projects_dict:
            projects_dict[current_project]["history"] = history
            save_projects(projects_dict)
    
    return history, history, ""

def save_projects(projects_dict):
    """Save projects to a JSON file"""
    with open('projects.json', 'w') as f:
        # Convert the projects dict to a serializable format
        serializable_projects = {}
        for name, data in projects_dict.items():
            serializable_projects[name] = {
                "history": data["history"],  # Now we save the chat history
                "system_prompt": data["system_prompt"],
                "temperature": data["temperature"],
                "model": data["model"],  # Added model
                "file": None  # We don't save file references
            }
        json.dump(serializable_projects, f)

def init_projects():
    """Initialize projects with default project"""
    return {
        "Default": {
            "history": [],
            "system_prompt": "You are a helpful AI assistant. Please provide clear and concise responses.",
            "temperature": 0.7,
            "model": "mistral",  # Added default model
            "file": None
        }
    }

def load_projects():
    """Load projects from JSON file or return default if file doesn't exist"""
    if os.path.exists('projects.json'):
        with open('projects.json', 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return init_projects()
    return init_projects()

# Add this function before the "with gr.Blocks() as iface:" line
def get_available_models():
    """Get list of available models from Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = [model['name'] for model in response.json()['models']]
            return models if models else ["mistral", "orca-mini"]  # fallback to defaults
    except:
        return ["mistral", "orca-mini"]  # fallback to defaults

# Create the Gradio interface
with gr.Blocks() as iface:
    gr.Markdown("# Ollama Chat Interface")
    
    # Make rows more compact by using smaller scales
    with gr.Row():
        model_selector = gr.Dropdown(
            label="Select AI Model",
            choices=get_available_models(),
            value="mistral",
            interactive=True,
            container=True,
            scale=2
        )
        refresh_models = gr.Button("🔄 Refresh Models", scale=1)
    
    with gr.Row():
        project_name = gr.Textbox(label="New Project Name", scale=1)
        project_list = gr.Dropdown(
            label="Current Project",
            choices=list(load_projects().keys()),
            value="Default",
            interactive=True,
            container=True,
            scale=2,
            filterable=True
        )
        create_project = gr.Button("Create Project", scale=1)
        delete_project = gr.Button("Delete Project", variant="stop", scale=1)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=300)  # Reduced height
            msg = gr.Textbox(
                label="Type your message here",
                lines=1,  # Reduced to 1 line
                autofocus=True,
                interactive=True,
                container=False
            )
            with gr.Row():
                clear = gr.Button("Clear")
                submit = gr.Button("Submit", variant="primary")  # Make submit button stand out
        
        with gr.Column(scale=1):
            system_prompt = gr.Textbox(
                label="System Prompt",
                value="You are a helpful AI assistant. Please provide clear and concise responses.",
                lines=2,  # Reduced lines
                container=False
            )
            temperature = gr.Slider(
                minimum=0.1,
                maximum=2.0,
                value=0.7,
                step=0.1,
                label="Temperature"
            )
            uploaded_file = gr.File(
                label="Upload Document",  # Shortened label
                file_types=[".pdf", ".docx", ".txt"],
                type="filepath"
            )
    
    # Initialize projects with Default project
    state = gr.State([])
    projects = gr.State(init_projects())
    
    def create_project_fn(new_name, projects_dict, current_system_prompt, current_temperature, current_model, current_file):
        """Create a new project"""
        if not new_name or new_name.strip() == "":
            return (
                [], [], current_system_prompt, current_temperature, current_model, current_file,
                projects_dict, 
                gr.update(choices=list(projects_dict.keys()), value="Default"),
                "Default"
            )
        
        new_name = new_name.strip()
        projects_dict[new_name] = {
            "history": [],
            "system_prompt": current_system_prompt,
            "temperature": current_temperature,
            "model": current_model,
            "file": current_file
        }
        
        save_projects(projects_dict)
        
        return (
            [], [], current_system_prompt, current_temperature, current_model, current_file,
            projects_dict, 
            gr.update(choices=list(projects_dict.keys()), value=new_name),
            new_name
        )
    
    def switch_project(selected_name, projects_dict):
        """Switch to selected project"""
        if selected_name not in projects_dict:
            selected_name = "Default"  # Fallback to Default if project not found
        
        project_data = projects_dict[selected_name]
        return (
            project_data["history"],
            project_data["history"],
            project_data["system_prompt"],
            project_data["temperature"],
            project_data.get("model", "mistral"),  # Add fallback value
            project_data.get("file", None)
        )
    
    def delete_project_fn(selected_name, projects_dict):
        """Delete selected project"""
        if selected_name == "Default":
            return (
                projects_dict["Default"]["history"],
                projects_dict["Default"]["history"],
                projects_dict["Default"]["system_prompt"],
                projects_dict["Default"]["temperature"],
                projects_dict["Default"]["model"],
                projects_dict["Default"]["file"],
                projects_dict,
                gr.update(choices=list(projects_dict.keys()), value="Default"),
                "Default"
            )
        
        if selected_name in projects_dict:
            del projects_dict[selected_name]
            save_projects(projects_dict)
        
        return (
            projects_dict["Default"]["history"],
            projects_dict["Default"]["history"],
            projects_dict["Default"]["system_prompt"],
            projects_dict["Default"]["temperature"],
            projects_dict["Default"]["model"],
            projects_dict["Default"]["file"],
            projects_dict,
            gr.update(choices=list(projects_dict.keys()), value="Default"),
            "Default"
        )

    # Project management handlers
    create_project.click(
        fn=create_project_fn,
        inputs=[
            project_name,
            projects,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file
        ],
        outputs=[
            chatbot,
            state,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file,
            projects,
            project_list,
            project_list
        ]
    ).then(
        lambda x: "",
        inputs=[project_name],
        outputs=[project_name]
    )
    
    project_list.change(
        fn=switch_project,
        inputs=[project_list, projects],
        outputs=[
            chatbot,
            state,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file
        ]
    )
    
    delete_project.click(
        fn=delete_project_fn,
        inputs=[project_list, projects],
        outputs=[
            chatbot,
            state,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file,
            projects,
            project_list,
            project_list
        ]
    )
    
    clear.click(lambda: ([], [], ""), outputs=[chatbot, state, msg])

    # Add the chat interface handler
    submit.click(
        fn=chat_interface,
        inputs=[
            msg,
            state,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file,
            projects,
            project_list
        ],
        outputs=[
            chatbot,
            state,
            msg
        ]
    )

    # Make sure both submit button and Enter key trigger the chat
    msg.submit(
        fn=chat_interface,
        inputs=[
            msg,
            state,
            system_prompt,
            temperature,
            model_selector,
            uploaded_file,
            projects,
            project_list
        ],
        outputs=[chatbot, state, msg]
    )

    # Update the project switching logic
    project_list.change(
        fn=switch_project,
        inputs=[project_list, projects],
        outputs=[chatbot, state, system_prompt, temperature, model_selector, uploaded_file]
    )

    # Update the clear button to also update projects
    def clear_chat(projects_dict, current_project):
        if current_project in projects_dict:
            projects_dict[current_project]["history"] = []
            save_projects(projects_dict)
        return [], [], ""

    clear.click(
        fn=clear_chat,
        inputs=[projects, project_list],
        outputs=[chatbot, state, msg]
    )

# Launch the app
if __name__ == "__main__":
    iface.launch(height=600)  # Reduced height
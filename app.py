import gradio as gr
import ollama
import json
import requests
from pathlib import Path
import os
import time
from datetime import datetime, timedelta

# Load and save project configurations
def load_projects():
    if os.path.exists('projects.json'):
        with open('projects.json', 'r') as f:
            return json.load(f)
    return {}

def save_project(name, system_instruction, model_name):
    projects = load_projects()
    projects[name] = {
        "system_instruction": system_instruction,
        "model": model_name
    }
    with open('projects.json', 'w') as f:
        json.dump(projects, f, indent=4)
    return list(projects.keys())

# Enhanced model management functions
def load_models_config():
    try:
        with open('models.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "recommended": {},
            "specialized": {},
            "experimental": {},
            "new": {}
        }

def get_installed_models():
    try:
        response = ollama.list()
        return {model['name']: model for model in response['models']}
    except Exception as e:
        print(f"Error getting installed models: {e}")
        return {}

def get_available_models():
    try:
        # First try to get models from Ollama's official library
        models = {
            # Base models
            "llama2": "Meta's flagship large language model",
            "mistral": "Mistral AI's powerful open model",
            "mixtral": "Mistral AI's mixture of experts model",
            "phi": "Microsoft's compact yet powerful model",
            "neural-chat": "Intel's optimized chat model",
            "starling-lm": "Berkeley's high quality open model",
            "codellama": "Meta's code specialized model",
            "dolphin-phi": "Efficient phi-based model",
            "orca-mini": "Lightweight but capable model",
            "vicuna": "Berkeley's chatbot model",
            "stable-beluga": "Stable performance model",
            "nous-hermes": "Anthropic-based model",
            "wizard-math": "Mathematics specialized model",
            "openchat": "Open source chat model",
            "solar": "Upstage's powerful model",
            "gemma": "Google's latest open model",
            "qwen": "Alibaba's multilingual model",
            # Add more models as they become available
        }
        
        # Try to get additional models from Ollama's API
        try:
            response = requests.get('https://ollama.ai/api/tags', timeout=5)
            if response.status_code == 200:
                api_models = response.json()
                # Add any models from the API that aren't in our list
                for model in api_models:
                    if model not in models:
                        models[model] = "Available through Ollama"
        except Exception as e:
            print(f"Couldn't fetch additional models from API: {e}")
        
        return models
    except Exception as e:
        print(f"Error fetching available models: {e}")
        return {}

def fetch_available_models():
    try:
        # Get installed models
        installed = get_installed_models()
        
        # Get available models
        available = get_available_models()
        
        model_list = []
        seen_models = set()
        
        # First add installed models
        for model_name, model_info in installed.items():
            base_name = model_name.split(':')[0]
            seen_models.add(base_name)
            model_list.append([
                model_name,                    # Name
                "Installed",                   # Category
                "Local",                       # Size
                f"Installed model ({base_name})",  # Description
                "✓ Installed",                # Status
                "Current",                     # Last Updated
                "Remove"                       # Action
            ])
        
        # Define categories based on model types
        categories = {
            'llama2': 'Foundation',
            'mistral': 'Foundation',
            'mixtral': 'Foundation',
            'codellama': 'Development',
            'neural-chat': 'Chat',
            'starling': 'Experimental',
            'dolphin': 'Experimental',
            'phi': 'Compact',
            'orca': 'Compact',
            'vicuna': 'Chat',
            'stable': 'Stable',
            'wizard': 'Specialized',
            'openchat': 'Chat',
            'solar': 'Foundation',
            'gemma': 'Foundation',
            'qwen': 'Multilingual'
        }
        
        # Then add available models that aren't installed
        for model_name, description in available.items():
            base_name = model_name.split(':')[0]
            if base_name not in seen_models:
                # Determine category
                category = 'General'
                for key, cat in categories.items():
                    if key in model_name.lower():
                        category = cat
                        break
                
                model_list.append([
                    model_name,                    # Name
                    category,                      # Category
                    "Remote",                      # Size
                    description,                   # Description
                    "Not Installed",               # Status
                    "Latest",                      # Last Updated
                    "Install"                      # Action
                ])
        
        # Sort the list: installed first, then by category and name
        model_list.sort(key=lambda x: (
            x[4] != "✓ Installed",  # Installed models first
            x[1],                   # Then by category
            x[0]                    # Then by name
        ))
        
        return model_list
        
    except Exception as e:
        print(f"Error preparing model list: {e}")
        return []

def refresh_models():
    try:
        models = fetch_available_models()
        installed_count = sum(1 for m in models if '✓ Installed' in m[4])
        available_count = sum(1 for m in models if 'Not Installed' in m[4])
        
        status = (
            "✅ Model list refreshed successfully!\n\n"
            f"Found {len(models)} models:\n"
            f"- {installed_count} installed\n"
            f"- {available_count} available for installation\n\n"
            "Click on any model to install or remove it."
        )
        
        return status, models, gr.Dropdown(
            choices=get_model_categories(models),
            value="All"
        )
    except Exception as e:
        error_msg = (
            "❌ Error refreshing models:\n"
            f"{str(e)}\n\n"
            "Please ensure:\n"
            "1. Ollama is running (brew services start ollama)\n"
            "2. You have internet connection\n"
            "3. Ollama service is responsive"
        )
        return error_msg, [], gr.Dropdown(choices=["All"], value="All")

def chat_with_model(message, history, model_name, system_instruction=None):
    try:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        for h in history:
            messages.append({"role": "user", "content": h[0]})
            messages.append({"role": "assistant", "content": h[1]})
        
        messages.append({"role": "user", "content": message})
        
        response = ollama.chat(model=model_name, messages=messages)
        return response['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

def calculate_eta(downloaded, total, elapsed_time):
    if downloaded == 0:
        return "calculating..."
    
    rate = downloaded / elapsed_time  # bytes per second
    remaining_bytes = total - downloaded
    eta_seconds = remaining_bytes / rate if rate > 0 else 0
    return format_time(eta_seconds)

def handle_model_action(evt: gr.SelectData, models_data, model_dropdown_component):
    """Handle model installation/removal with dropdown update"""
    try:
        models_list = models_data.values.tolist() if hasattr(models_data, 'values') else models_data
        
        if not evt or not hasattr(evt, 'index'):
            yield "❌ Error: Invalid selection", models_data, gr.update()
            return

        selected_row = models_list[evt.index[0]]
        model_name = selected_row[0]
        current_status = selected_row[4]
        
        progress_text = ""
        
        if "✓" not in str(current_status):  # Install model
            progress_text = f"Starting installation of {model_name}...\n"
            yield progress_text, models_data, gr.update()
            
            try:
                for response in ollama.pull(model_name, stream=True):
                    if 'status' in response:
                        progress_text += f"{response['status']}\n"
                    if 'completed' in response:
                        progress_text += f"Progress: {response['completed']}/{response['total']} layers\n"
                    yield progress_text, models_data, gr.update()
                
                progress_text += f"\n✅ Successfully installed {model_name}!"
                
            except Exception as install_error:
                progress_text += f"\n❌ Installation error: {str(install_error)}"
                yield progress_text, models_data, gr.update()
                return
                
        else:  # Remove model
            progress_text = f"Removing {model_name}...\n"
            yield progress_text, models_data, gr.update()
            
            try:
                ollama.rm(model_name)
                progress_text += f"✅ Successfully removed {model_name}!"
                
            except Exception as remove_error:
                progress_text += f"\n❌ Removal error: {str(remove_error)}"
                yield progress_text, models_data, gr.update()
                return
        
        # Update models list and dropdown
        try:
            new_models = fetch_available_models()
            installed_models = list(get_installed_models().keys())
            yield progress_text, new_models, gr.Dropdown(choices=installed_models)
            
        except Exception as update_error:
            progress_text += f"\n❌ Error updating model list: {str(update_error)}"
            yield progress_text, models_data, gr.update()
        
    except Exception as e:
        error_text = f"❌ Error: {str(e)}\nPlease check the console for details."
        yield error_text, models_data, gr.update()

def get_model_categories(models_list):
    """Extract unique categories from the models list and add 'All'"""
    categories = {"All"}  # Start with 'All'
    for model in models_list:
        categories.add(model[1])  # Add each model's category
    return sorted(list(categories))

def filter_models(search_term, category, models_data):
    """Filter models based on search term and category"""
    if not models_data:
        return []
    
    filtered_models = models_data
    
    # Apply category filter
    if category and category != "All":
        filtered_models = [m for m in filtered_models if m[1] == category]
    
    # Apply search filter
    if search_term:
        search_term = search_term.lower()
        filtered_models = [
            m for m in filtered_models 
            if search_term in m[0].lower() or search_term in m[3].lower()
        ]
    
    return filtered_models

def chat_response(message, history, model_name, system_prompt):
    """Chat function that takes model and system prompt as parameters"""
    try:
        system_inst = system_prompt if system_prompt else "You are a helpful AI assistant."
        
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_inst},
                *[{"role": m[0], "content": m[1]} for m in history],
                {"role": "user", "content": message}
            ]
        )
        
        assistant_message = response['message']['content']
        history.append([message, assistant_message])
        return "", history
        
    except Exception as e:
        error_message = f"Error: {str(e)}\nPlease ensure a model is selected and Ollama is running."
        history.append([message, error_message])
        return "", history

def process_file(file):
    """Process uploaded file and return its content"""
    if file is None:
        return None
    
    try:
        content = ""
        file_path = file.name
        
        # Handle different file types
        if file_path.endswith('.txt') or file_path.endswith('.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.endswith('.pdf'):
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = ' '.join(page.extract_text() for page in reader.pages)
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            import docx
            doc = docx.Document(file_path)
            content = ' '.join(paragraph.text for paragraph in doc.paragraphs)
            
        print(f"Processed file content length: {len(content)}")
        return content
    except Exception as e:
        print(f"Error processing file: {e}")
        return None

def chat_wrapper(message, history, model, system, file_content):
    """Chat function that properly integrates file content and system instructions"""
    try:
        # Construct system message
        if system and file_content:
            system_message = f"{system}\n\nDocument content:\n{file_content}"
        elif system:
            system_message = system
        elif file_content:
            system_message = f"You are a helpful AI assistant.\n\nDocument content:\n{file_content}"
        else:
            system_message = "You are a helpful AI assistant."
        
        # Format messages for Ollama
        ollama_messages = [
            {"role": "system", "content": system_message}
        ]
        
        if history:
            for exchange in history:
                user_msg, assistant_msg = exchange
                ollama_messages.extend([
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg}
                ])
        
        ollama_messages.append({"role": "user", "content": message})
        
        response = ollama.chat(
            model=model,
            messages=ollama_messages
        )
        
        assistant_message = response['message']['content']
        new_history = history + [[message, assistant_message]] if history is not None else [[message, assistant_message]]
        return "", new_history
        
    except Exception as e:
        print(f"Error in chat_wrapper: {str(e)}")
        error_message = f"Error: {str(e)}\nPlease ensure a model is selected and Ollama is running."
        new_history = history + [[message, error_message]] if history is not None else [[message, error_message]]
        return "", new_history

def refresh_project_list():
    """Refresh the list of available projects"""
    try:
        projects = list_projects()
        return gr.Dropdown(choices=projects, value=None)
    except Exception as e:
        print(f"Error refreshing project list: {e}")
        return gr.Dropdown(choices=[], value=None)

def save_chat_project(name, history, system_inst, file_cont):
    """Save the chat history, system instructions, and file content to a JSON file"""
    if not name:
        return gr.update(), history, gr.update(), system_inst, file_cont
    try:
        os.makedirs("projects", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure file_cont is properly handled even if it's None
        save_data = {
            "history": history,
            "timestamp": timestamp,
            "name": name,
            "system_instruction": system_inst,
            "file_content": file_cont if file_cont is not None else ""
        }
        
        with open(f"projects/{name}.json", "w", encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"Project saved successfully: {name}")  # Debug print
        print(f"Saved file content length: {len(str(file_cont)) if file_cont else 0}")  # Debug print
        
        return gr.update(), history, refresh_project_list(), system_inst, file_cont
    except Exception as e:
        print(f"Error saving project: {e}")  # Log error instead of showing it
        return gr.update(), history, gr.update(), system_inst, file_cont

def load_chat_project(name):
    """Load a chat history from a JSON file"""
    if not name:
        return gr.update(), None, "", ""
    try:
        with open(f"projects/{name}.json", "r", encoding='utf-8') as f:
            data = json.load(f)
        
        history = data.get("history", [])
        system_inst = data.get("system_instruction", "")
        file_cont = data.get("file_content", "")
        
        print(f"Loading project: {name}")
        print(f"Loaded system instruction length: {len(system_inst)}")
        print(f"Loaded file content length: {len(file_cont)}")
        
        return gr.update(), history, system_inst, file_cont
    except FileNotFoundError:
        return gr.update(), None, "", ""
    except Exception as e:
        print(f"Error loading project: {e}")
        return gr.update(), None, "", ""

def list_projects():
    """List all available projects"""
    try:
        if not os.path.exists("projects"):
            return []
        return [f.replace(".json", "") for f in os.listdir("projects") if f.endswith(".json")]
    except Exception:
        return []

def update_project_list():
    """Update the list of available projects"""
    try:
        projects = list_projects()
        return gr.Dropdown(choices=projects)
    except Exception as e:
        print(f"Error updating project list: {e}")
        return gr.Dropdown(choices=[])

def delete_chat_project(name):
    """Delete a chat project"""
    if not name:
        return gr.update(), gr.update()
    try:
        project_path = f"projects/{name}.json"
        if os.path.exists(project_path):
            os.remove(project_path)
            # Clear the project name and update dropdown without message
            return gr.update(value=""), refresh_project_list()
        else:
            print(f"Project '{name}' not found")  # Log error instead of showing it
            return gr.update(), gr.update()
    except Exception as e:
        print(f"Error deleting project: {e}")  # Log error instead of showing it
        return gr.update(), gr.update()

def main():
    with gr.Blocks(title="LocalGPT", theme=gr.themes.Soft()) as demo:
        # Initialize file content state with empty string
        file_content = gr.State("")
        
        with gr.Tabs() as tabs:
            # Chat Tab
            with gr.Tab("Chat"):
                # Project Management Row
                with gr.Row():
                    with gr.Column(scale=1):
                        project_name = gr.Textbox(
                            label="Project Name",
                            placeholder="Enter project name...",
                            container=False
                        )
                        available_projects = gr.Dropdown(
                            choices=list_projects(),
                            label="Available Projects",
                            container=False
                        )
                        with gr.Row():
                            save_project = gr.Button("Save Project")
                            load_project = gr.Button("Load Project")
                            delete_project = gr.Button("🗑️ Delete Project", variant="secondary")
                            refresh_projects = gr.Button("🔄 Refresh")
                
                # Chat Interface Row
                with gr.Row(equal_height=True):
                    # Chat interface on the left (wider)
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="Chat History",
                            height=500,
                            show_copy_button=True
                        )
                        with gr.Row():
                            msg = gr.Textbox(
                                label="Message",
                                placeholder="Type your message here and press Enter to send...",
                                lines=2,
                                scale=4,
                                container=False,
                                show_label=False,
                                autofocus=True
                            )
                            submit = gr.Button("Send", scale=1)
                            clear = gr.Button("Clear", scale=1)
                    
                    # Controls on the right (narrower)
                    with gr.Column(scale=1):
                        model_dropdown = gr.Dropdown(
                            choices=list(get_installed_models().keys()),
                            label="Select Model",
                            value=list(get_installed_models().keys())[0] if get_installed_models() else None,
                            container=False
                        )
                        system_instruction = gr.Textbox(
                            label="System Instruction",
                            placeholder="Enter specific instructions for the AI here...",
                            lines=3,
                            container=True,
                            show_label=True
                        )
                        file_upload = gr.File(
                            label="Upload File",
                            file_types=[".txt", ".md", ".pdf", ".doc", ".docx"],
                            container=False,
                            type="filepath"
                        )

                        # Add file status display
                        file_status = gr.Textbox(
                            label="File Status",
                            interactive=False,
                            container=True
                        )

                        # Add system instruction status
                        system_status = gr.Markdown("""
                        💡 **Tip:** Use system instructions to guide the AI's behavior. 
                        For example: "You are an expert programmer who explains code clearly and concisely."
                        """)

            # Model Management Tab
            with gr.Tab("Model Management"):
                with gr.Row():
                    with gr.Column(scale=3):
                        with gr.Row():
                            refresh_btn = gr.Button("Refresh Models", variant="primary")
                            search_box = gr.Textbox(
                                label="Search",
                                placeholder="Search models...",
                                container=False
                            )
                            category_filter = gr.Dropdown(
                                choices=get_model_categories(fetch_available_models()),
                                label="Category",
                                value="All",
                                container=False
                            )
                        
                        status_text = gr.TextArea(
                            label="Status & Progress",
                            interactive=False,
                            container=True,
                            lines=8,
                            autoscroll=True
                        )
                        
                        models_table = gr.Dataframe(
                            headers=["Name", "Category", "Size", "Description", "Status", "Last Updated", "Action"],
                            datatype=["str", "str", "str", "str", "str", "str", "str"],
                            interactive=False,
                            row_count=25,
                            wrap=True,
                            value=fetch_available_models()
                        )
                        
                        gr.Markdown("""
                        ### Instructions
                        1. Click on any model row to install or remove it
                        2. Watch the status area for progress
                        3. Refresh the list to see updates
                        4. Search or filter to find specific models
                        """)

        # Update file upload handler
        def safe_process_file(file_path):
            """Wrapper to safely process file and update state"""
            if file_path is None:
                return None
            try:
                new_content = process_file(file_path)
                print(f"Updating file content state with length: {len(new_content) if new_content else 0}")
                return new_content
            except Exception as e:
                print(f"Error in safe_process_file: {e}")
                return None
        
        file_upload.change(
            fn=safe_process_file,
            inputs=[file_upload],
            outputs=[file_content]
        )
        
        # Update chat events to include file content
        msg.submit(
            fn=chat_wrapper,
            inputs=[msg, chatbot, model_dropdown, system_instruction, file_content],
            outputs=[msg, chatbot]
        )
        
        submit.click(
            fn=chat_wrapper,
            inputs=[msg, chatbot, model_dropdown, system_instruction, file_content],
            outputs=[msg, chatbot]
        )
        
        clear.click(
            fn=lambda: (None, None),
            outputs=[msg, chatbot]
        )
        
        # Project management events
        save_project.click(
            fn=save_chat_project,
            inputs=[project_name, chatbot, system_instruction, file_content],
            outputs=[project_name, chatbot, available_projects, system_instruction, file_content]
        )
        
        load_project.click(
            fn=load_chat_project,
            inputs=[project_name],
            outputs=[project_name, chatbot, system_instruction, file_content]
        )
        
        refresh_projects.click(
            fn=update_project_list,
            outputs=[available_projects]
        )
        
        available_projects.change(
            fn=lambda x: x,
            inputs=[available_projects],
            outputs=[project_name]
        )

        # Model management events
        refresh_btn.click(
            fn=refresh_models,
            outputs=[status_text, models_table, category_filter]
        )
        
        def on_filter_change(search, category, current_models):
            return filter_models(search, category, current_models)

        search_box.change(
            fn=on_filter_change,
            inputs=[search_box, category_filter, models_table],
            outputs=[models_table]
        )
        
        category_filter.change(
            fn=on_filter_change,
            inputs=[search_box, category_filter, models_table],
            outputs=[models_table]
        )

        # Update model installation event
        models_table.select(
            fn=handle_model_action,
            inputs=[models_table, model_dropdown],
            outputs=[status_text, models_table, model_dropdown]
        )

        # Add delete project event handler
        delete_project.click(
            fn=delete_chat_project,
            inputs=[project_name],
            outputs=[project_name, available_projects]
        )

    demo.launch(
        height=750,
        show_error=True
    )

if __name__ == "__main__":
    main()
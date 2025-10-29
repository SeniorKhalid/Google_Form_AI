import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import json
import os
from datetime import datetime

TEMPLATE_FILE = "templates.json"
questions = []
template_names = []

# 📤 Send to Google Script
def send_to_google_script(form_data):
    headers = {"Content-Type": "application/json"}
    url = user_script_url.get().strip()
    if not url:
        messagebox.showwarning("Missing Script URL", "Please enter your Google Script URL.")
        return None
    response = requests.post(url, data=json.dumps(form_data), headers=headers)
    return response.text if response.status_code == 200 else None

# 💾 Save form history
def save_form_history(title, link):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {title}\n{link}\n\n"
    with open("form_history.txt", "a", encoding="utf-8") as file:
        file.write(entry)

# 🧠 Add a question
def add_question():
    q_text = question_entry.get().strip()
    q_type = question_type.get()
    if not q_text:
        messagebox.showwarning("Missing Question", "Please enter a question.")
        return
    question = {"type": q_type, "question": q_text}
    if q_type == "multiple_choice":
        options_text = simpledialog.askstring("Options", "Enter options separated by commas:")
        if not options_text:
            messagebox.showwarning("Missing Options", "Multiple choice requires options.")
            return
        question["options"] = [opt.strip() for opt in options_text.split(",")]
    questions.append(question)
    question_entry.delete(0, tk.END)
    update_question_list()

# 🧾 Update question list display
def update_question_list():
    question_list.delete(0, tk.END)
    for i, q in enumerate(questions, 1):
        display = f"{i}. [{q['type']}] {q['question']}"
        if q["type"] == "multiple_choice":
            display += f" → {', '.join(q['options'])}"
        question_list.insert(tk.END, display)

# 🗑️ Remove selected question
def remove_selected_question():
    selected = question_list.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a question to remove.")
        return
    index = selected[0]
    del questions[index]
    update_question_list()

# 🔼 Move question up
def move_question_up():
    selected = question_list.curselection()
    if not selected or selected[0] == 0:
        return
    index = selected[0]
    questions[index - 1], questions[index] = questions[index], questions[index - 1]
    update_question_list()
    question_list.select_set(index - 1)

# 🔽 Move question down
def move_question_down():
    selected = question_list.curselection()
    if not selected or selected[0] == len(questions) - 1:
        return
    index = selected[0]
    questions[index + 1], questions[index] = questions[index], questions[index + 1]
    update_question_list()
    question_list.select_set(index + 1)

# ✏️ Edit selected question
def edit_selected_question():
    selected = question_list.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a question to edit.")
        return
    index = selected[0]
    q = questions[index]
    new_text = simpledialog.askstring("Edit Question", "Update question text:", initialvalue=q["question"])
    if not new_text:
        return
    q["question"] = new_text
    if q["type"] == "multiple_choice":
        new_options = simpledialog.askstring("Edit Options", "Update options (comma-separated):", initialvalue=", ".join(q["options"]))
        if new_options:
            q["options"] = [opt.strip() for opt in new_options.split(",")]
    update_question_list()
    question_list.select_set(index)

# 💾 Save template
def save_template():
    title = title_entry.get().strip()
    if not title:
        messagebox.showwarning("Missing Title", "Please enter a form title before saving.")
        return
    if not questions:
        messagebox.showwarning("No Questions", "Please add questions before saving.")
        return
    template = {"title": title, "questions": questions}
    templates = {}
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            templates = json.load(f)
    templates[title] = template
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2)
    refresh_template_menu()
    messagebox.showinfo("Saved", f"Template '{title}' saved successfully!")

# 📥 Load selected template
def load_selected_template():
    name = selected_template.get()
    if not name or name not in template_names:
        messagebox.showwarning("Invalid Selection", "Please select a valid template.")
        return
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        templates = json.load(f)
    template = templates[name]
    title_entry.delete(0, tk.END)
    title_entry.insert(0, template["title"])
    questions.clear()
    questions.extend(template["questions"])
    update_question_list()
    messagebox.showinfo("Loaded", f"Template '{name}' loaded!")

# 🗑️ Delete selected template
def delete_selected_template():
    name = selected_template.get()
    if not name or name not in template_names:
        messagebox.showwarning("Invalid Selection", "Please select a valid template to delete.")
        return
    confirm = messagebox.askyesno("Delete Template", f"Are you sure you want to delete '{name}'?")
    if not confirm:
        return
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        templates = json.load(f)
    del templates[name]
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2)
    selected_template.set("Select a template")
    refresh_template_menu()
    messagebox.showinfo("Deleted", f"Template '{name}' has been deleted.")

# 🔄 Refresh dropdown menu
def refresh_template_menu():
    template_menu["menu"].delete(0, "end")
    template_names.clear()
    if not os.path.exists(TEMPLATE_FILE):
        return
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        templates = json.load(f)
    for name in templates.keys():
        template_names.append(name)
        template_menu["menu"].add_command(label=name, command=tk._setit(selected_template, name))

# 🧪 Generate form
def generate_form():
    title = title_entry.get().strip()
    if not title:
        messagebox.showwarning("Missing Title", "Please enter a form title.")
        return
    if not questions:
        messagebox.showwarning("No Questions", "Please add at least one question.")
        return
    form_data = {"title": title, "questions": questions}
    result = send_to_google_script(form_data)
    if result:
        result_label.config(text="Form created! Copy the link below:")
        result_entry.delete(0, tk.END)
        result_entry.insert(0, result)
        save_form_history(title, result)
    else:
        messagebox.showerror("Error", "Failed to create form. Check your script URL and access settings.")

# 📋 Copy link
def copy_to_clipboard():
    link = result_entry.get()
    if link:
        root.clipboard_clear()
        root.clipboard_append(link)
        messagebox.showinfo("Copied", "Form link copied to clipboard!")

# 🆘 Help window
def open_help_window():
    help_win = tk.Toplevel(root)
    help_win.title("Help - How to Use This App")
    help_win.geometry("700x500")

    help_text = """🚀 How to Use Khalid’s AI Form Builder with Your Own Google Account
STEP 1: Deploy Your Own Google Apps Script
1. Go to https://script.google.com
2. Click 'New Project'
3. Paste the code below
4. Click 'Deploy' > 'Test deployments' > 'Web App'
5. Set:
   - Execute as: Me
   - Who has access: Anyone
6. Click 'Deploy'
7. Copy the Web App URL

STEP 2: Use the Script in Khalid’s App
1. Paste your Script URL into the field labeled 'Your Google Script URL'
2. Build your form
3. Click 'Generate Form'
4. Your form will appear in your Google Drive
5. Copy and share the link!

✅ Tips:
- Save templates to reuse later
- Use 'Load Template' and 'Delete Template' to manage drafts
"""

    script_code = """function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var form = FormApp.create(data.title);
    data.questions.forEach(function(q) {
      if (q.type === "short_answer") {
        form.addTextItem().setTitle(q.question);
      } else if (q.type === "paragraph") {
        form.addParagraphTextItem().setTitle(q.question);
      } else if (q.type === "multiple_choice") {
        form.addMultipleChoiceItem()
            .setTitle(q.question)
            .setChoiceValues(q.options);
      }
    });
    return ContentService.createTextOutput(form.getEditUrl());
  } catch (err) {
    return ContentService.createTextOutput("Error: " + err.message);
  }
}"""

    text_widget = tk.Text(help_win, wrap="word", padx=10, pady=10)
    text_widget.insert("1.0", help_text + "\n\n📜 Google Apps Script Code:\n\n" + script_code)
    text_widget.config(state="disabled")
    text_widget.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(help_win, command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    def copy_script():
        help_win.clipboard_clear()
        help_win.clipboard_append(script_code)
        messagebox.showinfo("Copied", "Script code copied to clipboard!")

    tk.Button(help_win, text="Copy Script Code", command=copy_script).pack(pady=10)


    # Help text area
    text_widget = tk.Text(help_win, wrap="word", padx=10, pady=10)
    text_widget.insert("1.0", help_text + "\n\n📜 Google Apps Script Code:\n\n" + script_code)
    text_widget.config(state="disabled")
    text_widget.pack(fill="both", expand=True)

    # Scrollbar
    scrollbar = tk.Scrollbar(help_win, command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Copy button
    def copy_script():
        help_win.clipboard_clear()
        help_win.clipboard_append(script_code)
        messagebox.showinfo("Copied", "Script code copied to clipboard!")

    tk.Button(help_win, text="Copy Script Code", command=copy_script).pack(pady=10)




# 🖼️ GUI Setup
root = tk.Tk()
root.title("Manual Google Form Builder")

# Variables
selected_template = tk.StringVar()
selected_template.set("Select a template")
user_script_url = tk.StringVar()
question_type = tk.StringVar(value="short_answer")

# Script URL input
tk.Label(root, text="Your Google Script URL:").pack()
tk.Entry(root, textvariable=user_script_url, width=60).pack(pady=5)

# Form title
tk.Label(root, text="Form Title:").pack()
title_entry = tk.Entry(root, width=60)
title_entry.pack(pady=5)

# Question input
tk.Label(root, text="Add a Question:").pack()
question_entry = tk.Entry(root, width=60)
question_entry.pack(pady=5)

# Question type selector
tk.OptionMenu(root, question_type, "short_answer", "paragraph", "multiple_choice").pack(pady=5)

# Add question button
tk.Button(root, text="Add Question", command=add_question).pack(pady=5)

# Question list
tk.Label(root, text="Questions Added:").pack()
question_list = tk.Listbox(root, width=80, height=8)
question_list.pack(pady=5)

# Question controls
tk.Button(root, text="Remove Question", command=remove_selected_question).pack(pady=2)
tk.Button(root, text="Move Up", command=move_question_up).pack(pady=2)
tk.Button(root, text="Move Down", command=move_question_down).pack(pady=2)
tk.Button(root, text="Edit Question", command=edit_selected_question).pack(pady=2)

# Template controls
tk.Button(root, text="Save as Template", command=save_template).pack(pady=2)

tk.Label(root, text="Load a Saved Template:").pack()
template_menu = tk.OptionMenu(root, selected_template, ())
template_menu.pack(pady=2)

tk.Button(root, text="Load Selected Template", command=load_selected_template).pack(pady=2)
tk.Button(root, text="Delete Template", command=delete_selected_template).pack(pady=2)

# Generate form
tk.Button(root, text="Generate Form", command=generate_form).pack(pady=10)

# Result display
result_label = tk.Label(root, text="", fg="green")
result_label.pack(pady=5)

result_entry = tk.Entry(root, width=60)
result_entry.pack(pady=5)

tk.Button(root, text="Copy Link", command=copy_to_clipboard).pack(pady=5)

# Help button
tk.Button(root, text="Help", command=open_help_window).pack(pady=5)

# Start the app
refresh_template_menu()
root.mainloop()

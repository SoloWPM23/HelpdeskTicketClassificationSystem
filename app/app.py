import os
os.environ["USE_TF"] = "0"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import torch
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk, scrolledtext
import imaplib
import email
from email.header import decode_header
import pandas as pd
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import datetime

COLORS = {
    'primary': '#0F1E3D',      
    'secondary': '#A63D4F',    
    'bg_white': '#FFFFFF',
    'bg_light': '#F5F5F5',
    'input_bg': '#F0F0F0',
    'border': '#E0E0E0',
    'text_dark': '#333333',
    'text_light': '#888888',
    'header_bg': '#0F1E3D',
    'row_alt': '#E8E8E8',
}

def load_model(model_path='../weight/best.pt'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(model_path, map_location=device)
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=checkpoint['num_labels']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    label_classes = checkpoint['label_encoder_classes']
    return model, tokenizer, device, checkpoint['best_params']['max_length'], label_classes

# Predict priority
def predict_priority(text, model, tokenizer, device, max_length, label_classes):
    encoding = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    with torch.no_grad():
        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        prediction = torch.argmax(outputs.logits, dim=1).item()
    return label_classes[prediction]

# Custom rounded button class with hover effect
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg_color, fg_color='white', width=120, height=36, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.width = width
        self.height = height
        self.is_hovering = False
        
        self.draw_button()
        self.bind('<Button-1>', self.on_click)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def draw_button(self, hover=False, pressed=False):
        self.delete('all')
        radius = 8
        
        # Determine color based on state
        if pressed:
            color = self.darken_color(self.bg_color)
        elif hover:
            color = self.lighten_color(self.bg_color)
        else:
            color = self.bg_color
        
        # Draw rounded rectangle
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, 0, self.width, radius*2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, self.height-radius*2, radius*2, self.height, start=180, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, self.height-radius*2, self.width, self.height, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(radius, 0, self.width-radius, self.height, fill=color, outline=color)
        self.create_rectangle(0, radius, self.width, self.height-radius, fill=color, outline=color)
        
        # Draw text
        self.create_text(self.width/2, self.height/2, text=self.text, fill=self.fg_color, font=('Segoe UI', 10, 'bold'))
        
        # Change cursor on hover
        self.config(cursor='hand2' if hover else '')
    
    def lighten_color(self, hex_color):
        # Lighten color for hover effect
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c + (255 - c) * 0.2)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def darken_color(self, hex_color):
        # Darken color for pressed effect
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, int(c * 0.8)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def on_click(self, event):
        self.draw_button(pressed=True)
    
    def on_release(self, event):
        self.draw_button(hover=self.is_hovering)
        if self.command:
            self.command()
    
    def on_enter(self, event):
        self.is_hovering = True
        self.draw_button(hover=True)
    
    def on_leave(self, event):
        self.is_hovering = False
        self.draw_button(hover=False)

class EmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IT Support Email Manager")
        self.root.geometry("1100x700")
        self.root.state('zoomed')  # Maximize window on startup
        self.root.configure(bg=COLORS['bg_white'])
        
        # Configure ttk styles
        self.setup_styles()

        self.model, self.tokenizer, self.device, self.max_length, self.label_classes = load_model()

        self.emails_df = pd.DataFrame(columns=['Date', 'From', 'Subject', 'Body', 'Priority', 'Status', 'Resolved_Time'])

        self.login_frame = tk.Frame(self.root, bg=COLORS['bg_white'])
        self.main_frame = tk.Frame(self.root, bg=COLORS['bg_white'])

        self.setup_login()
        self.show_login()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview styling
        style.configure('Custom.Treeview',
                       background=COLORS['bg_light'],
                       foreground=COLORS['text_dark'],
                       rowheight=40,
                       fieldbackground=COLORS['bg_light'],
                       font=('Segoe UI', 10))
        style.configure('Custom.Treeview.Heading',
                       background=COLORS['header_bg'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        style.map('Custom.Treeview.Heading',
                 background=[('active', COLORS['header_bg'])])
        style.map('Custom.Treeview',
                 background=[('selected', COLORS['primary'])],
                 foreground=[('selected', 'white')])

    def setup_login(self):
        # Center container
        center_frame = tk.Frame(self.login_frame, bg=COLORS['bg_white'])
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Email label and entry
        email_label = tk.Label(center_frame, text="Email:", font=('Segoe UI', 11), 
                              bg=COLORS['bg_white'], fg=COLORS['text_dark'], anchor='w')
        email_label.pack(anchor='w', pady=(0, 5))
        
        email_frame = tk.Frame(center_frame, bg=COLORS['input_bg'], highlightbackground=COLORS['border'],
                              highlightthickness=1)
        email_frame.pack(fill='x', pady=(0, 20))
        
        self.email_entry = tk.Entry(email_frame, font=('Segoe UI', 11), bg=COLORS['input_bg'],
                                    fg=COLORS['text_dark'], relief='flat', width=50)
        self.email_entry.pack(padx=10, pady=10)
        self.email_entry.insert(0, "Type your email here...")
        self.email_entry.config(fg=COLORS['text_light'])
        self.email_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(self.email_entry, "Type your email here..."))
        self.email_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(self.email_entry, "Type your email here..."))
        
        # Password label and entry
        pass_label = tk.Label(center_frame, text="Password:", font=('Segoe UI', 11),
                             bg=COLORS['bg_white'], fg=COLORS['text_dark'], anchor='w')
        pass_label.pack(anchor='w', pady=(0, 5))
        
        pass_frame = tk.Frame(center_frame, bg=COLORS['input_bg'], highlightbackground=COLORS['border'],
                             highlightthickness=1)
        pass_frame.pack(fill='x', pady=(0, 30))
        
        self.pass_entry = tk.Entry(pass_frame, font=('Segoe UI', 11), bg=COLORS['input_bg'],
                                   fg=COLORS['text_light'], relief='flat', width=50)
        self.pass_entry.pack(padx=10, pady=10)
        self.pass_entry.insert(0, "Type your app password here...")
        self.pass_entry.bind('<FocusIn>', lambda e: self.on_pass_focus_in())
        self.pass_entry.bind('<FocusOut>', lambda e: self.on_pass_focus_out())
        
        # Login button container (right-aligned)
        btn_frame = tk.Frame(center_frame, bg=COLORS['bg_white'])
        btn_frame.pack(fill='x')
        
        login_btn = RoundedButton(btn_frame, text="Login", command=self.login,
                                  bg_color=COLORS['primary'], width=150, height=40)
        login_btn.pack(side='right')
    
    def on_entry_focus_in(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, 'end')
            entry.config(fg=COLORS['text_dark'])
    
    def on_entry_focus_out(self, entry, placeholder):
        if entry.get() == '':
            entry.insert(0, placeholder)
            entry.config(fg=COLORS['text_light'])
    
    def on_pass_focus_in(self):
        if self.pass_entry.get() == "Type your app password here...":
            self.pass_entry.delete(0, 'end')
            self.pass_entry.config(fg=COLORS['text_dark'], show='*')
    
    def on_pass_focus_out(self):
        if self.pass_entry.get() == '':
            self.pass_entry.config(show='')
            self.pass_entry.insert(0, "Type your app password here...")
            self.pass_entry.config(fg=COLORS['text_light'])

    def show_login(self):
        self.main_frame.pack_forget()
        self.login_frame.pack(fill=tk.BOTH, expand=True)

    def login(self):
        user_email = self.email_entry.get()
        user_pass = self.pass_entry.get()
        
        # Check for placeholder text
        if user_email == "Type your email here..." or not user_email:
            messagebox.showerror("Error", "Please enter email")
            return
        if user_pass == "Type your app password here..." or not user_pass:
            messagebox.showerror("Error", "Please enter password")
            return
        
        self.user_email = user_email
        self.user_pass = user_pass
        
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(self.user_email, self.user_pass)
            self.mail.select("inbox")
            messagebox.showinfo("Success", "Login successful")
            self.show_main()
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")

    def show_main(self):
        self.login_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Clear any existing widgets in main_frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Top button bar (right-aligned)
        top_bar = tk.Frame(self.main_frame, bg=COLORS['bg_white'])
        top_bar.pack(fill='x', padx=40, pady=(30, 20))
        
        # Spacer to push buttons to right
        spacer = tk.Frame(top_bar, bg=COLORS['bg_white'])
        spacer.pack(side='left', fill='x', expand=True)
        
        # Buttons container
        btn_container = tk.Frame(top_bar, bg=COLORS['bg_white'])
        btn_container.pack(side='right')
        
        load_btn = RoundedButton(btn_container, text="Load Emails", command=self.check_emails,
                                bg_color=COLORS['primary'], width=120, height=36)
        load_btn.pack(side='left', padx=(0, 10))
        
        download_btn = RoundedButton(btn_container, text="Download", command=self.download_excel,
                                    bg_color=COLORS['primary'], width=120, height=36)
        download_btn.pack(side='left', padx=(0, 10))
        
        logout_btn = RoundedButton(btn_container, text="Logout", command=self.logout,
                                  bg_color=COLORS['secondary'], width=120, height=36)
        logout_btn.pack(side='left')

        # Search bar area
        search_frame = tk.Frame(self.main_frame, bg=COLORS['bg_white'])
        search_frame.pack(fill='x', padx=40, pady=(0, 20))
        
        # Search entry with rounded border
        search_container = tk.Frame(search_frame, bg=COLORS['bg_white'], highlightbackground=COLORS['border'],
                                   highlightthickness=1, highlightcolor=COLORS['primary'])
        search_container.pack(side='left', fill='x', expand=True, padx=(0, 15))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var, font=('Segoe UI', 11),
                                     bg=COLORS['bg_white'], fg=COLORS['text_light'], relief='flat', width=60)
        self.search_entry.pack(padx=15, pady=10, fill='x', expand=True)
        self.search_entry.insert(0, "Search by subject, sender, or content...")
        self.search_entry.bind('<FocusIn>', lambda e: self.on_search_focus_in())
        self.search_entry.bind('<FocusOut>', lambda e: self.on_search_focus_out())
        
        # Search and Reset buttons
        search_btn = RoundedButton(search_frame, text="Search", command=self.filter_list,
                                  bg_color=COLORS['primary'], width=100, height=36)
        search_btn.pack(side='left', padx=(0, 10))
        
        reset_btn = RoundedButton(search_frame, text="Reset", command=self.reset_filter,
                                 bg_color=COLORS['primary'], width=100, height=36)
        reset_btn.pack(side='left')

        # Table frame
        table_frame = tk.Frame(self.main_frame, bg=COLORS['bg_white'])
        table_frame.pack(fill='both', expand=True, padx=40, pady=(0, 10))

        columns = ("Date", "From", "Subject", "Priority", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Custom.Treeview')
        
        # Configure columns
        col_widths = {'Date': 150, 'From': 200, 'Subject': 350, 'Priority': 100, 'Status': 100}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self.on_tree_double)
        
        # Configure alternating row colors
        self.tree.tag_configure('oddrow', background=COLORS['bg_light'])
        self.tree.tag_configure('evenrow', background=COLORS['row_alt'])
        self.tree.tag_configure('Escalated', background='#FFF4E5')
        self.tree.tag_configure('Done', background='#E8F5E9')

        # Note at bottom
        note_frame = tk.Frame(self.main_frame, bg=COLORS['bg_white'])
        note_frame.pack(fill='x', padx=40, pady=(0, 20))
        
        note_label = tk.Label(note_frame, text="Note:", font=('Segoe UI', 10, 'bold'),
                             bg=COLORS['bg_white'], fg=COLORS['text_dark'])
        note_label.pack(side='left')
        
        note_text = tk.Label(note_frame, text="  Double click to see email detail",
                            font=('Segoe UI', 10), bg=COLORS['bg_white'], fg=COLORS['text_dark'])
        note_text.pack(side='left')
    
    def on_search_focus_in(self):
        if self.search_var.get() == "Search by subject, sender, or content...":
            self.search_entry.delete(0, 'end')
            self.search_entry.config(fg=COLORS['text_dark'])
    
    def on_search_focus_out(self):
        if self.search_var.get() == '':
            self.search_entry.insert(0, "Search by subject, sender, or content...")
            self.search_entry.config(fg=COLORS['text_light'])

    def check_emails(self):
        try:
            status, messages = self.mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()

            self.emails_df = pd.DataFrame(columns=['Date', 'From', 'Subject', 'Body', 'Priority', 'Status', 'Resolved_Time'])

            for e_id in email_ids[-10:]:  # Last 10 emails
                status, msg_data = self.mail.fetch(e_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                from_ = decode_header(email_message["From"])[0][0]
                if isinstance(from_, bytes):
                    from_ = from_.decode()
                date = email_message["Date"]

                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()

                priority = predict_priority(body, self.model, self.tokenizer, self.device, self.max_length, self.label_classes)

                self.emails_df = pd.concat([self.emails_df, pd.DataFrame([{
                    'Date': date,
                    'From': from_,
                    'Subject': subject,
                    'Body': body,
                    'Priority': priority,
                    'Status': 'New',
                    'Resolved_Time': None
                }])], ignore_index=True)

            self.update_email_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check emails: {str(e)}")

    def update_email_list(self):
        # Populate Treeview from self.display_df if present (filter), else self.emails_df
        df = getattr(self, 'display_df', self.emails_df)
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, row in df.iterrows():
            tags = []
            # Add status tag
            status = row['Status']
            if status == 'Escalated':
                tags.append('Escalated')
            elif status == 'Done':
                tags.append('Done')
            else:
                tags.append('oddrow' if idx % 2 == 0 else 'evenrow')
            
            self.tree.insert('', 'end', iid=str(idx), 
                           values=(row['Date'], row['From'], row['Subject'], row['Priority'], row['Status']),
                           tags=tuple(tags))

    def on_email_click(self, event):
        # kept for compatibility; Treeview double-click handler used instead
        pass

    def on_tree_double(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        row = self.emails_df.iloc[idx]
        if row['Status'] == 'Escalated':
            self.show_escalated_detail(idx)
        elif row['Status'] == 'Done':
            self.show_done_detail(idx)
        else:
            self.show_email_detail(idx)

    def filter_list(self):
        q = self.search_var.get().strip().lower()
        if not q or q == "search by subject, sender, or content...":
            self.reset_filter()
            return
        df = self.emails_df.copy()
        mask = df['Subject'].str.lower().str.contains(q, na=False) | df['From'].str.lower().str.contains(q, na=False) | df['Body'].str.lower().str.contains(q, na=False)
        # keep original index mapping
        self.display_df = df[mask]
        self.update_email_list()

    def reset_filter(self):
        if hasattr(self, 'display_df'):
            delattr(self, 'display_df')
        self.search_var.set('')
        self.search_entry.delete(0, 'end')
        self.search_entry.insert(0, "Search by subject, sender, or content...")
        self.search_entry.config(fg=COLORS['text_light'])
        self.update_email_list()

    def show_email_detail(self, idx):
        # Enhanced email detail view matching UI design
        row = self.emails_df.iloc[idx]
        detail_win = tk.Toplevel(self.root)
        detail_win.title("Email Details")
        detail_win.geometry("850x600")
        detail_win.state('zoomed')  # Maximize detail window
        detail_win.configure(bg=COLORS['bg_white'])
        detail_win.resizable(True, True)

        main_container = tk.Frame(detail_win, bg=COLORS['bg_white'])
        main_container.pack(fill='both', expand=True, padx=30, pady=20)

        # Top section with form fields
        form_frame = tk.Frame(main_container, bg=COLORS['bg_white'])
        form_frame.pack(fill='x', pady=(0, 15))
        
        # Left side - Form fields
        left_form = tk.Frame(form_frame, bg=COLORS['bg_white'])
        left_form.pack(side='left', fill='x', expand=True)
        
        # From field
        from_row = tk.Frame(left_form, bg=COLORS['bg_white'])
        from_row.pack(fill='x', pady=5)
        
        from_label = tk.Label(from_row, text="From", font=('Segoe UI', 10, 'bold'),
                             bg=COLORS['primary'], fg='white', padx=15, pady=8, width=10)
        from_label.pack(side='left')
        
        from_value_frame = tk.Frame(from_row, bg=COLORS['bg_white'], highlightbackground=COLORS['border'],
                                   highlightthickness=1)
        from_value_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))
        from_value = tk.Label(from_value_frame, text=row['From'], font=('Segoe UI', 10),
                             bg=COLORS['bg_white'], fg=COLORS['text_dark'], anchor='w', padx=10, pady=8)
        from_value.pack(fill='x')
        
        # Subject field
        subject_row = tk.Frame(left_form, bg=COLORS['bg_white'])
        subject_row.pack(fill='x', pady=5)
        
        subject_label = tk.Label(subject_row, text="Subject", font=('Segoe UI', 10, 'bold'),
                                bg=COLORS['primary'], fg='white', padx=15, pady=8, width=10)
        subject_label.pack(side='left')
        
        subject_value_frame = tk.Frame(subject_row, bg=COLORS['bg_white'], highlightbackground=COLORS['border'],
                                      highlightthickness=1)
        subject_value_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))
        subject_value = tk.Label(subject_value_frame, text=row['Subject'], font=('Segoe UI', 10),
                                bg=COLORS['bg_white'], fg=COLORS['text_dark'], anchor='w', padx=10, pady=8)
        subject_value.pack(fill='x')
        
        # Date field
        date_row = tk.Frame(left_form, bg=COLORS['bg_white'])
        date_row.pack(fill='x', pady=5)
        
        date_label = tk.Label(date_row, text="Date", font=('Segoe UI', 10, 'bold'),
                             bg=COLORS['primary'], fg='white', padx=15, pady=8, width=10)
        date_label.pack(side='left')
        
        date_value_frame = tk.Frame(date_row, bg=COLORS['bg_white'], highlightbackground=COLORS['border'],
                                   highlightthickness=1)
        date_value_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))
        date_value = tk.Label(date_value_frame, text=row.get('Date', ''), font=('Segoe UI', 10),
                             bg=COLORS['bg_white'], fg=COLORS['text_dark'], anchor='w', padx=10, pady=8)
        date_value.pack(fill='x')
        
        # Right side - Priority badge
        right_form = tk.Frame(form_frame, bg=COLORS['bg_white'])
        right_form.pack(side='right', anchor='n', padx=(20, 0))
        
        priority_container = tk.Frame(right_form, bg=COLORS['bg_white'])
        priority_container.pack(anchor='e')
        
        priority_label = tk.Label(priority_container, text="Priority:", font=('Segoe UI', 10),
                                 bg=COLORS['bg_white'], fg=COLORS['text_dark'])
        priority_label.pack(side='left', padx=(0, 10))
        
        # Priority badge with color
        priority = str(row.get('Priority', ''))
        priority_colors = {'High': COLORS['secondary'], 'Medium': '#E6A23C', 'Low': '#67C23A'}
        badge_color = priority_colors.get(priority, COLORS['primary'])
        
        priority_badge = tk.Label(priority_container, text=priority, font=('Segoe UI', 10, 'bold'),
                                 bg=badge_color, fg='white', padx=15, pady=5)
        priority_badge.pack(side='left')

        # Email body frame with border
        body_container = tk.Frame(main_container, bg=COLORS['bg_white'], highlightbackground=COLORS['border'],
                                 highlightthickness=1)
        body_container.pack(fill='both', expand=True, pady=(10, 15))
        
        body_inner = tk.Frame(body_container, bg=COLORS['bg_light'])
        body_inner.pack(fill='both', expand=True, padx=2, pady=2)
        
        body_text = scrolledtext.ScrolledText(body_inner, wrap=tk.WORD, font=('Segoe UI', 10),
                                             bg=COLORS['bg_light'], fg=COLORS['text_dark'],
                                             relief='flat', borderwidth=0)
        
        # Show placeholder or actual content
        body_content = row['Body'] if row['Body'] else "Email body will appear here..."
        if not row['Body']:
            body_text.insert(tk.END, body_content)
            body_text.config(fg=COLORS['text_light'])
        else:
            body_text.insert(tk.END, body_content)
        
        body_text.configure(state='disabled')
        body_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Action buttons at bottom right
        action_frame = tk.Frame(main_container, bg=COLORS['bg_white'])
        action_frame.pack(fill='x')
        
        # Spacer
        spacer = tk.Frame(action_frame, bg=COLORS['bg_white'])
        spacer.pack(side='left', fill='x', expand=True)
        
        # Buttons container
        btn_container = tk.Frame(action_frame, bg=COLORS['bg_white'])
        btn_container.pack(side='right')
        
        escalate_btn = RoundedButton(btn_container, text="Escalated", 
                                    command=lambda: self.escalate_email(idx, detail_win),
                                    bg_color=COLORS['primary'], width=100, height=36)
        escalate_btn.pack(side='left', padx=(0, 10))
        
        done_btn = RoundedButton(btn_container, text="Reset",
                                command=lambda: self.done_email(idx, detail_win),
                                bg_color=COLORS['secondary'], width=100, height=36)
        done_btn.pack(side='left', padx=(0, 10))
        
        # Close button (X)
        close_btn = RoundedButton(btn_container, text="✕",
                                 command=detail_win.destroy,
                                 bg_color=COLORS['primary'], width=40, height=36)
        close_btn.pack(side='left')

    def escalate_email(self, idx, win):
        self.emails_df.at[idx, 'Status'] = 'Escalated'
        self.update_email_list()
        win.destroy()
        messagebox.showinfo("Escalated", "Issue has been escalated.")

    def done_email(self, idx, win):
        resolved_time = simpledialog.askstring("Done", "Enter resolution time (e.g., 2 hours):")
        if resolved_time:
            self.emails_df.at[idx, 'Status'] = 'Done'
            self.emails_df.at[idx, 'Resolved_Time'] = resolved_time
            self.update_email_list()
            win.destroy()
            messagebox.showinfo("Done", "Issue marked as done.")

    def erase_email(self, idx, win):
        self.emails_df = self.emails_df.drop(idx).reset_index(drop=True)
        self.update_email_list()
        win.destroy()
        messagebox.showinfo("Deleted", "Issue has been deleted.")

    def show_escalated_detail(self, idx):
        row = self.emails_df.iloc[idx]
        detail_win = tk.Toplevel(self.root)
        detail_win.title("Escalated Issue")
        detail_win.geometry("450x220")
        detail_win.configure(bg=COLORS['bg_white'])
        detail_win.resizable(False, False)

        container = tk.Frame(detail_win, bg=COLORS['bg_white'])
        container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Message
        msg_label = tk.Label(container, text="This issue is being handled by the team.",
                            font=('Segoe UI', 12), bg=COLORS['bg_white'], fg=COLORS['text_dark'])
        msg_label.pack(pady=(20, 30))
        
        # Button container
        btn_frame = tk.Frame(container, bg=COLORS['bg_white'])
        btn_frame.pack()
        
        done_btn = RoundedButton(btn_frame, text="Mark as Done",
                                command=lambda: self.done_escalated(idx, detail_win),
                                bg_color=COLORS['primary'], width=140, height=40)
        done_btn.pack()

    def show_done_detail(self, idx):
        row = self.emails_df.iloc[idx]
        detail_win = tk.Toplevel(self.root)
        detail_win.title("Completed Issue")
        detail_win.geometry("450x280")
        detail_win.configure(bg=COLORS['bg_white'])
        detail_win.resizable(False, False)

        container = tk.Frame(detail_win, bg=COLORS['bg_white'])
        container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Message
        msg_label = tk.Label(container, text="This issue has been resolved.",
                            font=('Segoe UI', 12), bg=COLORS['bg_white'], fg=COLORS['text_dark'])
        msg_label.pack(pady=(10, 20))
        
        if pd.isna(row['Resolved_Time']):
            # Time entry
            time_label = tk.Label(container, text="Enter resolution time (e.g., 2 hours):",
                                 font=('Segoe UI', 10), bg=COLORS['bg_white'], fg=COLORS['text_dark'])
            time_label.pack(pady=(0, 10))
            
            entry_frame = tk.Frame(container, bg=COLORS['input_bg'], highlightbackground=COLORS['border'],
                                  highlightthickness=1)
            entry_frame.pack(pady=(0, 20))
            
            time_entry = tk.Entry(entry_frame, font=('Segoe UI', 11), bg=COLORS['input_bg'],
                                 fg=COLORS['text_dark'], relief='flat', width=30)
            time_entry.pack(padx=10, pady=8)
            
            submit_btn = RoundedButton(container, text="Submit",
                                      command=lambda: self.submit_time(idx, time_entry.get(), detail_win),
                                      bg_color=COLORS['primary'], width=120, height=40)
            submit_btn.pack()
        else:
            resolved_label = tk.Label(container, text=f"Resolution Time: {row['Resolved_Time']}",
                                     font=('Segoe UI', 11, 'bold'), bg=COLORS['bg_white'], fg=COLORS['primary'])
            resolved_label.pack(pady=20)

    def done_escalated(self, idx, win):
        resolved_time = simpledialog.askstring("Done", "Enter resolution time (e.g., 2 hours):")
        if resolved_time:
            self.emails_df.at[idx, 'Status'] = 'Done'
            self.emails_df.at[idx, 'Resolved_Time'] = resolved_time
            self.update_email_list()
            win.destroy()
            messagebox.showinfo("Done", "Issue marked as done.")

    def submit_time(self, idx, time, win):
        if time:
            self.emails_df.at[idx, 'Resolved_Time'] = time
            win.destroy()
            messagebox.showinfo("Success", "Time submitted.")

    def download_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.emails_df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", "Report exported successfully.")

    def logout(self):
        self.mail.logout()
        self.show_login()

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailApp(root)
    root.mainloop()
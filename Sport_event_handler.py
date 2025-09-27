import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from datetime import datetime

EXCEL_FILE = "campaigns.xlsx"
campaigns = []

class Marquee(tk.Frame):
    def __init__(self, parent, text, fps=20, step=1, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.fps = fps
        self.step = step
        self.text = text
        self.offset = 0
        self.label = tk.Label(self, text=self.text, anchor='w',
                              font=("Helvetica", 12, "bold"), fg="white", bg=self["bg"])
        self.label.pack(side="left", fill="both", expand=True)
        self.after_id = None
        self.start_marquee()

    def start_marquee(self):
        self.offset = (self.offset + self.step) % len(self.text)
        display_text = self.text[self.offset:] + "   " + self.text[:self.offset]
        self.label.config(text=display_text)
        self.after_id = self.after(int(2000/self.fps), self.start_marquee)

    def stop_marquee(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def set_text(self, new_text):
        self.text = new_text
        self.offset = 0

def load_from_excel():
    global campaigns
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        required_keys = ["id", "event_id", "name", "strategy", "budget",
                         "start_date", "end_date", "match_date", "available_slots", "booked_slots"]
        for key in required_keys:
            if key not in df.columns:
                df[key] = None
        df.fillna(0, inplace=True)
        df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce")
        df["efficiency"] = df.apply(lambda row: (row["booked_slots"] / row["available_slots"]) * 100
                                     if row["available_slots"] > 0 else 0, axis=1)
        campaigns[:] = df.to_dict(orient="records")
        update_treeview()
        update_marquee_text()

def update_treeview():
    for row in tree.get_children():
        tree.delete(row)
    for campaign in campaigns:
        available_slots = int(campaign.get("available_slots", 1))
        booked_slots = int(campaign.get("booked_slots", 0))
        efficiency = (booked_slots / available_slots) * 100 if available_slots > 0 else 0
        tree.insert("", "end", values=(
            campaign.get("id", "N/A"),
            campaign.get("event_id", "N/A"),
            campaign.get("name", "N/A"),
            campaign.get("strategy", "N/A"),
            campaign.get("budget", "N/A"),
            campaign.get("start_date", "N/A"),
            campaign.get("end_date", "N/A"),
            campaign.get("match_date", "N/A"),
            campaign.get("available_slots", "N/A"),
            campaign.get("booked_slots", "N/A"),
            f"{efficiency:.2f}%"
        ))

def save_to_excel():
    df = pd.DataFrame(campaigns)
    df.to_excel(EXCEL_FILE, index=False)

def validate_int(value):
    try:
        return int(value)
    except ValueError:
        return 0

def add_campaign():
    new_campaign = {
        "id": entry_id.get(),
        "event_id": entry_event_id.get(),
        "name": entry_name.get(),
        "strategy": entry_strategy.get(),
        "budget": entry_budget.get(),
        "start_date": start_date_entry.get_date(),
        "end_date": end_date_entry.get_date(),
        "match_date": match_date_entry.get_date(),
        "available_slots": validate_int(entry_available_slots.get()),
        "booked_slots": validate_int(entry_booked_slots.get())
    }
    campaigns.append(new_campaign)
    update_treeview()
    save_to_excel()
    update_marquee_text()
    messagebox.showinfo("Success", "Campaign Added Successfully!")

def update_campaign():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No campaign selected for update!")
        return
    for item in selected_item:
        campaign_id = tree.item(item)["values"][0]
        for campaign in campaigns:
            if campaign["id"] == campaign_id:
                campaign.update({
                    "event_id": entry_event_id.get(),
                    "name": entry_name.get(),
                    "strategy": entry_strategy.get(),
                    "budget": entry_budget.get(),
                    "start_date": start_date_entry.get_date(),
                    "end_date": end_date_entry.get_date(),
                    "match_date": match_date_entry.get_date(),
                    "available_slots": validate_int(entry_available_slots.get()),
                    "booked_slots": validate_int(entry_booked_slots.get())
                })
                break
    update_treeview()
    save_to_excel()
    update_marquee_text()
    messagebox.showinfo("Updated", "Campaign updated successfully!")

def delete_campaign():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No campaign selected!")
        return
    for item in selected_item:
        campaign_id = tree.item(item)["values"][0]
        campaigns[:] = [c for c in campaigns if c["id"] != campaign_id]
        tree.delete(item)
    save_to_excel()
    update_marquee_text()
    messagebox.showinfo("Deleted", "Campaign deleted successfully!")

def show_graph():
    df = pd.DataFrame(campaigns)
    if df.empty:
        messagebox.showwarning("No Data", "No campaigns to show in graph!")
        return
    df["efficiency"] = df.apply(lambda row: (row["booked_slots"] / row["available_slots"]) * 100
                                if row["available_slots"] > 0 else 0, axis=1)
    df["name"] = df["name"].astype(str)
    plt.figure(figsize=(10, 6))
    plt.bar(df["name"], df["efficiency"], color='green')
    plt.xlabel("Campaign Name")
    plt.ylabel("Efficiency (%)")
    plt.title("Campaign Efficiency")
    plt.xticks(rotation=45)
    plt.show()

def open_excel():
    if os.path.exists(EXCEL_FILE):
        os.startfile(EXCEL_FILE)
    else:
        messagebox.showwarning("File Not Found", f"{EXCEL_FILE} does not exist.")

def get_next_match_date():
    next_date = None
    now = datetime.now()
    for campaign in campaigns:
        match_date = campaign.get("match_date")
        if match_date:
            if not isinstance(match_date, pd.Timestamp):
                try:
                    match_date = pd.to_datetime(match_date)
                except Exception:
                    continue
            if match_date >= now:
                if next_date is None or match_date < next_date:
                    next_date = match_date
    return next_date.strftime("%Y-%m-%d") if next_date else "No upcoming match"

def update_marquee_text():
    next_match = get_next_match_date()
    marquee.set_text(f"Next Match Date: {next_match}")

def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return "break"

### MAIN WINDOW ###
root = tk.Tk()
root.title("Campaign Manager")

# 1) Give the main window a geometry so you can see background around frames
root.geometry("1000x700")  # width x height

# 2) Set a LIGHT background color so frames with dark background stand out
root.configure(bg="#B0C4DE")  # LightSteelBlue

root.option_add("*Font", "Helvetica 10")

### STYLE CONFIG ###
style = ttk.Style(root)
style.theme_use("clam")

style.configure("Treeview",
                background="white",
                foreground="black",
                rowheight=25,
                fieldbackground="white",
                borderwidth=1,
                relief="solid",
                highlightthickness=1)

style.configure("Treeview.Heading",
                background="#2980b9",
                foreground="white",
                relief="solid",
                borderwidth=1,
                highlightthickness=1)

style.map("Treeview", background=[('selected', '#347083')])

style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

### TITLE ###
title_label = tk.Label(root,
                       text="PROSPORTS MARKETING DASHBOARD",
                       font=("Arial", 20, "bold"),
                       bg="#B0C4DE",  # matches root background
                       fg="black")
title_label.pack(pady=10)

### MARQUEE ###
marquee = Marquee(root,
                  text="Next Match Date: Loading...",
                  fps=30,
                  step=1,
                  bg="red")  # stands out
marquee.pack(padx=100, pady=10, fill="y")

### INPUT FRAME ###
# Notice the background is #34495E so it looks different from root
input_frame = tk.Frame(root, bg="#34495E", highlightbackground="gray", highlightthickness=1)
input_frame.pack(pady=10)

labels = ["ID", "Event ID", "Name", "Strategy", "Budget",
          "Start Date", "End Date", "Match Date", "Available Slots", "Booked Slots"]
entries = {}
row_num = 0
for i, label in enumerate(labels):
    tk.Label(input_frame, text=label, bg="#34495E", fg="white").grid(
        row=row_num,
        column=i % 2 * 2,
        padx=5,
        pady=5,
        sticky="e"
    )
    if "Date" in label:
        widget = DateEntry(input_frame,
                           width=12,
                           background='darkblue',
                           foreground='white',
                           borderwidth=2)
    else:
        widget = tk.Entry(input_frame)
    widget.grid(row=row_num, column=i % 2 * 2 + 1, padx=5, pady=5, sticky="w")
    widget.bind("<Return>", focus_next_widget)
    entries[label] = widget
    if i % 2 == 1:
        row_num += 1

entry_id, entry_event_id, entry_name, entry_strategy, entry_budget = [
    entries[l] for l in labels[:5]
]
start_date_entry, end_date_entry, match_date_entry = [
    entries[l] for l in labels[5:8]
]
entry_available_slots, entry_booked_slots = [
    entries[l] for l in labels[8:10]
]

### BUTTON FRAME ###
button_frame = tk.Frame(root, bg="#34495E")
button_frame.pack(pady=5)

tk.Button(button_frame, text="Add Campaign", command=add_campaign,
          bg="#4CAF50", fg="white", padx=10, pady=5).grid(row=0, column=0, padx=5, pady=5)

tk.Button(button_frame, text="Update Campaign", command=update_campaign,
          bg="#FF9800", fg="white", padx=10, pady=5).grid(row=0, column=1, padx=5, pady=5)

tk.Button(button_frame, text="Delete Campaign", command=delete_campaign,
          bg="#F44336", fg="white", padx=10, pady=5).grid(row=0, column=2, padx=5, pady=5)

tk.Button(button_frame, text="Show Graph", command=show_graph,
          bg="#9C27B0", fg="white", padx=10, pady=5).grid(row=0, column=3, padx=5, pady=5)

tk.Button(button_frame, text="Open Excel", command=open_excel,
          bg="#3F51B5", fg="white", padx=10, pady=5).grid(row=0, column=4, padx=5, pady=5)

### TABLE FRAME ###
table_frame = tk.Frame(root, bg="#34495E", bd=2, relief="groove")
table_frame.pack(pady=10, fill="both", expand=True)

tree = ttk.Treeview(table_frame,
                    columns=labels + ["Efficiency"],
                    show="headings",
                    style="Treeview")
for col in labels + ["Efficiency"]:
    tree.heading(col, text=col)
    tree.column(col, width=100, anchor="center")
tree.pack(fill="both", expand=True, padx=5, pady=5)

### INITIAL LOAD ###
load_from_excel()

root.mainloop()

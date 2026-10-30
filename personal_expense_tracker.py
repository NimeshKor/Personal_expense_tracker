import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

# Data is saved locally in this database file.
DB_FILE = "expenses.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0)
)
""")
conn.commit()


def money(value):
    return f"₹{value:,.2f}"


# ---------- WINDOW ----------
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("1000x680")
root.minsize(850, 600)
root.configure(bg="#f3f6fb")

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("Treeview", rowheight=28, font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

header = tk.Frame(root, bg="#173b6c", padx=22, pady=18)
header.pack(fill="x")
tk.Label(
    header, text="PERSONAL EXPENSE TRACKER",
    font=("Arial", 20, "bold"), bg="#173b6c", fg="white"
).pack(anchor="w")
tk.Label(
    header, text="Record spending • Track categories • Understand your budget",
    font=("Arial", 10), bg="#173b6c", fg="#dbeafe"
).pack(anchor="w", pady=(5, 0))

# ---------- SUMMARY CARDS ----------
summary = tk.Frame(root, bg="#f3f6fb", padx=18, pady=14)
summary.pack(fill="x")


def make_card(parent, title, initial):
    card = tk.Frame(parent, bg="white", padx=15, pady=12,
                    highlightbackground="#dbe3ef", highlightthickness=1)
    card.pack(side="left", fill="x", expand=True, padx=5)
    tk.Label(card, text=title, bg="white", fg="#64748b",
             font=("Arial", 10)).pack(anchor="w")
    value_label = tk.Label(card, text=initial, bg="white", fg="#173b6c",
                           font=("Arial", 17, "bold"))
    value_label.pack(anchor="w", pady=(6, 0))
    return value_label


total_label = make_card(summary, "TOTAL SPENT", "₹0.00")
count_label = make_card(summary, "TRANSACTIONS", "0")
average_label = make_card(summary, "AVERAGE EXPENSE", "₹0.00")

# ---------- ENTRY FORM ----------
form = tk.LabelFrame(root, text=" Add an Expense ", bg="#f3f6fb",
                     padx=12, pady=10, font=("Arial", 10, "bold"))
form.pack(fill="x", padx=22, pady=(0, 12))

date_var = tk.StringVar(value=date.today().isoformat())
category_var = tk.StringVar(value="Food")
description_var = tk.StringVar()
amount_var = tk.StringVar()

tk.Label(form, text="Date (YYYY-MM-DD)", bg="#f3f6fb").grid(
    row=0, column=0, sticky="w", padx=6, pady=4)
date_entry = ttk.Entry(form, textvariable=date_var, width=18)
date_entry.grid(row=1, column=0, padx=6, pady=4, sticky="ew")

tk.Label(form, text="Category", bg="#f3f6fb").grid(
    row=0, column=1, sticky="w", padx=6, pady=4)
category_box = ttk.Combobox(
    form, textvariable=category_var, width=18, state="readonly",
    values=("Food", "Travel", "Shopping", "Bills", "Education",
            "Health", "Entertainment", "Other")
)
category_box.grid(row=1, column=1, padx=6, pady=4, sticky="ew")

tk.Label(form, text="Description", bg="#f3f6fb").grid(
    row=0, column=2, sticky="w", padx=6, pady=4)
ttk.Entry(form, textvariable=description_var, width=30).grid(
    row=1, column=2, padx=6, pady=4, sticky="ew")

tk.Label(form, text="Amount (₹)", bg="#f3f6fb").grid(
    row=0, column=3, sticky="w", padx=6, pady=4)
ttk.Entry(form, textvariable=amount_var, width=15).grid(
    row=1, column=3, padx=6, pady=4, sticky="ew")

for col in range(4):
    form.grid_columnconfigure(col, weight=1)

# ---------- TRANSACTION TABLE ----------
table_frame = tk.Frame(root, bg="#f3f6fb", padx=22)
table_frame.pack(fill="both", expand=True)

table_top = tk.Frame(table_frame, bg="#f3f6fb")
table_top.pack(fill="x", pady=(0, 7))
tk.Label(table_top, text="Expense History", bg="#f3f6fb",
         fg="#173b6c", font=("Arial", 13, "bold")).pack(side="left")

search_var = tk.StringVar()
ttk.Label(table_top, text="Search:").pack(side="left", padx=(20, 5))
search_entry = ttk.Entry(table_top, textvariable=search_var, width=24)
search_entry.pack(side="left")
ttk.Button(table_top, text="Search", command=lambda: load_expenses()).pack(
    side="left", padx=5)
ttk.Button(table_top, text="Show All",
           command=lambda: (search_var.set(""), load_expenses())).pack(side="left")

columns = ("id", "date", "category", "description", "amount")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
for col, heading, width in [
    ("id", "ID", 55), ("date", "Date", 125), ("category", "Category", 135),
    ("description", "Description", 360), ("amount", "Amount", 130)
]:
    tree.heading(col, text=heading)
    tree.column(col, width=width, anchor="center" if col != "description" else "w")
tree.pack(fill="both", expand=True)

# ---------- APPLICATION FUNCTIONS ----------
def clear_form():
    date_var.set(date.today().isoformat())
    category_var.set("Food")
    description_var.set("")
    amount_var.set("")
    tree.selection_remove(tree.selection())


def refresh_summary():
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses")
    count, total = cursor.fetchone()
    average = total / count if count else 0
    total_label.config(text=money(total))
    count_label.config(text=str(count))
    average_label.config(text=money(average))


def load_expenses():
    for item in tree.get_children():
        tree.delete(item)

    keyword = search_var.get().strip()
    if keyword:
        pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT id, expense_date, category, description, amount
            FROM expenses
            WHERE expense_date LIKE ? OR category LIKE ? OR description LIKE ?
            ORDER BY expense_date DESC, id DESC
        """, (pattern, pattern, pattern))
    else:
        cursor.execute("""
            SELECT id, expense_date, category, description, amount
            FROM expenses
            ORDER BY expense_date DESC, id DESC
        """)

    for expense_id, expense_date, category, description, amount in cursor.fetchall():
        tree.insert("", "end", values=(
            expense_id, expense_date, category, description, money(amount)
        ))
    refresh_summary()


def add_expense():
    expense_date = date_var.get().strip()
    category = category_var.get().strip()
    description = description_var.get().strip()
    amount_text = amount_var.get().strip()

    if not all((expense_date, category, description, amount_text)):
        messagebox.showwarning("Missing Information", "Please fill in every field.")
        return

    try:
        date.fromisoformat(expense_date)
    except ValueError:
        messagebox.showerror("Invalid Date", "Enter a valid date as YYYY-MM-DD.")
        return

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Amount", "Enter an amount greater than zero.")
        return

    cursor.execute("""
        INSERT INTO expenses (expense_date, category, description, amount)
        VALUES (?, ?, ?, ?)
    """, (expense_date, category, description, amount))
    conn.commit()
    search_var.set("")
    load_expenses()
    clear_form()
    messagebox.showinfo("Saved", "Expense added successfully.")


def delete_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Select Expense", "Select an expense from the table first.")
        return

    values = tree.item(selected[0], "values")
    expense_id = int(values[0])
    if not messagebox.askyesno("Confirm Delete", "Delete this expense?"):
        return

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    load_expenses()
    messagebox.showinfo("Deleted", "Expense deleted successfully.")


def show_category_summary():
    cursor.execute("""
        SELECT category, SUM(amount), COUNT(*)
        FROM expenses
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo("Category Summary", "No expenses recorded yet.")
        return

    lines = ["Spending by category", "--------------------"]
    for category, total, count in rows:
        lines.append(f"{category}: {money(total)} ({count} transaction(s))")
    messagebox.showinfo("Category Summary", "\n".join(lines))


# ---------- ACTION BUTTONS ----------
actions = tk.Frame(root, bg="#f3f6fb", padx=22, pady=12)
actions.pack(fill="x")

ttk.Button(actions, text="Add Expense", command=add_expense).pack(
    side="left", padx=(0, 8))
ttk.Button(actions, text="Delete Selected", command=delete_expense).pack(
    side="left", padx=8)
ttk.Button(actions, text="Clear Form", command=clear_form).pack(
    side="left", padx=8)
ttk.Button(actions, text="Category Summary", command=show_category_summary).pack(
    side="left", padx=8)

tk.Label(
    root,
    text="Your records are saved locally on this computer in expenses.db.",
    bg="#f3f6fb", fg="#64748b", font=("Arial", 9)
).pack(pady=(0, 10))

load_expenses()


def close_app():
    conn.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()

import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# -------------------- PRODUCT DATA (loaded fro     m CSV) --------------------
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products_full.csv")

def load_products(path):
    """Read products.csv (id,name,category,price,stock) into the same dict
    format used before: {id: {"name", "category", "price", "stock"}}"""
    data = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            data[int(row["id"])] = {
                "name": row["name"].strip(),
                "category": row["category"].strip(),
                "price": float(row["price"]),
                "stock": int(row["stock"]),
            }
    return data


try:
    products = load_products(CSV_FILE)
except FileNotFoundError:
    tk.Tk().withdraw()
    messagebox.showerror("File Not Found",
                         f"Could not find products.csv at:\n{CSV_FILE}\n\n"
                         "Place products.csv in the same folder as this script.")
    raise SystemExit
except (KeyError, ValueError) as e:
    tk.Tk().withdraw()
    messagebox.showerror("Invalid CSV",
                         f"products.csv must have columns id,name,category,price,stock.\n\nDetails: {e}")
    raise SystemExit

cart = {}


def subtotal():
    return sum(products[pid]["price"] * qty for pid, qty in cart.items())


def discount_amount(amount):
    if amount >= 10000:
        return amount * 0.10
    if amount >= 5000:
        return amount * 0.05
    return 0


def update_summary():
    sub = subtotal()
    discount = discount_amount(sub)
    taxable = sub - discount
    gst = taxable * 0.18
    total = taxable + gst

    subtotal_var.set(f"₹{sub:,.2f}")
    discount_var.set(f"₹{discount:,.2f}")
    gst_var.set(f"₹{gst:,.2f}")
    total_var.set(f"₹{total:,.2f}")
    cart_count_var.set(f"{sum(cart.values())} item(s)")


def populate_products(*_):
    """Fill the catalogue table, applying the search filter."""
    keep = product_tree.selection()
    for item in product_tree.get_children():
        product_tree.delete(item)

    term = search_var.get().strip().lower()
    for pid, p in products.items():
        if term and term not in p["name"].lower() and term not in p["category"].lower():
            continue
        product_tree.insert(
            "", "end", iid=str(pid),
            values=(pid, p["name"], p["category"],
                    f"₹{p['price']:,.2f}", p["stock"] if p["stock"] > 0 else "Out"),
            tags=("out",) if p["stock"] <= 0 else ()
        )
    for k in keep:
        if product_tree.exists(k):
            product_tree.selection_set(k)


def refresh_cart():
    for item in cart_tree.get_children():
        cart_tree.delete(item)

    for pid, qty in cart.items():
        p = products[pid]
        cart_tree.insert(
            "", "end", iid=str(pid),
            values=(pid, p["name"], qty, f"₹{p['price']:,.2f}",
                    f"₹{p['price'] * qty:,.2f}")
        )
    update_summary()


def read_quantity():
    try:
        qty = int(quantity_var.get())
    except ValueError:
        messagebox.showerror("Invalid Quantity", "Enter a valid quantity.")
        return None
    if qty <= 0:
        messagebox.showerror("Invalid Quantity", "Quantity must be greater than 0.")
        return None
    return qty


def add_to_cart():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("Select Product", "Please select a product first.")
        return

    pid = int(selected[0])
    qty = read_quantity()
    if qty is None:
        return

    current = cart.get(pid, 0)
    available = products[pid]["stock"] - current
    if qty > available:
        msg = ("This product is out of stock." if products[pid]["stock"] <= 0
               else f"Only {max(available, 0)} more item(s) are available.")
        messagebox.showerror("Stock Error", msg)
        return

    cart[pid] = current + qty
    quantity_var.set("1")
    refresh_cart()


def update_cart_quantity():
    selected = cart_tree.selection()
    if not selected:
        messagebox.showwarning("Select Item", "Select an item from the cart.")
        return

    pid = int(selected[0])
    qty = read_quantity()
    if qty is None:
        return

    if qty > products[pid]["stock"]:
        messagebox.showerror("Stock Error", "Requested quantity exceeds stock.")
        return

    cart[pid] = qty
    refresh_cart()


def remove_from_cart():
    selected = cart_tree.selection()
    if not selected:
        messagebox.showwarning("Select Item", "Select an item from the cart.")
        return

    del cart[int(selected[0])]
    refresh_cart()


def clear_cart():
    if cart and messagebox.askyesno("Clear Cart", "Remove all items from the cart?"):
        cart.clear()
        refresh_cart()


def checkout():
    if not cart:
        messagebox.showwarning("Empty Cart", "Add at least one product before checkout.")
        return

    sub = subtotal()
    discount = discount_amount(sub)
    taxable = sub - discount
    gst = taxable * 0.18
    total = taxable + gst
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    W = 74  # receipt width
    lines = [
        "=" * W,
        "SHOPPING CART RECEIPT".center(W),
        "=" * W,
        f"Date & Time: {now}",
        "-" * W,
        f"{'Product':<36}{'Qty':<6}{'Price':>16}{'Total':>16}",
        "-" * W,
    ]

    for pid, qty in cart.items():
        p = products[pid]
        name = p["name"] if len(p["name"]) <= 34 else p["name"][:33] + "…"
        lines.append(
            f"{name:<36}{qty:<6}"
            f"{'₹' + format(p['price'], ',.2f'):>16}"
            f"{'₹' + format(p['price'] * qty, ',.2f'):>16}"
        )

    label_w = W - 18
    lines += [
        "-" * W,
        f"{'Subtotal':>{label_w}} : ₹{sub:,.2f}",
        f"{'Discount':>{label_w}} : ₹{discount:,.2f}",
        f"{'Taxable Amount':>{label_w}} : ₹{taxable:,.2f}",
        f"{'GST (18%)':>{label_w}} : ₹{gst:,.2f}",
        "-" * W,
        f"{'FINAL TOTAL':>{label_w}} : ₹{total:,.2f}",
        "=" * W,
        "Thank you for shopping!".center(W),
        "=" * W,
    ]

    with open("receipt.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    # Deduct purchased quantities from stock
    for pid, qty in cart.items():
        products[pid]["stock"] -= qty
    cart.clear()
    refresh_cart()
    populate_products()

    messagebox.showinfo(
        "Order Confirmed",
        f"Order placed successfully!\n\nFinal Total: ₹{total:,.2f}\n\n"
        "Receipt saved as receipt.txt"
    )


def product_selected(event=None):
    if product_tree.selection():
        quantity_var.set("1")


def cart_selected(event=None):
    selected = cart_tree.selection()
    if selected:
        quantity_var.set(str(cart[int(selected[0])]))


# -------------------- WINDOW --------------------
root = tk.Tk()
root.title("ShopEase - Shopping Cart Management System")
root.geometry("1360x780")
root.minsize(1150, 700)
root.configure(bg="#eef2f7")

NAVY = "#172554"
BLUE = "#2563eb"
LIGHT_BLUE = "#eff6ff"
WHITE = "#ffffff"
BACKGROUND = "#eef2f7"
TEXT = "#172033"
MUTED = "#64748b"
BORDER = "#dbe2ea"
GREEN = "#15803d"
RED = "#dc2626"
SUMMARY_BG = "#f8fafc"

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview", rowheight=34, font=("Segoe UI", 10),
    background=WHITE, fieldbackground=WHITE, foreground=TEXT,
    borderwidth=0
)
style.configure(
    "Treeview.Heading", font=("Segoe UI", 10, "bold"),
    background="#e8eef7", foreground=TEXT, padding=8, relief="flat"
)
style.map("Treeview", background=[("selected", "#dbeafe")],
          foreground=[("selected", TEXT)])
style.configure("TEntry", font=("Segoe UI", 11), padding=7)

# -------------------- HEADER --------------------
header = tk.Frame(root, bg=NAVY, height=92)
header.pack(fill="x")
header.pack_propagate(False)

title_area = tk.Frame(header, bg=NAVY)
title_area.pack(side="left", padx=28, pady=14)

tk.Label(title_area, text="ShopEase", font=("Segoe UI", 25, "bold"),
         fg=WHITE, bg=NAVY).pack(anchor="w")
tk.Label(title_area, text="Shopping Cart Management System",
         font=("Segoe UI", 10), fg="#cbd5e1", bg=NAVY).pack(anchor="w")

cart_status = tk.Frame(header, bg=NAVY)
cart_status.pack(side="right", padx=30)

tk.Label(cart_status, text="CART", font=("Segoe UI", 9, "bold"),
         fg="#bfdbfe", bg=NAVY).pack(anchor="e")
cart_count_var = tk.StringVar(value="0 item(s)")
tk.Label(cart_status, textvariable=cart_count_var,
         font=("Segoe UI", 12, "bold"), fg=WHITE, bg=NAVY).pack(anchor="e")

# -------------------- MAIN --------------------
main = tk.Frame(root, bg=BACKGROUND)
main.pack(fill="both", expand=True, padx=24, pady=20)

# Cart panel has a fixed width; the catalogue takes the remaining space
right = tk.Frame(main, bg=WHITE, width=500,
                 highlightbackground=BORDER, highlightthickness=1)
right.pack(side="right", fill="y", padx=(10, 0))
right.pack_propagate(False)

left = tk.Frame(main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
left.pack(side="left", fill="both", expand=True, padx=(0, 10))

# -------------------- PRODUCT PANEL --------------------
product_header = tk.Frame(left, bg=WHITE)
product_header.pack(fill="x", padx=18, pady=(16, 8))

tk.Label(product_header, text="Product Catalogue",
         font=("Segoe UI", 17, "bold"), fg=TEXT, bg=WHITE).pack(side="left")
tk.Label(product_header, text=f"{len(products)} products loaded from products.csv",
         font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack(side="right")

search_row = tk.Frame(left, bg=WHITE)
search_row.pack(fill="x", padx=18, pady=(0, 8))
tk.Label(search_row, text="Search", font=("Segoe UI", 10, "bold"),
         fg=TEXT, bg=WHITE).pack(side="left", padx=(0, 8))
search_var = tk.StringVar()
search_var.trace_add("write", populate_products)
ttk.Entry(search_row, textvariable=search_var).pack(side="left", fill="x", expand=True)

product_frame = tk.Frame(left, bg=WHITE)
product_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

product_tree = ttk.Treeview(
    product_frame,
    columns=("ID", "Product", "Category", "Price", "Stock"),
    show="headings",
    selectmode="browse"
)
product_scroll = ttk.Scrollbar(product_frame, orient="vertical",
                               command=product_tree.yview)
product_tree.configure(yscrollcommand=product_scroll.set)

for col, width, anchor, stretch in [
    ("ID", 45, "center", False),
    ("Product", 330, "w", True),
    ("Category", 160, "w", False),
    ("Price", 100, "e", False),
    ("Stock", 60, "center", False),
]:
    product_tree.heading(col, text=col)
    product_tree.column(col, width=width, anchor=anchor, stretch=stretch)

product_tree.tag_configure("out", foreground="#9ca3af")
product_scroll.pack(side="right", fill="y")
product_tree.pack(side="left", fill="both", expand=True)
product_tree.bind("<<TreeviewSelect>>", product_selected)
populate_products()

add_box = tk.Frame(left, bg=LIGHT_BLUE,
                   highlightbackground="#bfdbfe", highlightthickness=1)
add_box.pack(fill="x", padx=16, pady=(0, 16))

tk.Label(add_box, text="Quantity", font=("Segoe UI", 10, "bold"),
         fg=TEXT, bg=LIGHT_BLUE).pack(side="left", padx=(14, 7), pady=11)

quantity_var = tk.StringVar(value="1")
ttk.Entry(add_box, textvariable=quantity_var, width=7).pack(
    side="left", padx=5, pady=8
)

tk.Button(
    add_box, text="＋  Add to Cart", command=add_to_cart,
    font=("Segoe UI", 10, "bold"), fg=WHITE, bg=BLUE,
    activebackground="#1d4ed8", activeforeground=WHITE,
    relief="flat", bd=0, padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=10, pady=7)

# -------------------- CART PANEL --------------------
cart_header = tk.Frame(right, bg=WHITE)
cart_header.pack(fill="x", padx=18, pady=(16, 8))

tk.Label(cart_header, text="Your Cart",
         font=("Segoe UI", 17, "bold"), fg=TEXT, bg=WHITE).pack(side="left")
tk.Label(cart_header, text="Review your selected items",
         font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack(side="right")

# Fixed height keeps Bill Summary and Checkout visible
cart_frame = tk.Frame(right, bg=WHITE, height=210)
cart_frame.pack(fill="x", padx=16)
cart_frame.pack_propagate(False)

cart_tree = ttk.Treeview(
    cart_frame,
    columns=("ID", "Product", "Qty", "Price", "Total"),
    show="headings",
    selectmode="browse"
)
cart_scroll = ttk.Scrollbar(cart_frame, orient="vertical", command=cart_tree.yview)
cart_tree.configure(yscrollcommand=cart_scroll.set)

for col, width, anchor, stretch in [
    ("ID", 38, "center", False),
    ("Product", 170, "w", True),
    ("Qty", 42, "center", False),
    ("Price", 90, "e", False),
    ("Total", 100, "e", False),
]:
    cart_tree.heading(col, text=col)
    cart_tree.column(col, width=width, anchor=anchor, stretch=stretch)

cart_scroll.pack(side="right", fill="y")
cart_tree.pack(side="left", fill="both", expand=True)
cart_tree.bind("<<TreeviewSelect>>", cart_selected)

cart_buttons = tk.Frame(right, bg=WHITE)
cart_buttons.pack(fill="x", padx=16, pady=7)


def small_button(text, command, bg):
    return tk.Button(
        cart_buttons, text=text, command=command,
        font=("Segoe UI", 9, "bold"), fg=WHITE, bg=bg,
        activebackground=bg, activeforeground=WHITE,
        relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
    )


small_button("Update", update_cart_quantity, BLUE).pack(side="left", padx=3)
small_button("Remove", remove_from_cart, RED).pack(side="left", padx=3)
small_button("Clear Cart", clear_cart, "#475569").pack(side="left", padx=3)

# -------------------- BILL SUMMARY --------------------
summary = tk.Frame(right, bg=SUMMARY_BG,
                   highlightbackground=BORDER, highlightthickness=1)
summary.pack(fill="x", padx=16, pady=(0, 8))

tk.Label(summary, text="Bill Summary",
         font=("Segoe UI", 12, "bold"), fg=TEXT, bg=SUMMARY_BG).pack(
             anchor="w", padx=14, pady=(9, 4)
         )

subtotal_var = tk.StringVar(value="₹0.00")
discount_var = tk.StringVar(value="₹0.00")
gst_var = tk.StringVar(value="₹0.00")
total_var = tk.StringVar(value="₹0.00")


def summary_row(label, variable, bold=False):
    row = tk.Frame(summary, bg=SUMMARY_BG)
    row.pack(fill="x", padx=14, pady=2)
    font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
    tk.Label(row, text=label, font=font, fg=TEXT, bg=SUMMARY_BG).pack(side="left")
    tk.Label(row, textvariable=variable, font=font, fg=TEXT, bg=SUMMARY_BG).pack(side="right")


summary_row("Subtotal", subtotal_var)
summary_row("Discount", discount_var)
summary_row("GST (18%)", gst_var)

tk.Frame(summary, height=1, bg=BORDER).pack(fill="x", padx=13, pady=5)
summary_row("FINAL TOTAL", total_var, bold=True)

# -------------------- CHECKOUT --------------------
tk.Button(
    right,
    text="CHECKOUT  &  GENERATE RECEIPT",
    command=checkout,
    font=("Segoe UI", 11, "bold"),
    fg=WHITE, bg=GREEN,
    activebackground="#166534", activeforeground=WHITE,
    relief="flat", bd=0, pady=9, cursor="hand2"
).pack(fill="x", padx=16, pady=(0, 14))

root.mainloop()

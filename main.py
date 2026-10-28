import csv
import json
import os
import shutil
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "canteen_data")
IMAGES_DIR = os.path.join(DATA_DIR, "item_images")
CSV_FILE = os.path.join(DATA_DIR, "canteen_sales.csv")
MENU_FILE = os.path.join(DATA_DIR, "menu_items.json")

os.makedirs(IMAGES_DIR, exist_ok=True)

DEFAULT_MENU = [
    {"name": "Vadapav", "price": 20, "category": "Snacks", "image_path": None},
    {"name": "Samosa", "price": 20, "category": "Snacks", "image_path": None},
    {"name": "Kachori", "price": 20, "category": "Snacks", "image_path": None},
    {"name": "Vada Bhaji", "price": 50, "category": "Snacks", "image_path": None},
    {"name": "Puri-Bhaji", "price": 50, "category": "Meals", "image_path": None},
    {"name": "Chapati Bhaji", "price": 50, "category": "Meals", "image_path": None},
    {"name": "Tea", "price": 15, "category": "Beverages", "image_path": None},
    {"name": "Coffee", "price": 20, "category": "Beverages", "image_path": None},
    {"name": "Black Tea", "price": 15, "category": "Beverages", "image_path": None},
    {"name": "Milk", "price": 10, "category": "Beverages", "image_path": None},
    {"name": "Water", "price": 20, "category": "Beverages", "image_path": None},
]


def load_menu():
    if not os.path.exists(MENU_FILE):
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_MENU, f, indent=2)
        return DEFAULT_MENU
    try:
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_MENU


def save_menu(menu_data):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(menu_data, f, indent=2)


if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Order_ID",
            "Timestamp",
            "Customer_Name",
            "Buyers_Count",
            "Items_Summary",
            "Total_Amount",
            "Payment_Mode"
        ])


class CanteenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Campus Canteen POS & Billing System")
        self.geometry("1220x760")
        self.minsize(1080, 690)

        self.menu_items = load_menu()
        self.cart = {}
        self.selected_category = "All"
        self.search_query = ""

        self.title_click_times = []
        self.image_cache = {}

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_menu_panel()
        self._build_cart_panel()
        self._render_menu_items()

    def _on_title_click(self, event=None):
        now = time.time()
        self.title_click_times.append(now)
        self.title_click_times = [t for t in self.title_click_times if now - t <= 1.5]

        if len(self.title_click_times) >= 3:
            self.title_click_times.clear()
            self._open_admin_panel()

    def _build_menu_panel(self):
        menu_frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#181a20")
        menu_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)
        menu_frame.grid_rowconfigure(2, weight=1)
        menu_frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(menu_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        top_bar.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(
            top_bar,
            text="Campus Canteen Express",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color="#F8FAFC",
            cursor="hand2"
        )
        self.title_lbl.grid(row=0, column=0, sticky="w")
        self.title_lbl.bind("<Button-1>", self._on_title_click)

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Search items...",
            width=220,
            height=34,
            corner_radius=17,
            fg_color="#242731",
            border_width=1,
            border_color="#383d4c"
        )
        self.search_entry.grid(row=0, column=1, sticky="e")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        cat_bar = ctk.CTkFrame(menu_frame, fg_color="transparent")
        cat_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        categories = ["All", "Snacks", "Meals", "Beverages"]
        self.cat_buttons = {}
        for cat in categories:
            btn = ctk.CTkButton(
                cat_bar,
                text=cat,
                width=85,
                height=30,
                corner_radius=15,
                fg_color="#2563EB" if cat == "All" else "#242731",
                hover_color="#1D4ED8",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda c=cat: self._filter_category(c)
            )
            btn.pack(side="left", padx=(0, 8))
            self.cat_buttons[cat] = btn

        self.menu_scroll = ctk.CTkScrollableFrame(
            menu_frame,
            fg_color="transparent",
            scrollbar_button_color="#333846",
            scrollbar_button_hover_color="#454b5e"
        )
        self.menu_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.menu_scroll.grid_columnconfigure((0, 1, 2), weight=1)

    def _get_image_for_item(self, item):
        path = item.get("image_path")
        if path and os.path.exists(path):
            if path in self.image_cache:
                return self.image_cache[path]
            try:
                pil_img = Image.open(path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 90))
                self.image_cache[path] = ctk_img
                return ctk_img
            except Exception:
                pass
        return None

    def _render_menu_items(self):
        for widget in self.menu_scroll.winfo_children():
            widget.destroy()

        filtered_items = [
            item for item in self.menu_items
            if (self.selected_category == "All" or item["category"] == self.selected_category)
            and (self.search_query.lower() in item["name"].lower())
        ]

        row, col, cols_limit = 0, 0, 3
        for item in filtered_items:
            card = ctk.CTkFrame(
                self.menu_scroll,
                corner_radius=14,
                fg_color="#20232c",
                border_width=1,
                border_color="#2c303c"
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            img_obj = self._get_image_for_item(item)
            if img_obj:
                img_lbl = ctk.CTkLabel(card, text="", image=img_obj)
                img_lbl.pack(pady=(12, 4))
                name_top_pad = 2
            else:
                name_top_pad = 16

            ctk.CTkLabel(
                card,
                text=item["name"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F1F5F9"
            ).pack(pady=(name_top_pad, 0))

            ctk.CTkLabel(
                card,
                text=f"₹{item['price']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#38BDF8"
            ).pack(pady=(2, 8))

            ctk.CTkButton(
                card,
                text="+ Add to Order",
                height=30,
                corner_radius=8,
                fg_color="#10B981",
                hover_color="#059669",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda it=item: self._add_to_cart(it)
            ).pack(padx=14, pady=(0, 14), fill="x")

            col += 1
            if col >= cols_limit:
                col = 0
                row += 1

    def _build_cart_panel(self):
        cart_frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#181a20")
        cart_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)
        cart_frame.grid_rowconfigure(2, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(cart_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(15, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Live Order", font=ctk.CTkFont(size=20, weight="bold"), text_color="#F8FAFC").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            header,
            text="Clear",
            width=60,
            height=26,
            corner_radius=6,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._clear_cart
        ).grid(row=0, column=1, sticky="e")

        details_box = ctk.CTkFrame(cart_frame, fg_color="#20232c", corner_radius=12)
        details_box.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        self.cust_name_entry = ctk.CTkEntry(
            details_box,
            placeholder_text="Customer Name (Optional)",
            height=32,
            corner_radius=8,
            fg_color="#181a20",
            border_color="#303544"
        )
        self.cust_name_entry.pack(fill="x", padx=10, pady=(10, 5))

        self.buyers_count_entry = ctk.CTkEntry(
            details_box,
            placeholder_text="No. of Buyers / Tokens (Optional, e.g. 1, 3)",
            height=32,
            corner_radius=8,
            fg_color="#181a20",
            border_color="#303544"
        )
        self.buyers_count_entry.pack(fill="x", padx=10, pady=(0, 6))

        pay_row = ctk.CTkFrame(details_box, fg_color="transparent")
        pay_row.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(pay_row, text="Mode:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(side="left", padx=(0, 6))
        self.payment_mode = ctk.CTkSegmentedButton(pay_row, values=["UPI / QR", "Cash"], selected_color="#2563EB", height=26)
        self.payment_mode.set("UPI / QR")
        self.payment_mode.pack(side="left", fill="x", expand=True)

        self.cart_scroll = ctk.CTkScrollableFrame(cart_frame, fg_color="transparent")
        self.cart_scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=4)
        self.cart_scroll.grid_columnconfigure(0, weight=1)

        checkout_box = ctk.CTkFrame(cart_frame, fg_color="#20232c", corner_radius=12)
        checkout_box.grid(row=3, column=0, sticky="ew", padx=16, pady=16)

        total_row = ctk.CTkFrame(checkout_box, fg_color="transparent")
        total_row.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(total_row, text="Total Amount", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.total_lbl = ctk.CTkLabel(total_row, text="₹0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#10B981")
        self.total_lbl.pack(side="right")

        ctk.CTkButton(
            checkout_box,
            text="Confirm & Record Sale",
            height=40,
            corner_radius=10,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._process_checkout
        ).pack(fill="x", padx=14, pady=(4, 12))

        self._render_cart()

    def _add_to_cart(self, item):
        name = item["name"]
        price = item["price"]
        if name in self.cart:
            self.cart[name]["qty"] += 1
        else:
            self.cart[name] = {"price": price, "qty": 1}
        self._render_cart()

    def _update_cart_qty(self, name, delta):
        if name in self.cart:
            self.cart[name]["qty"] += delta
            if self.cart[name]["qty"] <= 0:
                del self.cart[name]
            self._render_cart()

    def _render_cart(self):
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()

        if not self.cart:
            ctk.CTkLabel(
                self.cart_scroll,
                text="Order is empty\nTap items on the left to add",
                font=ctk.CTkFont(size=13),
                text_color="#64748B"
            ).pack(pady=40)
            self.total_lbl.configure(text="₹0")
            return

        grand_total = 0
        for name, data in self.cart.items():
            subtotal = data["price"] * data["qty"]
            grand_total += subtotal

            row = ctk.CTkFrame(self.cart_scroll, fg_color="#1f222b", corner_radius=8)
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w", padx=10, pady=6)
            ctk.CTkLabel(info, text=name, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=f"₹{data['price']} × {data['qty']} = ₹{subtotal}", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")

            stepper = ctk.CTkFrame(row, fg_color="transparent")
            stepper.grid(row=0, column=1, sticky="e", padx=8, pady=6)

            ctk.CTkButton(stepper, text="-", width=24, height=24, corner_radius=5, fg_color="#333846", hover_color="#474e61", command=lambda n=name: self._update_cart_qty(n, -1)).pack(side="left", padx=2)
            ctk.CTkLabel(stepper, text=str(data["qty"]), width=20, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
            ctk.CTkButton(stepper, text="+", width=24, height=24, corner_radius=5, fg_color="#333846", hover_color="#474e61", command=lambda n=name: self._update_cart_qty(n, 1)).pack(side="left", padx=2)

        self.total_lbl.configure(text=f"₹{grand_total}")

    def _clear_cart(self):
        self.cart.clear()
        self._render_cart()

    def _filter_category(self, cat):
        self.selected_category = cat
        for c, btn in self.cat_buttons.items():
            btn.configure(fg_color="#2563EB" if c == cat else "#242731")
        self._render_menu_items()

    def _on_search(self, event=None):
        self.search_query = self.search_entry.get().strip()
        self._render_menu_items()

    def _process_checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Order", "Please select items first.")
            return

        order_id = "ORD-" + datetime.now().strftime("%y%m%d-%H%M%S")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cust_name = self.cust_name_entry.get().strip() or "Guest Student"
        buyers_count = self.buyers_count_entry.get().strip() or "1"
        payment = self.payment_mode.get()
        total_amount = sum(d["price"] * d["qty"] for d in self.cart.values())
        summary = "; ".join([f"{name} x {d['qty']}" for name, d in self.cart.items()])

        try:
            with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([order_id, timestamp, cust_name, buyers_count, summary, total_amount, payment])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record sale: {e}")
            return

        messagebox.showinfo("Order Saved", f"Order {order_id} recorded successfully!\nTotal: ₹{total_amount}\nBuyers/Tokens: {buyers_count}")
        self.cart.clear()
        self.cust_name_entry.delete(0, tk.END)
        self.buyers_count_entry.delete(0, tk.END)
        self._render_cart()

    def _open_admin_panel(self):
        AdminWindow(self)


class AdminWindow(ctk.CTkToplevel):
    def __init__(self, parent: CanteenApp):
        super().__init__(parent)
        self.parent = parent
        self.title("Canteen Admin Dashboard")
        self.geometry("860x600")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=0)
        top.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        ctk.CTkLabel(top, text="Admin Control Panel", font=ctk.CTkFont(size=18, weight="bold"), text_color="#38BDF8").pack(side="left", padx=20, pady=12)

        tabview = ctk.CTkTabview(self)
        tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        tabview.add("Manage & Edit Menu")
        tabview.add("Sales Analytics")

        self._setup_manage_tab(tabview.tab("Manage & Edit Menu"))
        self._setup_analytics_tab(tabview.tab("Sales Analytics"))

    def _setup_manage_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        add_bar = ctk.CTkFrame(tab, fg_color="#20232c", corner_radius=10)
        add_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        self.new_name = ctk.CTkEntry(add_bar, placeholder_text="Item Name", width=140)
        self.new_name.pack(side="left", padx=6, pady=8)

        self.new_price = ctk.CTkEntry(add_bar, placeholder_text="Price (₹)", width=80)
        self.new_price.pack(side="left", padx=6, pady=8)

        self.new_cat = ctk.CTkComboBox(add_bar, values=["Snacks", "Meals", "Beverages"], width=110)
        self.new_cat.pack(side="left", padx=6, pady=8)

        ctk.CTkButton(
            add_bar,
            text="+ Add New Dish",
            fg_color="#10B981",
            hover_color="#059669",
            command=self._add_new_item
        ).pack(side="left", padx=8, pady=8)

        self.items_list_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.items_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.items_list_frame.grid_columnconfigure(0, weight=1)

        self._render_admin_items()

    def _render_admin_items(self):
        for widget in self.items_list_frame.winfo_children():
            widget.destroy()

        for idx, item in enumerate(self.parent.menu_items):
            row = ctk.CTkFrame(self.items_list_frame, fg_color="#20232c", corner_radius=8)
            row.pack(fill="x", pady=4)

            name_entry = ctk.CTkEntry(row, width=150, height=28)
            name_entry.insert(0, item["name"])
            name_entry.pack(side="left", padx=(10, 5), pady=8)

            price_entry = ctk.CTkEntry(row, width=70, height=28)
            price_entry.insert(0, str(item["price"]))
            price_entry.pack(side="left", padx=5, pady=8)

            cat_combo = ctk.CTkComboBox(row, values=["Snacks", "Meals", "Beverages"], width=110, height=28)
            cat_combo.set(item.get("category", "Snacks"))
            cat_combo.pack(side="left", padx=5, pady=8)

            ctk.CTkButton(
                row,
                text="Save",
                width=55,
                height=28,
                fg_color="#10B981",
                hover_color="#059669",
                command=lambda i=idx, ne=name_entry, pe=price_entry, ce=cat_combo: self._save_item_edits(i, ne, pe, ce)
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                row,
                text="Upload Photo",
                width=100,
                height=28,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                command=lambda i=idx: self._upload_photo_for_item(i)
            ).pack(side="left", padx=5)

            if item.get("image_path") and os.path.exists(item["image_path"]):
                ctk.CTkButton(
                    row,
                    text="Del Photo",
                    width=75,
                    height=28,
                    fg_color="#D97706",
                    hover_color="#B45309",
                    command=lambda i=idx: self._remove_photo_for_item(i)
                ).pack(side="left", padx=4)

            ctk.CTkButton(
                row,
                text="Delete",
                width=60,
                height=28,
                fg_color="#EF4444",
                hover_color="#DC2626",
                command=lambda i=idx: self._delete_item(i)
            ).pack(side="right", padx=(5, 10))

    def _save_item_edits(self, idx, name_entry, price_entry, cat_combo):
        new_name = name_entry.get().strip()
        new_price_str = price_entry.get().strip()
        new_cat = cat_combo.get().strip()

        if not new_name or not new_price_str:
            messagebox.showwarning("Invalid Input", "Name and price cannot be empty.")
            return

        try:
            new_price = int(new_price_str)
        except ValueError:
            messagebox.showwarning("Invalid Price", "Price must be a valid whole number.")
            return

        old_name = self.parent.menu_items[idx]["name"]
        self.parent.menu_items[idx]["name"] = new_name
        self.parent.menu_items[idx]["price"] = new_price
        self.parent.menu_items[idx]["category"] = new_cat

        if old_name in self.parent.cart:
            qty = self.parent.cart[old_name]["qty"]
            del self.parent.cart[old_name]
            self.parent.cart[new_name] = {"price": new_price, "qty": qty}
            self.parent._render_cart()

        save_menu(self.parent.menu_items)
        self.parent._render_menu_items()
        messagebox.showinfo("Saved", f"'{new_name}' updated successfully!")

    def _upload_photo_for_item(self, idx):
        file_path = filedialog.askopenfilename(
            title="Select Dish Photo",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        if not file_path:
            return

        item = self.parent.menu_items[idx]
        ext = os.path.splitext(file_path)[1]
        safe_name = item["name"].lower().replace(" ", "_").replace("-", "_") + ext
        destination = os.path.join(IMAGES_DIR, safe_name)

        try:
            shutil.copyfile(file_path, destination)
            item["image_path"] = destination

            if destination in self.parent.image_cache:
                del self.parent.image_cache[destination]

            save_menu(self.parent.menu_items)
            self._render_admin_items()
            self.parent._render_menu_items()
            messagebox.showinfo("Success", f"Photo updated for {item['name']}!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload image: {e}")

    def _remove_photo_for_item(self, idx):
        item = self.parent.menu_items[idx]
        item["image_path"] = None
        save_menu(self.parent.menu_items)
        self._render_admin_items()
        self.parent._render_menu_items()
        messagebox.showinfo("Photo Removed", f"Photo removed for {item['name']}.")

    def _add_new_item(self):
        name = self.new_name.get().strip()
        price_str = self.new_price.get().strip()
        cat = self.new_cat.get()

        if not name or not price_str:
            messagebox.showwarning("Incomplete", "Please enter item name and price.")
            return

        try:
            price = int(price_str)
        except ValueError:
            messagebox.showwarning("Invalid Price", "Price must be a valid whole number.")
            return

        self.parent.menu_items.append({
            "name": name,
            "price": price,
            "category": cat,
            "image_path": None
        })
        save_menu(self.parent.menu_items)

        self.new_name.delete(0, tk.END)
        self.new_price.delete(0, tk.END)
        self._render_admin_items()
        self.parent._render_menu_items()

    def _delete_item(self, idx):
        item = self.parent.menu_items[idx]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item['name']}'?"):
            del self.parent.menu_items[idx]
            save_menu(self.parent.menu_items)
            self._render_admin_items()
            self.parent._render_menu_items()

    def _setup_analytics_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        total_rev = 0
        order_count = 0

        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row and len(row) >= 6:
                        try:
                            total_rev += float(row[5])
                            order_count += 1
                        except ValueError:
                            pass

        stats_frame = ctk.CTkFrame(tab, fg_color="#20232c", corner_radius=10)
        stats_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(stats_frame, text=f"Total Lifetime Orders:  {order_count}", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(12, 4))
        ctk.CTkLabel(stats_frame, text=f"Total Revenue Generated:  ₹{int(total_rev)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#10B981").pack(anchor="w", padx=15, pady=(0, 12))

        path_lbl = ctk.CTkLabel(
            tab,
            text=f"CSV Database Location:\n{CSV_FILE}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        )
        path_lbl.pack(anchor="w", padx=15, pady=10)


if __name__ == "__main__":
    app = CanteenApp()
    app.mainloop()

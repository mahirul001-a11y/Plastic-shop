from datetime import datetime
import sqlite3
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

# ব্যাকগ্রাউন্ড কালার
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class PlasticShopApp(App):

    def build(self):
        self.title = "Plastic Shop - Smart Dues Tracker"

        # ডাটাবেস সেটআপ
        self.conn = sqlite3.connect("mobile_plastic_shop_v4.db")
        self.cursor = self.conn.cursor()

        # কাস্টমার টেবিল
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                phone TEXT
            )
        """
        )

        # লেনদেন টেবিল
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cust_name TEXT,
                items TEXT,
                rate REAL,
                qty REAL,
                bill REAL,
                paid REAL,
                due REAL,
                date_str TEXT
            )
        """
        )
        self.conn.commit()

        # প্রধান লেআউট
        main_layout = BoxLayout(
            orientation="vertical", padding=12, spacing=6
        )

        # শিরোনাম
        header = Label(
            text="PLASTIC SHOP - DUES TRACKER",
            font_size="16sp",
            bold=True,
            color=(0.1, 0.4, 0.8, 1),
            size_hint_y=None,
            height=30,
        )
        main_layout.add_widget(header)

        # --- ১ম অংশ: নতুন কাস্টমার যোগ ---
        cust_box = BoxLayout(
            orientation="horizontal", spacing=5, size_hint_y=None, height=38
        )
        self.input_new_name = TextInput(
            hint_text="New Cust Name", multiline=False
        )
        self.input_new_phone = TextInput(
            hint_text="Mobile No", multiline=False
        )
        btn_add_cust = Button(
            text="+ Add Cust",
            background_color=(0.2, 0.6, 0.8, 1),
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_x=0.8,
        )
        btn_add_cust.bind(on_press=self.add_customer)

        cust_box.add_widget(self.input_new_name)
        cust_box.add_widget(self.input_new_phone)
        cust_box.add_widget(btn_add_cust)
        main_layout.add_widget(cust_box)

        # --- ২য় অংশ: কাস্টমার সিলেকশন (ড্রপডাউন) ---
        self.customer_spinner = Spinner(
            text="Select Customer",
            values=[],
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.3, 0.5, 1),
            color=(1, 1, 1, 1),
        )
        # ড্রপডাউনে কাস্টমার পরিবর্তন হলেই ফিল্টার হবে
        self.customer_spinner.bind(text=self.on_customer_change)
        main_layout.add_widget(self.customer_spinner)

        # ইনপুট ফিল্ডসমূহ
        self.input_items = TextInput(
            hint_text="Item Name (e.g. Chair/Bucket)",
            multiline=False,
            size_hint_y=None,
            height=38,
        )
        self.input_rate = TextInput(
            hint_text="Item Rate (Tk)",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=38,
        )
        self.input_qty = TextInput(
            hint_text="Item Quantity (Poriman)",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=38,
        )
        self.input_paid = TextInput(
            hint_text="Paid Amount (Joma)",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=38,
        )

        main_layout.add_widget(self.input_items)
        main_layout.add_widget(self.input_rate)
        main_layout.add_widget(self.input_qty)
        main_layout.add_widget(self.input_paid)

        # সেভ বাটন
        btn_save = Button(
            text="SAVE TRANSACTION",
            background_color=(0.16, 0.65, 0.27, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=40,
            bold=True,
        )
        btn_save.bind(on_press=self.save_transaction)
        main_layout.add_widget(btn_save)

        # স্ট্যাটাস মেসেজ
        self.msg_label = Label(
            text="",
            color=(0.8, 0, 0, 1),
            size_hint_y=None,
            height=20,
            font_size="12sp",
        )
        main_layout.add_widget(self.msg_label)

        # --- ৩য় অংশ: নির্বাচন করা কাস্টমারের সর্বমোট হিসাব (Summary) ---
        self.summary_label = Label(
            text="Total Bill: 0 Tk | Paid: 0 Tk | TOTAL DUE: 0 Tk",
            font_size="13sp",
            bold=True,
            color=(0.8, 0.2, 0.1, 1),
            size_hint_y=None,
            height=25,
        )
        main_layout.add_widget(self.summary_label)

        # তালিকা
        self.scroll_view = ScrollView()
        self.list_layout = BoxLayout(
            orientation="vertical", spacing=6, size_hint_y=None
        )
        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )
        self.scroll_view.add_widget(self.list_layout)

        main_layout.add_widget(self.scroll_view)

        # প্রাথমিক ডাটা লোড
        self.update_spinner_list()

        return main_layout

    # নতুন কাস্টমার যোগ
    def add_customer(self, instance):
        name = self.input_new_name.text.strip().lower()
        phone = self.input_new_phone.text.strip()

        if not name:
            self.msg_label.text = "Error: Enter customer name first!"
            return

        try:
            self.cursor.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)",
                (name, phone),
            )
            self.conn.commit()
            self.input_new_name.text = ""
            self.input_new_phone.text = ""
            self.msg_label.text = f"Customer '{name}' added!"
            self.update_spinner_list()
            self.customer_spinner.text = name
        except sqlite3.IntegrityError:
            self.msg_label.text = "Error: Customer already exists!"

    # ড্রপডাউন তালিকা আপডেট
    def update_spinner_list(self):
        self.cursor.execute("SELECT name FROM customers")
        rows = self.cursor.fetchall()
        names = [r[0] for r in rows]
        if names:
            self.customer_spinner.values = names
            if self.customer_spinner.text not in names:
                self.customer_spinner.text = names[0]
        else:
            self.customer_spinner.values = []
            self.customer_spinner.text = "No Customer"

    # কাস্টমার নির্বাচন বদলালে এই ফাংশনটি চলবে
    def on_customer_change(self, spinner, text):
        self.load_customer_transactions(text)

    # লেনদেন সেভ করা
    def save_transaction(self, instance):
        selected_cust = self.customer_spinner.text
        if selected_cust in ["Select Customer", "No Customer"]:
            self.msg_label.text = "Error: Select a valid customer!"
            return

        items = self.input_items.text.strip()
        try:
            rate = float(self.input_rate.text or 0)
            qty = float(self.input_qty.text or 0)
            paid = float(self.input_paid.text or 0)
        except ValueError:
            self.msg_label.text = "Error: Rate, Qty & Paid must be numbers!"
            return

        bill = rate * qty
        due = bill - paid
        today_date = datetime.now().strftime("%d-%b-%Y %I:%M %p")

        self.cursor.execute(
            """
            INSERT INTO transactions (cust_name, items, rate, qty, bill, paid, due, date_str)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (selected_cust, items, rate, qty, bill, paid, due, today_date),
        )
        self.conn.commit()

        # ঘর খালি করা
        self.input_items.text = ""
        self.input_rate.text = ""
        self.input_qty.text = ""
        self.input_paid.text = ""

        self.msg_label.text = f"Saved for {selected_cust}!"
        self.load_customer_transactions(selected_cust)

    # নির্দিষ্ট কাস্টমারের লেনদেন ফিল্টার ও মোট হিসাব তৈরি
    def load_customer_transactions(self, cust_name):
        self.list_layout.clear_widgets()

        if cust_name in ["Select Customer", "No Customer"]:
            self.summary_label.text = "No Customer Selected"
            return

        # নির্বাচিত কাস্টমারের রেকর্ডসমূহ আনা
        self.cursor.execute(
            "SELECT * FROM transactions WHERE cust_name = ? ORDER BY id DESC",
            (cust_name,),
        )
        rows = self.cursor.fetchall()

        total_bill = 0
        total_paid = 0
        total_due = 0

        for row in rows:
            # row: [id, cust_name, items, rate, qty, bill, paid, due, date_str]
            total_bill += row[5]
            total_paid += row[6]
            total_due += row[7]

            text_info = f"Date: {row[8]}\nItem: {row[2]} ({row[4]} pcs x {row[3]} Tk)\nBill: {row[5]} Tk | Paid: {row[6]} Tk | Due: {row[7]} Tk"
            card = Button(
                text=text_info,
                size_hint_y=None,
                height=70,
                background_color=(0.9, 0.9, 0.95, 1),
                color=(0, 0, 0, 1),
                font_size="11sp",
            )
            self.list_layout.add_widget(card)

        # কাস্টমারের জন্য মোট যোগফল দেখাবে
        self.summary_label.text = f"[{cust_name.upper()}] Bill: {total_bill}Tk | Paid: {total_paid}Tk | DUE: {total_due}Tk"


if __name__ == "__main__":
    PlasticShopApp().run()

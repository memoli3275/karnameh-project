from flask import Flask, render_template, request, send_from_directory
import fitz  # PyMuPDF
import os
import json
import threading

app = Flask(__name__)

# ⛔ بارگذاری لیست کدهای ثبت‌نام‌نشده
with open("unauthorized.json", "r", encoding="utf-8") as f:
    unauthorized_codes = json.load(f)

# 📄 استخراج فقط یک صفحه خاص از فایل اصلی
def extract_single_page(source_path, target_path, page_number):
    doc = fitz.open(source_path)
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_number - 1, to_page=page_number - 1)
    new_doc.save(target_path)
    new_doc.close()
    doc.close()

# 🔍 پیدا کردن صفحه‌ای که شامل کد ملی هست
def find_page_by_code(pdf_path, code):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if code in text:
            return page_num + 1  # شماره صفحه از 1 شروع بشه
    return None

# 🧹 پاک کردن فایل موقتی بعد از ارسال
def delete_file_later(path, delay=15):
    def task():
        import time
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=task).start()

# 🎯 نقطه ورود اصلی سایت
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        code = request.form["access_code"].strip()
        source_pdf = os.path.join("files", "documents.pdf")

        # ⛔ بررسی ثبت‌نام‌نشده‌ها
        if code in unauthorized_codes:
            error = "دانش آموزعزیز به دلیل عدم ثبت نام قادر به دیدن کارنامه خود نمی باشید  ."
            return render_template("index.html", error=error)

        page_number = find_page_by_code(source_pdf, code)

        if page_number:
            output_pdf = os.path.join("files", f"{code}.pdf")
            extract_single_page(source_pdf, output_pdf, page_number)
            delete_file_later(output_pdf)  # پاک‌سازی بعد از ۱۵ ثانیه
            return send_from_directory("files", f"{code}.pdf", as_attachment=True)
        else:
            error = "کد ملی شما در فایل یافت نشد 😔"
    return render_template("index.html", error=error)

# 🔧 اجرای برنامه
if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0",post=10000)

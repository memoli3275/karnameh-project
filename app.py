from flask import Flask, render_template, request, send_from_directory
import fitz  # PyMuPDF برای کار با PDF
import os
import json
import threading

app = Flask(__name__)

# ⛔ بارگذاری لیست کدهای ثبت‌نام‌نشده از فایل JSON
with open("unauthorized.json", "r", encoding="utf-8") as f:
    unauthorized_codes = json.load(f)

# 📄 استخراج فقط یک صفحه از فایل PDF
def extract_single_page(source_path, target_path, page_number):
    doc = fitz.open(source_path)
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_number - 1, to_page=page_number - 1)
    new_doc.save(target_path)
    new_doc.close()
    doc.close()

# 🔍 جستجوی شماره صفحه‌ای که شامل کد ملی باشد
def find_page_by_code(pdf_path, code):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if code in text:
            return page_num + 1
    return None

# 🧹 حذف خودکار فایل PDF بعد از چند ثانیه
def delete_file_later(path, delay=15):
    def task():
        import time
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=task).start()

# 🎯 مسیر اصلی سایت - کنترل فرم و ارسال فایل
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        code = request.form["access_code"].strip()
        source_pdf = os.path.join("files", "documents.pdf")

        # ⛔ اگر دانش‌آموز ثبت‌نام نشده باشد
        if code in unauthorized_codes:
            error = "دانش آموز عزیز، به دلیل عدم ثبت‌نام قادر به دریافت کارنامه نمی‌باشید."
            return render_template("index.html", error=error, code="")

        # 🔎 بررسی وجود کد در PDF
        page_number = find_page_by_code(source_pdf, code)

        if page_number:
            output_pdf = os.path.join("files", f"{code}.pdf")
            extract_single_page(source_pdf, output_pdf, page_number)
            delete_file_later(output_pdf)
            return send_from_directory("files", f"{code}.pdf", as_attachment=True)
        else:
            error = "کد ملی شما در فایل یافت نشد 😔"
            return render_template("index.html", error=error, code="")

    # بارگذاری اولیه صفحه بدون خطا و مقدار کد
    return render_template("index.html", code="")

# 🔧 اجرای برنامه در محیط توسعه یا استقرار
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

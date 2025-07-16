from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import fitz  # کتابخانه PyMuPDF
import os
import json
import threading

app = Flask(__name__)

# بارگذاری لیست دانش‌آموزان ثبت‌نام‌نشده
with open("unauthorized.json", "r", encoding="utf-8") as f:
    unauthorized_codes = json.load(f)

# استخراج یک صفحه خاص از فایل PDF
def extract_single_page(source_path, target_path, page_number):
    doc = fitz.open(source_path)
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_number - 1, to_page=page_number - 1)
    new_doc.save(target_path)
    new_doc.close()
    doc.close()

# یافتن شماره صفحه‌ای که شامل کد ملی باشد
def find_page_by_code(pdf_path, code):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        if code in doc[page_num].get_text():
            return page_num + 1
    return None

# حذف فایل موقت بعد از ۱۵ ثانیه
def delete_file_later(path, delay=15):
    def task():
        import time
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=task).start()

# مسیر اصلی برای نمایش فرم
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", code="", error="")

# مسیر بررسی کد و استخراج کارنامه
@app.route("/get", methods=["POST"])
def get_pdf():
    code = request.form["access_code"].strip().replace("‌", "").replace(" ", "")
    source_pdf = os.path.join("files", "documents.pdf")

    if code in unauthorized_codes:
        error = "دانش‌آموز عزیز، به دلیل عدم ثبت‌نام قادر به دریافت کارنامه نمی‌باشید."
        return render_template("index.html", error=error, code=code)

    page_number = find_page_by_code(source_pdf, code)

    if page_number:
        output_pdf = os.path.join("files", f"{code}.pdf")
        extract_single_page(source_pdf, output_pdf, page_number)
        delete_file_later(output_pdf)
        return redirect(url_for("success", filename=f"{code}.pdf"))
    else:
        error = "کد ملی شما در فایل یافت نشد 😔"
        return render_template("index.html", error=error, code=code)

# مسیر نمایش پیام موفقیت و لینک دانلود فایل
@app.route("/success")
def success():
    filename = request.args.get("filename")
    return render_template("success.html", filename=filename)

# مسیر ارسال فایل PDF برای دانلود
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("files", filename, as_attachment=True)

# اجرای برنامه روی پورت 10000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

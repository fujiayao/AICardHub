"""Create a synthetic workbook with one valid and one invalid row; no secrets printed."""
import secrets
import string
import time
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1] / ".local"
root.mkdir(exist_ok=True)
password = "Aa9" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
rows = [["姓名", "手机号", "初始密码", "部门", "职位"],
        ["合成Excel验收" + str(time.time_ns()), "139" + str(time.time_ns())[-8:], password, "合成导入测试", "演示"],
        ["无效合成行", "invalid", password, "合成导入测试", "演示"]]
content = "".join('<row r="%s">%s</row>' % (i, "".join('<c t="inlineStr"><is><t>%s</t></is></c>' % escape(v) for v in row)) for i, row in enumerate(rows, 1))
with ZipFile(root / "synthetic-employees.xlsx", "w") as workbook:
    workbook.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    workbook.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    workbook.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Synthetic" sheetId="1" r:id="rId1"/></sheets></workbook>')
    workbook.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
    workbook.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + content + '</sheetData></worksheet>')

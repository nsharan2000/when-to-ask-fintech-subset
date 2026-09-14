"""Inject experiments/figures/report_data.json into report/guide_template.html → report/askbc-guide.html"""
import json, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
data = json.load(open(os.path.join(root, "experiments/figures/report_data.json")))
tpl = open(os.path.join(here, "guide_template.html")).read()
html = tpl.replace("/*__REPORT_DATA__*/", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open(os.path.join(here, "askbc-guide.html"), "w").write(html)
print("built", len(html), "bytes; models:", list(data["models"]))

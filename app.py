"""A simple web page for your chatbot. No installs needed.

Run:  python app.py      then open  http://localhost:8000  in your browser.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from chatbot import answer

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Cybersecurity Book Chatbot</title>
<style>body{font-family:Arial,sans-serif;max-width:820px;margin:30px auto;padding:0 16px}
input{width:75%;padding:10px;font-size:16px}button{padding:10px 18px;font-size:16px}
#out{white-space:pre-wrap;background:#f4f6f8;padding:14px;margin-top:16px;border-radius:6px}
.src{margin-top:10px;font-size:14px;color:#235}</style></head><body>
<h2>Cybersecurity Book Chatbot</h2><p>Answers come only from the 15 books, with citations.</p>
<input id="q" placeholder="Ask a cybersecurity question..."><button onclick="ask()">Ask</button>
<div id="out"></div><div class="src" id="src"></div>
<script>
async function ask(){
 const q=document.getElementById('q').value; if(!q) return;
 document.getElementById('out').textContent='Searching...'; document.getElementById('src').textContent='';
 const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
 const d=await r.json();
 document.getElementById('out').textContent=d.answer;
 document.getElementById('src').textContent=d.insufficient_evidence?'Insufficient evidence: no sources shown.':
   'Sources: '+d.sources.map(s=>s.book_id+' p.'+s.page+' ('+s.chunk_id+')').join('; ');
}
document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter')ask()});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGE.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        question = json.loads(self.rfile.read(length) or b"{}").get("question", "")
        body = json.dumps(answer(question)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Chatbot page running at http://localhost:8000  (press Ctrl+C to stop)")
    HTTPServer(("localhost", 8000), Handler).serve_forever()

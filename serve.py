#!/usr/bin/env python3
import http.server
import os
import posixpath
import urllib.parse
import mimetypes
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NEXT_DIR = BASE_DIR / "_next"

class NextStaticRewriteHandler(http.server.SimpleHTTPRequestHandler):
	# Serve files relative to the project directory
	def translate_path(self, path: str) -> str:
		# Default resolution for static assets (css/js/fonts) and direct file hits
		path = path.split("?", 1)[0]
		path = path.split("#", 1)[0]
		trailing_slash = path.endswith("/")
		path = posixpath.normpath(urllib.parse.unquote(path))
		words = path.strip("/").split("/") if path != "/" else []
		resolved = BASE_DIR
		for word in words:
			if not word:
				continue
			# don't allow going up the tree
			word = word.replace(":", "").replace("\\", "")
			resolved = resolved / word
			if resolved.is_dir():
				continue
		# directory default files
		if trailing_slash and (resolved / "index.html").exists():
			return str(resolved / "index.html")
		return str(resolved)

	def _serve_next_image_candidate(self, raw_query: str) -> bool:
		"""Try to serve exported Next image file based on a raw query string.
		Returns True if served, False to continue normal handling.
		"""
		# Clean up known export artifacts
		clean = raw_query
		# Decode percent-encoding once
		clean = urllib.parse.unquote(clean)
		# Some builds include html-escaped ampersands and concatenated srcset fragments
		# Keep only the first query segment before any concatenated 'amp;q_next/image%3F'
		if "amp;q_next/image%3F" in clean:
			clean = clean.split("amp;q_next/image%3F", 1)[0]
		# Replace html-escaped ampersands
		clean = clean.replace("amp;", "&")
		# Remove any stray suffix like 'p;w=...' from corrupted tokens
		clean = clean.replace("p;w=", "&w=")
		params = urllib.parse.parse_qs(clean, keep_blank_values=True)
		if not params:
			return False

		def encode_params(p: dict) -> str:
			return urllib.parse.urlencode([(k, v[0]) for k, v in p.items() if v])

		# Try original query
		candidate = NEXT_DIR / ("image?" + encode_params(params))
		if candidate.exists():
			url_vals = params.get("url", [])
			ctype = "application/octet-stream"
			if url_vals:
				url_path = url_vals[0]
				if url_path.endswith(".png"):
					ctype = "image/png"
				elif url_path.endswith(".jpg") or url_path.endswith(".jpeg"):
					ctype = "image/jpeg"
				elif url_path.endswith(".webp"):
					ctype = "image/webp"
				elif url_path.endswith(".gif"):
					ctype = "image/gif"
			self.send_response(200)
			self.send_header("Content-Type", ctype)
			self.send_header("Cache-Control", "public, max-age=31536000, immutable")
			self.end_headers()
			with open(candidate, "rb") as f:
				self.wfile.write(f.read())
			return True

		# If not found, try substituting /full/ with /color/ and /mono/ inside the url param
		url_vals = params.get("url", [])
		if url_vals and url_vals[0].startswith("/full/"):
			for variant in ("/color/", "/mono/"):
				alt_params = dict(params)
				alt_params["url"] = [url_vals[0].replace("/full/", variant, 1)]
				alt_candidate = NEXT_DIR / ("image?" + encode_params(alt_params))
				if alt_candidate.exists():
					ctype, _ = mimetypes.guess_type(alt_params["url"][0])
					if not ctype:
						ctype = "application/octet-stream"
					self.send_response(200)
					self.send_header("Content-Type", ctype)
					self.send_header("Cache-Control", "public, max-age=31536000, immutable")
					self.end_headers()
					with open(alt_candidate, "rb") as f:
						self.wfile.write(f.read())
					return True

		# Fallback: serve the underlying source image directly if present
		if url_vals:
			source_url = url_vals[0]
			source_rel = source_url.lstrip("/")
			search_paths = [
				BASE_DIR / source_rel,
				BASE_DIR / source_rel.replace("full/", "color/", 1),
				BASE_DIR / source_rel.replace("full/", "mono/", 1),
			]
			for candidate_file in search_paths:
				if candidate_file.exists():
					ctype, _ = mimetypes.guess_type(str(candidate_file))
					if not ctype:
						ctype = "application/octet-stream"
					self.send_response(200)
					self.send_header("Content-Type", ctype)
					self.send_header("Cache-Control", "public, max-age=31536000, immutable")
					self.end_headers()
					with open(candidate_file, "rb") as f:
						self.wfile.write(f.read())
					return True

		return False

	def do_GET(self):
		parsed = urllib.parse.urlsplit(self.path)
		path = parsed.path
		query = parsed.query

		# 0) Handle encoded path variant: /_next/image%3F...
		if path.startswith("/_next/image%3F"):
			encoded_query = path.split("/_next/image%3F", 1)[1]
			if self._serve_next_image_candidate(encoded_query):
				return

		# 0.5) Rewrite dynamic bouquet viewer to color mode static page
		if path.startswith("/bouquet/") and not os.path.splitext(path)[1]:
			viewer = BASE_DIR / "bouquet?mode=color.html"
			if viewer.exists():
				self.send_response(200)
				self.send_header("Content-Type", "text/html; charset=utf-8")
				self.end_headers()
				with open(viewer, "rb") as f:
					self.wfile.write(f.read())
				return

		# 1) Map Next.js image optimization endpoint to exported files
		if path == "/_next/image" and query:
			if self._serve_next_image_candidate(query):
				return

		# 2) Pretty URL mapping: /garden -> garden.html (ignore query)
		if not os.path.splitext(path)[1]:  # no extension in path
			candidate_html = BASE_DIR / (path.strip("/") + ".html" if path != "/" else "index.html")
			if candidate_html.exists():
				self.path = "/" + os.path.relpath(candidate_html, BASE_DIR)
				return http.server.SimpleHTTPRequestHandler.do_GET(self)

		# 3) Queryful page mapping: /bouquet?mode=color -> bouquet?mode=color.html in root
		if query:
			file_with_query = (BASE_DIR / (path.strip("/") + "?" + query + ".html"))
			if file_with_query.exists():
				self.send_response(200)
				self.send_header("Content-Type", "text/html; charset=utf-8")
				self.end_headers()
				with open(file_with_query, "rb") as f:
					self.wfile.write(f.read())
				return

		# Fallback to default static serving (handles /_next/static/*, css, js, fonts, icons)
		return http.server.SimpleHTTPRequestHandler.do_GET(self)


def run(server_class=http.server.ThreadingHTTPServer, handler_class=NextStaticRewriteHandler, port=5174):
	server_address = ("", port)
	httpd = server_class(server_address, handler_class)
	print(f"Serving digibouquet static export with rewrites on http://localhost:{port}")
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		httpd.server_close()

if __name__ == "__main__":
	run() 
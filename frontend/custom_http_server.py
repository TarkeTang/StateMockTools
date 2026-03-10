import http.server
import socketserver
import logging
import os

# 配置日志
log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=date_format
)

logger = logging.getLogger("frontend.server")

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # 自定义日志格式
        if len(args) >= 3:
            logger.info(f"{self.client_address[0]} - {args[0]} {args[1]} {args[2]}")
        else:
            logger.info(f"{self.client_address[0]} - {format % args}")

if __name__ == "__main__":
    PORT = 3000
    
    # 确保在frontend目录下运行
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    handler = CustomHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        logger.info(f"Serving HTTP on port {PORT} (http://localhost:{PORT}/) ...")
        httpd.serve_forever()

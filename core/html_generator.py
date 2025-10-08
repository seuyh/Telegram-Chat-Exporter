from datetime import datetime
from . import utils


class HtmlGenerator:
    def __init__(self, chat_name: str, messages: list):
        self.chat_name = chat_name
        self.messages = messages

    def generate(self) -> str:
        grouped_messages = {}
        for msg in self.messages:
            if not msg: continue
            date_key = msg['date'].strftime("%d %B %Y")
            if date_key not in grouped_messages:
                grouped_messages[date_key] = []
            grouped_messages[date_key].append(msg)

        messages_html = ""
        for date, msgs in grouped_messages.items():
            messages_html += f'<div class="date-separator">{date}</div>\n'
            for msg in msgs:
                messages_html += self._generate_message_html(msg)

        return self._get_html_template(messages_html)

    def _generate_message_html(self, msg: dict) -> str:
        if msg.get('action_text'):
            return f'<div class="system-message">{utils.escape_html(msg["action_text"])}</div>'

        time_str = msg['date'].strftime("%H:%M")
        html = f'<div class="message">\n'
        html += f'    <div class="message-header">\n'
        html += f'        <span class="sender">{utils.escape_html(msg["from"])}</span>\n'
        html += f'        <span class="time">{time_str}</span>\n'
        html += f'    </div>\n'

        if msg.get('forwarded'):
            html += f'    <div class="forwarded">Forwarded from: {utils.escape_html(msg["forwarded"]["from"])}</div>\n'
        if msg.get('reply_to'):
            html += f'    <div class="reply">\n'
            html += f'        <div class="reply-from">{utils.escape_html(msg["reply_to"]["from"])}</div>\n'
            html += f'        <div class="reply-text">{utils.format_text(msg["reply_to"]["text"][:200])}</div>\n'
            html += f'    </div>\n'
        if msg.get('text'):
            html += f'    <div class="text">{msg["text"]}</div>\n'

        if msg.get('media'):
            media_path, media_type = msg["media"], msg["media_type"]
            if media_type == 'photo':
                html += f'    <div class="media"><img class="media-item" src="{media_path}" alt="Photo"></div>\n'
            elif media_type == 'video':
                html += f'    <div class="media"><video class="media-item" controls playsinline preload="metadata" src="{media_path}"></video></div>\n'
            elif media_type == 'audio':
                html += f'    <div class="media"><audio controls src="{media_path}"></audio></div>\n'
            else:
                filename = media_path.split('/')[-1]
                html += f'    <div class="document">\n'
                html += f'        <div class="document-icon">📄</div>\n'
                html += f'        <a href="{media_path}" class="document-name" download>{utils.escape_html(filename)}</a>\n'
                html += f'    </div>\n'
        elif msg.get('media_placeholder'):
            html += f'    <div class="media-placeholder">{utils.escape_html(msg["media_placeholder"])}</div>\n'

        html += '</div>\n'
        return html

    def _get_html_template(self, messages_html: str) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{utils.escape_html(self.chat_name)} - Export</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0e1621; color: #ffffff; line-height: 1.5; }}
        .body-no-scroll {{ overflow: hidden; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a2332; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; color: #8774e1; }}
        .header .info {{ color: #8b95a5; font-size: 14px; margin-bottom: 20px; }}

        /* === ИЗМЕНЕНИЯ ЗДЕСЬ === */
        .messages-container {{
            /* Этот контейнер будет масштабироваться */
            transform-origin: top; /* Масштабирование от верхнего края */
            transition: transform 0.1s ease-out;
        }}
        .messages {{ background: #17212b; border-radius: 12px; padding: 20px; }}

        .message {{ margin: 15px 0; padding: 12px 16px; background: #1a2332; border-radius: 12px; border-left: 3px solid #8774e1; transition: background 0.2s; font-size: 14px; max-width: 100%; }}
        .message:hover {{ background: #1e2936; }}
        .message-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .sender {{ font-weight: 600; color: #8774e1; font-size: 1em; }}
        .time {{ color: #8b95a5; font-size: 0.9em; }}
        .text {{ color: #e4e9f0; word-wrap: break-word; white-space: pre-wrap; }}
        .text a {{ color: #5288c1; text-decoration: none; }} .text a:hover {{ text-decoration: underline; }}
        .reply {{ background: #0e1621; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 2px solid #5288c1; font-size: 0.9em; }}
        .forwarded {{ color: #8b95a5; font-size: 0.9em; margin-bottom: 8px; font-style: italic; }}
        .media img, .media video {{ max-width: 100%; height: auto; display: block; border-radius: 8px; }}
        .media-item {{ cursor: pointer; }}
        .media audio {{ width: 100%; margin-top: 8px; }}
        .document {{ background: #0e1621; padding: 12px; border-radius: 8px; margin-top: 10px; display: flex; align-items: center; gap: 10px; font-size: 1em; }}
        .media-placeholder {{ background: #0e1621; padding: 10px; border-radius: 8px; margin-top: 10px; border-left: 2px solid #8b95a5; color: #8b95a5; font-style: italic; }}
        .date-separator, .system-message {{ text-align: center; color: #8b95a5; font-size: 13px; padding: 8px 15px; border-radius: 20px; margin: 20px auto; display: table; }}
        .date-separator {{ background: #0e1621; }}
        .system-message {{ background: #1a2332; }}
        .scale-slider-container {{ color: #8b95a5; font-size: 14px; display: flex; justify-content: center; align-items: center; gap: 12px; user-select: none; }}
        input[type="range"] {{ -webkit-appearance: none; appearance: none; width: 220px; background: transparent; cursor: pointer; }}
        input[type="range"]::-webkit-slider-runnable-track {{ background: #0e1621; height: 4px; border-radius: 2px; }}
        input[type="range"]::-moz-range-track {{ background: #0e1621; height: 4px; border-radius: 2px; }}
        input[type="range"]::-webkit-slider-thumb {{ -webkit-appearance: none; appearance: none; margin-top: -6px; background-color: #8774e1; height: 16px; width: 16px; border-radius: 50%; }}
        input[type="range"]::-moz-range-thumb {{ background-color: #8774e1; height: 16px; width: 16px; border-radius: 50%; border: none; }}
        #media-viewer {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; flex-direction: column; justify-content: center; align-items: center; user-select: none; }}
        #media-viewer img, #media-viewer video {{ max-width: 90%; max-height: 80%; border-radius: 8px; object-fit: contain; }}
        .viewer-nav {{ position: absolute; top: 50%; transform: translateY(-50%); width: 50px; height: 50px; background: rgba(255,255,255,0.1); color: white; border-radius: 50%; font-size: 30px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: background 0.2s; }}
        #viewer-prev {{ left: 20px; }} #viewer-next {{ right: 20px; }}
        #viewer-close {{ position: absolute; top: 20px; right: 20px; width: 40px; height: 40px; color: white; font-size: 30px; cursor: pointer; }}
        #viewer-counter {{ position: absolute; top: 20px; left: 50%; transform: translateX(-50%); color: white; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{utils.escape_html(self.chat_name)}</h1>
            <div class="info">Exported: {datetime.now().strftime("%d.%m.%Y %H:%M")} | Messages: {len(self.messages)}</div>
            <div class="scale-slider-container">
                <span style="font-size: 12px;">-</span>
                <input type="range" id="scaleSlider" min="50" max="150" value="100">
                <span style="font-size: 18px;">+</span>
            </div>
        </div>
        <div class="messages-container">
            <div class="messages">{messages_html}</div>
        </div>
    </div>

    <div id="media-viewer">
        </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            // ... (код для медиа-галереи остается без изменений)

            /* === НОВЫЙ КОД ДЛЯ МАСШТАБИРОВАНИЯ === */
            const slider = document.getElementById('scaleSlider');
            const messagesContainer = document.querySelector('.messages-container');

            const applyScale = (scaleValue) => {{
                // Преобразуем значение слайдера (50-150) в масштаб (0.5-1.5)
                const scale = scaleValue / 100;
                messagesContainer.style.transform = `scale(${{scale}})`;
            }};

            // Применяем сохраненный масштаб при загрузке
            const savedScale = localStorage.getItem('chatPageScale');
            if (savedScale) {{
                slider.value = savedScale;
                applyScale(savedScale);
            }}

            // Слушаем изменения слайдера
            slider.addEventListener('input', (e) => {{
                const newScale = e.target.value;
                applyScale(newScale);
                localStorage.setItem('chatPageScale', newScale);
            }});
        }});
    </script>
</body>
</html>'''
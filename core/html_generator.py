from datetime import datetime
from typing import Optional
from . import utils


class HtmlGenerator:
    def __init__(self, chat_name: str, messages: list, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        self.chat_name = chat_name
        self.messages = messages
        self.start_date = start_date
        self.end_date = end_date

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

        if msg.get('media_files'):
            count = len(msg["media_files"])
            container_class = "media-group"
            if count > 1:
                container_class += f" layout-cols-{(2 if count % 2 == 0 else 3)}"

            html += f'    <div class="{container_class}">\n'
            for media in msg['media_files']:
                media_path, media_type = media["path"], media["type"]

                html += f'    <div class="media">\n'
                if media_type == 'photo':
                    html += f'        <img class="media-item" src="{media_path}" alt="Photo">\n'
                elif media_type == 'video':
                    html += f'        <div class="video-wrapper">'
                    html += f'           <video class="media-item" playsinline preload="metadata" src="{media_path}"></video>'
                    html += f'           <div class="play-button"></div>'
                    html += f'        </div>'
                elif media_type == 'audio':
                    html += f'        <audio controls src="{media_path}"></audio>\n'
                else:
                    filename = media_path.split('/')[-1]
                    html += f'    <div class="document-standalone">\n'
                    html += f'        <div class="document-icon">📄</div>\n'
                    html += f'        <a href="{media_path}" class="document-name" download>{utils.escape_html(filename)}</a>\n'
                    html += f'    </div>\n'
                html += f'    </div>\n'
            html += '    </div>\n'

        if msg.get('text'):
            text_class = "text-with-media" if msg.get('media_files') else ""
            html += f'    <div class="text {text_class}">{msg["text"]}</div>\n'

        if msg.get('media_placeholder'):
            html += f'    <div class="media-placeholder">{utils.escape_html(msg["media_placeholder"])}</div>\n'

        html += '</div>\n'
        return html

    def _get_html_template(self, messages_html: str) -> str:
        date_range_html = ""
        if self.start_date or self.end_date:
            if self.messages:
                actual_start_date = self.messages[0]['date']
                actual_end_date = self.messages[-1]['date']
                from_str = actual_start_date.strftime('%d.%m.%Y %H:%M')
                to_str = actual_end_date.strftime('%d.%m.%Y %H:%M')
                date_range_html = f'<div class="info" style="font-size: 13px; color: #aab5c3; margin-top: 5px;">Export Range: {from_str} — {to_str} (UTC)</div>'
            else:
                date_range_html = f'<div class="info" style="font-size: 13px; color: #aab5c3; margin-top: 5px;">No messages found in the selected range</div>'

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

            .header {{ 
                background: #1a2332; 
                padding: 30px; 
                border-radius: 12px; 
                margin-bottom: 30px; 
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 100;
                transition: transform 0.3s ease-in-out, padding 0.3s ease-in-out;
                will-change: transform, padding;
            }}
            .header--hidden {{
                transform: translateY(-120%);
            }}
            .header h1 {{ 
                font-size: 28px; 
                margin-bottom: 10px; 
                color: #8774e1;
                transition: font-size 0.3s ease-in-out, margin-bottom 0.3s ease-in-out;
            }}
            .header .info {{ 
                color: #8b95a5; 
                font-size: 14px; 
                margin-bottom: 20px;
                transition: opacity 0.3s ease-in-out, height 0.3s ease-in-out, margin-bottom 0.2s ease-in-out;
                height: 1.5em;
                opacity: 1;
                overflow: hidden;
            }}

            .header--shrunk {{
                padding-top: 15px;
                padding-bottom: 15px;
            }}
            .header--shrunk h1 {{
                font-size: 22px;
                margin-bottom: 15px;
            }}
            .header--shrunk .info {{
                height: 0;
                opacity: 0;
                margin-bottom: 0;
            }}

            .messages-container {{ transform-origin: top; transition: transform 0.1s ease-out; }}
            .messages {{ background: #17212b; border-radius: 12px; padding: 20px; }}
            .message {{ margin: 15px 0; padding: 12px 16px; background: #1a2332; border-radius: 12px; border-left: 3px solid #8774e1; transition: background 0.2s; font-size: 14px; max-width: 100%; }}
            .message:hover {{ background: #1e2936; }}
            .message-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
            .sender {{ font-weight: 600; color: #8774e1; font-size: 1em; }}
            .time {{ color: #8b95a5; font-size: 0.9em; }}
            .text {{ color: #e4e9f0; word-wrap: break-word; white-space: pre-wrap; }}
            .text-with-media {{ margin-top: 10px; }}
            .text a {{ color: #5288c1; text-decoration: none; }} .text a:hover {{ text-decoration: underline; }}
            .reply {{ background: #0e1621; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 2px solid #5288c1; font-size: 0.9em; }}
            .forwarded {{ color: #8b95a5; font-size: 0.9em; margin-bottom: 8px; font-style: italic; }}
            .media-group {{ display: grid; gap: 3px; }}
            .media img, .media video {{ width: 100%; height: auto; display: block; cursor: pointer; border-radius: 8px; }}
            .layout-cols-2 {{ grid-template-columns: 1fr 1fr; }}
            .layout-cols-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
            .video-wrapper {{ position: relative; width: 100%; height: 100%; border-radius: 8px; overflow: hidden;}}
            .play-button {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; background-color: rgba(0, 0, 0, 0.5); border-radius: 50%; display: flex; align-items: center; justify-content: center; pointer-events: none; }}
            .play-button::after {{ content: ''; border-style: solid; border-width: 10px 0 10px 20px; border-color: transparent transparent transparent white; margin-left: 5px; }}
            .media audio {{ width: 100%; margin-top: 8px; }}
            .document-standalone {{ background: #0e1621; padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px; font-size: 1em; }}
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
                {date_range_html}
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

        <div id="media-viewer"></div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const viewer = document.getElementById('media-viewer');
                const messagesContainer = document.querySelector('.messages-container');
                const messages = document.querySelector('.messages');
                const body = document.body;
                const slider = document.getElementById('scaleSlider');
                const header = document.querySelector('.header');
                const initialContentHeight = messages.offsetHeight;
                let mediaItems = [];
                let currentIndex = -1;
                let lastScrollTop = 0;

                const setupMediaItems = () => {{
                    const clickableMedia = document.querySelectorAll('.media-item');
                    mediaItems = Array.from(clickableMedia);
                    mediaItems.forEach((item, index) => {{
                        const parent = item.parentElement;
                        if (parent.classList.contains('video-wrapper')) {{
                            parent.addEventListener('click', () => openViewer(index));
                        }} else {{
                            item.addEventListener('click', () => openViewer(index));
                        }}
                    }});
                }};

                const openViewer = (index) => {{
                    currentIndex = index;
                    updateViewerContent();
                    viewer.style.display = 'flex';
                    body.classList.add('body-no-scroll');
                }};

                const closeViewer = () => {{
                    viewer.style.display = 'none';
                    viewer.innerHTML = '';
                    body.classList.remove('body-no-scroll');
                }};

                const changeMedia = (direction) => {{
                    currentIndex += direction;
                    if (currentIndex >= mediaItems.length) currentIndex = 0;
                    if (currentIndex < 0) currentIndex = mediaItems.length - 1;
                    updateViewerContent();
                }};

                const updateViewerContent = () => {{
                    const item = mediaItems[currentIndex];
                    const isVideo = item.tagName === 'VIDEO';
                    let contentHtml = isVideo ? `<video src="${{item.getAttribute('src')}}" controls autoplay></video>` : `<img src="${{item.src}}" alt="Media">`;
                    viewer.innerHTML = `
                        <div id="viewer-close" class="viewer-control">×</div>
                        <div id="viewer-prev" class="viewer-nav viewer-control">‹</div>
                        <div id="viewer-next" class="viewer-nav viewer-control">›</div>
                        <div id="viewer-counter">${{currentIndex + 1}} / ${{mediaItems.length}}</div>
                        ${{contentHtml}}
                    `;
                }};

                viewer.addEventListener('click', (e) => {{
                    if (e.target.classList.contains('viewer-control')) {{
                        if (e.target.id === 'viewer-close') closeViewer();
                        if (e.target.id === 'viewer-prev') changeMedia(-1);
                        if (e.target.id === 'viewer-next') changeMedia(1);
                    }} else if (e.target.tagName !== 'VIDEO') {{
                        closeViewer();
                    }}
                }});

                document.addEventListener('keydown', (e) => {{
                    if (viewer.style.display === 'flex') {{
                        if (e.key === 'Escape') closeViewer();
                        if (e.key === 'ArrowLeft') changeMedia(-1);
                        if (e.key === 'ArrowRight') changeMedia(1);
                    }}
                }});

                const applyScale = (scaleValue) => {{
                    let value = parseInt(scaleValue, 10);

                    if (window.innerWidth < 768 && value > 100) {{
                        value = 100;
                        slider.value = 100;
                    }}

                    const scale = value / 100;
                    messagesContainer.style.transform = `scale(${{scale}})`;
                    messagesContainer.style.height = `${{initialContentHeight * scale}}px`;
                }};

                const savedScale = localStorage.getItem('chatPageScale');
                if (savedScale) {{
                    slider.value = savedScale;
                }}
                applyScale(slider.value);

                slider.addEventListener('input', (e) => {{
                    const newScaleValue = e.target.value;
                    applyScale(newScaleValue);
                    if (window.innerWidth >= 768 || newScaleValue <= 100) {{
                       localStorage.setItem('chatPageScale', newScaleValue);
                    }}
                }});

                header.addEventListener('mouseenter', () => {{
                    header.classList.remove('header--hidden');
                }});

                window.addEventListener('scroll', () => {{
                    let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

                    if (scrollTop > 50) {{
                        header.classList.add('header--shrunk');
                    }} else {{
                        header.classList.remove('header--shrunk');
                    }}

                    if (scrollTop > lastScrollTop && scrollTop > 50) {{
                        header.classList.add('header--hidden');
                    }} else {{
                        header.classList.remove('header--hidden');
                    }}

                    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
                }}, false);

                window.addEventListener('resize', () => {{
                    applyScale(slider.value);
                }});

                setupMediaItems();
            }});
        </script>
    </body>
    </html>'''
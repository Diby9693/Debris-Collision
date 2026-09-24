import os
import re

def main():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    with open('css/styles.css', 'r', encoding='utf-8') as f:
        css = f.read()

    import base64

    # Files in topological dependency order
    js_files = [
        'js/config.js',
        'js/orbital-math.js',
        'js/data-source.js',
        'js/ai-predictor.js',
        'js/audio-fx.js',
        'js/earth-3d.js',
        'js/source-viewer.js',
        'js/ai-assistant.js',
        'js/ui-controller.js',
        'js/main.js'
    ]

    # Pre-embed audio files as base64 Data URIs for 100% self-contained standalone.html
    embedded_audio_js = "window.EMBEDDED_AUDIO = {\n"
    audio_map = [
        ('radarPing', 'audio/radar-ping.mp3'),
        ('debrisCollision', 'audio/debris-collision.mp3'),
        ('alertSiren', 'audio/alert-siren.mp3')
    ]
    for key, path in audio_map:
        if os.path.exists(path):
            with open(path, 'rb') as af:
                b64 = base64.b64encode(af.read()).decode('ascii')
                embedded_audio_js += f'  "{key}": "data:audio/mp3;base64,{b64}",\n'
    embedded_audio_js += "};\n\n"

    bundled_js = [embedded_audio_js]
    for path in js_files:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Remove imports
        code = re.sub(r'import\s+.*?from\s+[\'"][^\'"]+[\'"];?', '', code)
        
        # Convert export default class X / export class X to class X / window.X = X
        code = re.sub(r'export\s+default\s+class\s+([A-Za-z0-9_]+)', r'class \1', code)
        code = re.sub(r'export\s+class\s+([A-Za-z0-9_]+)', r'class \1', code)
        code = re.sub(r'export\s+const\s+([A-Za-z0-9_]+)', r'const \1', code)
        code = re.sub(r'export\s+function\s+([A-Za-z0-9_]+)', r'function \1', code)
        
        bundled_js.append(f"// === BEGIN {path} ===\n{code}\n// === END {path} ===")

    all_js = "\n\n".join(bundled_js)

    # Replace CSS link
    html = html.replace('<link rel="stylesheet" href="css/styles.css">', f'<style>\n{css}\n</style>')

    # Replace script module with inline script (use lambda to prevent backslash expansion)
    html = re.sub(r'<script\s+type="module"\s+src="js/main.js"></script>', lambda m: f'<script>\n{all_js}\n</script>', html)

    with open('standalone.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("standalone.html created successfully! Size:", os.path.getsize('standalone.html'), "bytes")

if __name__ == '__main__':
    main()

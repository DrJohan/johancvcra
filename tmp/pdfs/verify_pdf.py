from pathlib import Path
from html.parser import HTMLParser
import difflib
import re
from collections import Counter
from pypdf import PdfReader
import pdfplumber
from PIL import Image, ImageOps, ImageDraw

ROOT = Path.cwd()

class MainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.main_depth = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self.depth += 1
            if dict(attrs).get('id') == 'main':
                self.main_depth = self.depth

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.depth == self.main_depth:
                self.main_depth = None
            self.depth -= 1

    def handle_data(self, data):
        if self.main_depth is not None:
            self.parts.append(data)

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def main_text(path):
    parser = MainText()
    parser.feed(path.read_text(encoding='utf-8'))
    return clean(' '.join(parser.parts))

class HTMLChecks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'script' and 'src' in attrs:
            self.scripts.append(attrs['src'])

for path in (ROOT / 'index.html', ROOT / 'tmp/pdfs/cv-pdf.html'):
    html = path.read_text(encoding='utf-8')
    parser = HTMLChecks()
    parser.feed(html)
    duplicates = [key for key, count in Counter(parser.ids).items() if count > 1]
    assert not duplicates, f'Duplicate HTML IDs: {duplicates}'
    assert '<mark class="intro-highlight"><strong>Hi my name is Dr Johan Ibrahim.</strong></mark>' in html
    assert 'background-color: #fff2a8' in html
    assert 'print-color-adjust: exact' in html
    assert not any('Rm9yYmlkZGVu' in src for src in parser.scripts)
print('HTML IDs, bold introduction, print highlight, and script sources verified.')

website = main_text(ROOT / 'index.html')
pdf_html = main_text(ROOT / 'tmp/pdfs/cv-pdf.html')
if website != pdf_html:
    print('Main text differences:')
    print('\n'.join(list(difflib.unified_diff(website.split(), pdf_html.split()))[:120]))
    raise AssertionError('PDF source content differs from the live website source')
print('All CV main content matches the website source.')

reader = PdfReader(ROOT / 'output/pdf/drjohan_cv.pdf')
text = clean(' '.join(page.extract_text() for page in reader.pages))
expected = [
    'Hi my name is Dr Johan Ibrahim.',
    'I am the Clinic Manager at Klinik Inocare on Jalan Pahang, Kuala Lumpur.',
    'My work brings together medical training, clinical research experience and operational leadership to strengthen clinic services and support patient care.',
    'My experience spans clinical practice, clinical trial monitoring and health research, supported by a strong foundation in research design, medical statistics, data management and visualisation.',
    'With Good Clinical Practice certification, I am committed to ethical research, data quality and patient safety.',
    'I combine analytical thinking with a collaborative approach to solve problems, improve workflows and deliver results in demanding healthcare settings.',
    'Analisa Data Dengan R Studio group',
]
for sentence in expected:
    assert sentence in text, f'Missing PDF sentence: {sentence}'
assert 'Currently I\u2019m working as Clinical Research Associate with' not in text
assert len(reader.pages) == 5
uris = []
for number, page in enumerate(reader.pages, 1):
    page_text = clean(page.extract_text())
    assert page_text
    print(f'Page {number}: {len(page_text)} text characters')
    for annotation in page.get('/Annots', []):
        action = annotation.get_object().get('/A', {})
        if action.get('/URI'):
            uris.append(str(action['/URI']))
assert 'https://drjohan.github.io/johancvcra/' in uris
assert not any(uri.startswith('file:') for uri in uris)
print('Updated introduction and PDF links verified.')
print('Link destinations:', uris)

with pdfplumber.open(ROOT / 'output/pdf/drjohan_cv.pdf') as pdf:
    intro_words = pdf.pages[0].extract_words(extra_attrs=['fontname'])
    hi = next(word for word in intro_words if word['text'] == 'Hi')
    intro = [word for word in intro_words if abs(word['top'] - hi['top']) < 0.1 and word['x0'] <= 260]
    assert ' '.join(word['text'] for word in intro).startswith('Hi my name is Dr Johan Ibrahim.')
    highlights = []
    for rect in pdf.pages[0].rects:
        color = rect.get('non_stroking_color')
        if isinstance(color, (tuple, list)) and len(color) == 3:
            if all(abs(actual - wanted) < 0.02 for actual, wanted in zip(color, (1, 242/255, 168/255))):
                highlights.append(rect)
    assert highlights, 'PDF highlight background missing'
    assert any(rect['top'] <= hi['top'] and rect['bottom'] >= hi['bottom'] for rect in highlights)
print('PDF introduction text and yellow background verified.')

previews = sorted((ROOT / 'tmp/pdfs').glob('cv-page-*.png'))
assert len(previews) == len(reader.pages)
contact = Image.new('RGB', (3 * 480, 2 * 650), '#d9d9d9')
draw = ImageDraw.Draw(contact)
for index, path in enumerate(previews):
    image = Image.open(path).convert('RGB')
    image.thumbnail((460, 615))
    x = (index % 3) * 480 + 10
    y = (index // 3) * 650 + 25
    contact.paste(ImageOps.expand(image, border=1, fill='#999999'), (x, y))
    draw.text((x, y - 18), f'Page {index + 1}', fill='black')
contact.save(ROOT / 'tmp/pdfs/contact-sheet.png')

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class EvidenceContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        image = Image.new('RGB', (200, 400), 'white')
        image.paste('navy', (0, 0, 200, 20))
        image.paste('green', (0, 380, 200, 400))
        image.save(self.run / 'source.png')
        spec = {'source': 'source.png', 'crop': [0.25, 0.25, 0.5, 0.25],
                'boxes': [[0.3, 0.3, 0.2, 0.1]]}
        self.write('annotations.json', {'items': [{'id': 'issue-1', 'problem': spec, 'design': spec}]})
        self.invoke('render-evidence.py')
        self.entry = json.loads((self.run / 'evidence/render-manifest.json').read_text())[0]

    def write(self, name, data):
        (self.run / name).write_text(json.dumps(data))

    def invoke(self, script, *args):
        return subprocess.run([sys.executable, str(ROOT / 'scripts' / script),
                               '--run', str(self.run), *args], capture_output=True, text=True, check=True)

    def test_crop_is_supplement_and_full_page_edges_survive(self):
        self.assertEqual(self.entry['context_mode'], 'full')
        for side in ['problem', 'design']:
            with Image.open(self.run / self.entry[side + '_image']) as main:
                self.assertEqual(main.size, (600, 1200))
                self.assertEqual(main.getpixel((0, 0)), (0, 0, 128))
                self.assertEqual(main.getpixel((0, 1199)), (0, 128, 0))
            with Image.open(self.run / self.entry[side + '_detail_image']) as detail:
                self.assertEqual(detail.size, (600, 600))

    def test_final_delivery_rejects_detail_as_primary_image(self):
        url = 'https://www.figma.com/design/example?node-id=1-2'
        self.write('run.json', {'platforms': ['iOS'], 'module_order': ['Header'], 'pages': [
            {'id': 'page-1', 'status': 'done', 'requirements': [
                {'id': 'req-1', 'summary': 'Arrow appearance', 'figma_url': url, 'case_ids': ['case-1']}]}]})
        self.write('cases.json', [{'id': 'case-1', 'page_id': 'page-1', 'platform': 'iOS',
            'module': 'Header', 'status': 'issue', 'preconditions': [], 'steps': ['Open History'],
            'expected': 'Design arrow', 'figma_url': url, 'finding_ids': ['issue-1']}])
        finding = {'id': 'issue-1', 'platform': 'iOS', 'module': 'Header', 'kind': 'implementation',
            'review': 'confirmed', 'publish': False, 'case_ids': ['case-1'], 'title': 'Arrow size',
            'actual': 'Too large', 'expected': 'Design size', 'feedback': 'Restore arrow size',
            'figma_url': url, 'problem_source': 'source.png', 'design_source': 'source.png',
            'problem_image': self.entry['problem_image'], 'design_image': self.entry['design_image']}
        self.write('findings.json', [finding])
        self.invoke('validate-delivery.py', '--final')
        finding['problem_image'] = self.entry['problem_detail_image']
        self.write('findings.json', [finding])
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.invoke('validate-delivery.py', '--final')
        self.assertIn('必须引用完整主图', caught.exception.stdout)


if __name__ == '__main__':
    unittest.main()

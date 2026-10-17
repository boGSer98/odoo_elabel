"""Offline package validation; native Odoo tests are intentionally separate."""
import ast
import csv
import pathlib
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]
MODULES=('odoo_elabel','odoo_elabel_documents','odoo_elabel_sale','odoo_elabel_wine_analysis')


def main():
    counts={'python':0,'xml':0,'manifests':0,'acl':0}
    for module in MODULES:
        folder=ROOT/module
        manifest=ast.literal_eval((folder/'__manifest__.py').read_text())
        expected_version = {'odoo_elabel':'19.0.1.4.3','odoo_elabel_sale':'19.0.1.4.6','odoo_elabel_documents':'19.0.1.4.2','odoo_elabel_wine_analysis':'19.0.1.0.0'}[module]
        assert manifest['version']==expected_version,(module,'version')
        assert manifest.get('installable'),module
        counts['manifests']+=1
        for entry in manifest.get('data',[]):assert (folder/entry).is_file(),(module,entry)
        for path in folder.rglob('*.py'):
            ast.parse(path.read_text(),filename=str(path));counts['python']+=1
        ids=set()
        for path in folder.rglob('*.xml'):
            tree=ET.parse(path);counts['xml']+=1
            for record in tree.iter():
                if record.get('id'):
                    # External IDs may be referenced via qualified names.
                    key=record.get('id');assert key not in ids,(module,key);ids.add(key)
        for path in folder.rglob('ir.model.access.csv'):
            rows=list(csv.DictReader(path.open()))
            assert len({r['id'] for r in rows})==len(rows)
            for row in rows:
                assert row['group_id:id'],(module,'unrestricted ACL')
                assert all(row[k] in ('0','1') for k in ('perm_read','perm_write','perm_create','perm_unlink'))
            counts['acl']+=len(rows)
    core=ast.literal_eval((ROOT/'odoo_elabel/__manifest__.py').read_text())
    assert not {'documents','documents_product','website_sale'}.intersection(core['depends'])
    bridge=ast.literal_eval((ROOT/'odoo_elabel_documents/__manifest__.py').read_text())
    assert {'odoo_elabel','documents_product'}.issubset(bridge['depends'])
    for path in ROOT.rglob('*.py'):
        if '.git' not in path.parts:ast.parse(path.read_text(),filename=str(path))
    print('PACKAGE_CHECKS_OK',counts)

if __name__=='__main__':main()

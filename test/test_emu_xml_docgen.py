import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = REPO_ROOT / "doc"
if str(DOC_DIR) not in sys.path:
    sys.path.insert(0, str(DOC_DIR))

import gen_emu_xml_trees


def test_tree_from_real_xml_contains_expected_structure():
    xml_path = REPO_ROOT / "test" / "emu" / "devices" / "ad5710r.xml"

    tree = gen_emu_xml_trees.tree_from_xml_path(xml_path)

    assert "context name=xml" in tree
    assert "device id=iio:device0 name=ad5710r" in tree
    assert "channel id=voltage0 type=output name=Ch0" in tree
    assert "attribute name=raw filename=out_voltage0_raw value=0" in tree
    assert "debug-attribute name=direct_reg_access" in tree


def test_generation_is_deterministic_and_cleans_stale_files(tmp_path):
    xml_dir = tmp_path / "xml"
    out_dir = tmp_path / "out"
    xml_dir.mkdir()

    (xml_dir / "z.xml").write_text(
        '<context name="z"><device id="iio:device0" name="zdev"/></context>',
        encoding="utf-8",
    )
    (xml_dir / "a.xml").write_text(
        '<context name="a"><context-attribute name="k" value="v"/></context>',
        encoding="utf-8",
    )

    repo_root = tmp_path
    stale_file = out_dir / "stale.rst"
    out_dir.mkdir()
    stale_file.write_text("old", encoding="utf-8")

    first = gen_emu_xml_trees.generate_emu_xml_tree_docs(
        repo_root=repo_root, xml_dir=xml_dir, output_dir=out_dir,
    )
    first_contents = {path.name: path.read_text(encoding="utf-8") for path in first}

    second = gen_emu_xml_trees.generate_emu_xml_tree_docs(
        repo_root=repo_root, xml_dir=xml_dir, output_dir=out_dir,
    )
    second_contents = {path.name: path.read_text(encoding="utf-8") for path in second}

    assert first_contents == second_contents
    assert [path.name for path in first] == ["a.rst", "index.rst", "z.rst"]
    assert not stale_file.exists()

    index = (out_dir / "index.rst").read_text(encoding="utf-8")
    assert "   a" in index
    assert "   z" in index
    assert index.find("   a") < index.find("   z")

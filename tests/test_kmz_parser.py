import io
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

from kmz_parser import KmzParseError, parse_kmz, parse_kmz_document


TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2"><Document><wpml:templateId>0</wpml:templateId><wpml:templateType>waypoint</wpml:templateType><wpml:heightMode>relativeToStartPoint</wpml:heightMode><Folder><Placemark><Point><coordinates>120.0,30.0,0</coordinates></Point><wpml:index>0</wpml:index><wpml:height>20</wpml:height></Placemark><Placemark><Point><coordinates>120.001,30.001,0</coordinates></Point><wpml:index>1</wpml:index><wpml:height>25</wpml:height></Placemark></Folder></Document></kml>"""
WAYLINES = """<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2"><Document><wpml:templateId>0</wpml:templateId><wpml:waylineId>0</wpml:waylineId><wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode><wpml:globalTransitionalSpeed>8</wpml:globalTransitionalSpeed><Folder><Placemark><Point><coordinates>120.0,30.0</coordinates></Point><wpml:index>0</wpml:index><wpml:executeHeight>20</wpml:executeHeight><wpml:waypointSpeed>5</wpml:waypointSpeed><wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc></Placemark><Placemark><Point><coordinates>120.001,30.001</coordinates></Point><wpml:index>1</wpml:index><wpml:executeHeight>25</wpml:executeHeight><wpml:waypointSpeed>6</wpml:waypointSpeed></Placemark></Folder></Document></kml>"""


class ParserTests(unittest.TestCase):
    def write_kmz(self, files: dict[str, str]) -> Path:
        handle = tempfile.NamedTemporaryFile(suffix=".kmz", delete=False)
        handle.close()
        path = Path(handle.name)
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return path

    def test_reads_standard_wpmz_paths_without_extracting(self):
        path = self.write_kmz({"wpmz/template.kml": TEMPLATE, "wpmz/waylines.wpml": WAYLINES})
        try:
            model = parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(len(model.waypoints), 2)
        self.assertEqual(len(model.template_waypoints), 2)
        self.assertEqual(model.execute_height_mode, "relativeToStartPoint")
        self.assertEqual(model.height_mode, "relativeToStartPoint")
        self.assertEqual(model.waypoints[0].actions, ["takePhoto"])
        self.assertGreater(model.statistics["distanceMeters"], 100)

    def test_preserves_ellipsoid_height_for_3d_view(self):
        content = TEMPLATE.replace("<wpml:height>20</wpml:height>", "<wpml:height>20</wpml:height><wpml:ellipsoidHeight>45</wpml:ellipsoidHeight>")
        path = self.write_kmz({"template.kml": content})
        try:
            model = parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(model.template_waypoints[0].ellipsoid_height, 45)

    def test_rejects_path_traversal(self):
        path = self.write_kmz({"../route.xml": TEMPLATE})
        try:
            with self.assertRaises(KmzParseError):
                parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)

    def test_accepts_root_fallback_paths(self):
        path = self.write_kmz({"template.kml": TEMPLATE})
        try:
            model = parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(model.template_type, "waypoint")

    def test_rejects_non_kmz(self):
        path = Path(tempfile.mktemp(suffix=".zip"))
        path.write_bytes(b"")
        try:
            with self.assertRaises(KmzParseError):
                parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)

    def test_document_keeps_raw_files_and_field_status(self):
        path = self.write_kmz({"wpmz/template.kml": TEMPLATE, "wpmz/waylines.wpml": WAYLINES})
        try:
            document = parse_kmz_document(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertIn("template.kml", document.files)
        self.assertIn("waylines.wpml", document.files)
        self.assertIn("<kml", document.files["template.kml"].raw_text)
        self.assertEqual(document.files["waylines.wpml"].version, "1.0.2")
        self.assertEqual(len(document.files["waylines.wpml"].route.waypoints), 2)
        self.assertEqual(len(document.files["template.kml"].route.template_waypoints), 2)
        self.assertEqual(len(document.route.waypoints), 2)
        self.assertEqual(len(document.route.template_waypoints), 2)
        self.assertTrue(any(field["name"] == "waypointSpeed" and field["sourceStatus"] == "官方文档" for field in document.files["waylines.wpml"].fields))

    def test_entity_declaration_is_rejected_even_after_prefix(self):
        content = " " * 3000 + "<!DOCTYPE foo [<!ENTITY x 'bad'>]>" + TEMPLATE
        path = self.write_kmz({"template.kml": content})
        try:
            with self.assertRaises(KmzParseError):
                parse_kmz(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

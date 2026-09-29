from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from field_catalog import _OFFICIAL, annotate_fields


WPML_NAMESPACE = "http://www.dji.com/wpmz/1.0.6"


class FieldCatalogTests(unittest.TestCase):
    def test_entire_supplied_2026_wpml_tables_are_indexed(self):
        self.assertEqual(sum(len(row["lines"]) for group in _OFFICIAL.values() for row in group.values()), 267)
        self.assertEqual(len(set().union(*(set(group) for group in _OFFICIAL.values()))), 172)
        self.assertEqual(len(_OFFICIAL["template.kml"]), 84)
        self.assertEqual(len(_OFFICIAL["waylines.wpml"]), 22)
        self.assertEqual(len(_OFFICIAL["common"]), 93)

    def test_documented_mission_fields_have_meaning_and_source(self):
        values = {
            "flyToWaylineMode": "safely",
            "finishAction": "goHome",
            "exitOnRCLost": "goContinue",
            "executeRCLostAction": "goBack",
            "takeOffSecurityHeight": "20",
        }
        fields = [{"name": name, "value": value, "namespace": WPML_NAMESPACE, "path": f"/kml/Document/missionConfig/{name}"} for name, value in values.items()]
        annotated = annotate_fields(fields, "waylines.wpml")
        self.assertTrue(all(field["sourceStatus"] == "官方文档" for field in annotated))
        self.assertTrue(all(field["sourceReference"].startswith("waylines.wpml 说明 (2026-03-19):") for field in annotated))
        self.assertTrue(all(field["label"] != field["name"] for field in annotated))
        self.assertTrue(all(annotated[index]["valueMeaning"] for index in range(4)))
        self.assertEqual(annotated[-1]["unit"], "m")

    def test_new_2026_fields_are_explained(self):
        cases = [("template.kml", "quickOrthoMappingEnable", "1"), ("template.kml", "quickOrthoMappingPitch", "20"), ("waylines.wpml", "megaphoneOperateType", "0"), ("waylines.wpml", "searchlightOperateType", "2")]
        for file_name, name, value in cases:
            with self.subTest(name=name):
                [field] = annotate_fields([{"name": name, "value": value, "namespace": WPML_NAMESPACE, "path": f"/kml/Document/{name}"}], file_name)
                self.assertEqual(field["sourceStatus"], "官方文档")
                self.assertNotEqual(field["label"], name)
                self.assertTrue(field["description"])

    def test_unknown_extension_and_foreign_namespace_are_not_claimed_official(self):
        fields = [
            {"name": "unpublishedExtension", "value": "x", "namespace": WPML_NAMESPACE, "path": "/kml/Document/unpublishedExtension"},
            {"name": "finishAction", "value": "goHome", "namespace": "https://example.invalid/extension", "path": "/kml/Document/finishAction"},
        ]
        self.assertEqual([field["sourceStatus"] for field in annotate_fields(fields, "waylines.wpml")], ["未收录", "未收录"])


if __name__ == "__main__":
    unittest.main()

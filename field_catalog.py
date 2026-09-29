"""Versioned, local-only explanations for WPML fields."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CATALOG_VERSION = "2026-03-19"
CATALOG_SOURCE = "DJI 上云 API 的 template.kml 说明、waylines.wpml 说明和共用元素信息；2026-03-19 用户提供的网页文本"
CATALOG_SCOPE = "收录这三份文档中的 WPML 字段表；文档之外的扩展字段仍显示未收录。"
_OFFICIAL: dict[str, dict[str, dict[str, Any]]] = json.loads(Path(__file__).with_name("field_catalog_data.json").read_text(encoding="utf-8"))

_FIELDS: dict[str, dict[str, str]] = {
    "templateType": {"label": "航线模板类型", "description": "航线任务的模板类型。", "sourceStatus": "官方文档"},
    "templateId": {"label": "模板 ID", "description": "template.kml 与 waylines.wpml 之间关联模板的标识。", "sourceStatus": "官方文档"},
    "waylineId": {"label": "航线 ID", "description": "当前执行航线的标识。", "sourceStatus": "官方文档"},
    "heightMode": {"label": "规划高度模式", "description": "规划文件中高度值采用的参考方式。", "sourceStatus": "官方文档"},
    "executeHeightMode": {"label": "执行高度模式", "description": "执行文件中高度值采用的参考方式。", "sourceStatus": "官方文档"},
    "height": {"label": "规划高度", "description": "规划航点高度，单位由高度模式定义。", "unit": "m", "sourceStatus": "官方文档"},
    "executeHeight": {"label": "执行高度", "description": "执行航点高度，单位由执行高度模式定义。", "unit": "m", "sourceStatus": "官方文档"},
    "waypointSpeed": {"label": "航点速度", "description": "从当前航点飞往下一航点的速度。", "unit": "m/s", "sourceStatus": "官方文档"},
    "globalTransitionalSpeed": {"label": "全局过渡速度", "description": "飞往首航点，或任务中断后恢复至断点时的速度。", "unit": "m/s", "sourceStatus": "官方文档"},
    "waypointHeadingParam": {"label": "航点航向参数", "description": "航点航向相关参数容器。", "sourceStatus": "官方文档"},
    "waypointTurnParam": {"label": "航点转弯参数", "description": "航点转弯相关参数容器。", "sourceStatus": "官方文档"},
    "coordinates": {"label": "坐标", "description": "坐标顺序为经度、纬度，可能附带高度。", "unit": "经纬度", "sourceStatus": "官方文档"},
    "actionActuatorFunc": {"label": "动作执行器功能", "description": "航点动作使用的执行器功能标识。", "sourceStatus": "官方文档"},
    "payloadParam": {"label": "载荷参数", "description": "载荷动作的参数容器；具体子字段按官方版本说明解释。", "sourceStatus": "官方文档"},
    "flyToWaylineMode": {"label": "飞向首航点模式", "description": "定义飞行器从起飞位置到首航点的飞行方式；具体路径依机型和高度设置而定。", "sourceStatus": "官方文档"},
    "finishAction": {"label": "航线结束动作", "description": "定义航线任务完成后的动作。", "sourceStatus": "官方文档"},
    "exitOnRCLost": {"label": "失控后是否继续航线", "description": "决定失控后继续执行航线，还是退出航线并执行失控动作。", "sourceStatus": "官方文档"},
    "executeRCLostAction": {"label": "失控动作", "description": "仅当失控策略设为退出航线并执行失控动作时生效。", "sourceStatus": "官方文档"},
    "takeOffSecurityHeight": {"label": "安全起飞高度", "description": "相对起飞点的安全高度，仅在飞行器尚未起飞时生效。", "unit": "m", "sourceStatus": "官方文档"},
    "quickOrthoMappingEnable": {"label": "正射智能摆拍开关", "description": "控制单次建图航拍任务中是否通过云台摆动完成正射拍摄。", "sourceStatus": "官方文档"},
    "quickOrthoMappingPitch": {"label": "正射智能摆拍角度", "description": "正射智能摆拍的角度；文档给出的范围为 10～30°，在开启正射智能摆拍时必需。", "unit": "°", "sourceStatus": "官方文档"},
    "megaphoneOperateType": {"label": "喊话动作开关", "description": "控制喊话器开始或结束喊话。", "sourceStatus": "官方文档"},
    "megaphoneOperateVolume": {"label": "喊话动作音量", "description": "喊话器音量，文档给出的范围为 0～100。", "sourceStatus": "官方文档"},
    "megaphoneOperateLoop": {"label": "是否单曲循环播放", "description": "控制喊话音频是否单曲循环播放。", "sourceStatus": "官方文档"},
    "megaphoneOperateFilePath": {"label": "喊话音频文件路径", "description": "喊话音频文件在 KMZ 包中的路径。", "sourceStatus": "官方文档"},
    "megaphoneFileName": {"label": "喊话音频文件名", "description": "喊话音频文件在 KMZ 包中对应的名称。", "sourceStatus": "官方文档"},
    "megaphoneFileOriginalName": {"label": "喊话音频显示名", "description": "播放时喊话器回传的音频名称。", "sourceStatus": "官方文档"},
    "megaphoneFileMd5": {"label": "喊话音频 MD5", "description": "喊话音频文件的 MD5 值。", "sourceStatus": "官方文档"},
    "megaphoneFileBitrate": {"label": "喊话音频比特率", "description": "喊话音频压缩比特率；文档注明当前仅支持值 4（32000）。", "sourceStatus": "官方文档"},
    "searchlightOperateType": {"label": "探照灯操作类型", "description": "控制探照灯关闭、照明或爆闪。", "sourceStatus": "官方文档"},
    "searchlightBrightness": {"label": "探照灯亮度", "description": "探照灯亮度，文档给出的范围为 0～100。", "sourceStatus": "官方文档"},
}

_VALUE_MEANINGS = {
    "flyToWaylineMode": {"safely": "安全模式：先爬升到要求的高度，再前往首航点；具体轨迹随机型和首航点高度变化。", "pointToPoint": "倾斜飞行模式：起飞后按机型要求前往首航点。"},
    "finishAction": {"goHome": "航线结束后返航。", "noAction": "航线结束后退出航线模式。", "autoLand": "航线结束后原地降落。", "gotoFirstWaypoint": "航线结束后飞回起始航点。"},
    "exitOnRCLost": {"goContinue": "失控后继续执行航线。", "executeLostAction": "失控后退出航线，执行失控动作。"},
    "executeRCLostAction": {"goBack": "失控动作设为返航；仅在退出航线并执行失控动作时生效。", "landing": "失控动作设为原地降落；仅在退出航线并执行失控动作时生效。", "hover": "失控动作设为悬停；仅在退出航线并执行失控动作时生效。"},
    "quickOrthoMappingEnable": {"0": "关闭正射智能摆拍。", "1": "开启正射智能摆拍。"},
    "megaphoneOperateType": {"0": "开始喊话。", "1": "结束喊话。"},
    "megaphoneOperateLoop": {"0": "关闭单曲循环。", "1": "开启单曲循环。"},
    "megaphoneFileBitrate": {"1": "8000；文档注明当前仅支持值 4。", "2": "16000；文档注明当前仅支持值 4。", "3": "24000；文档注明当前仅支持值 4。", "4": "32000；文档注明当前仅支持此值。", "5": "48000；文档注明当前仅支持值 4。", "6": "64000；文档注明当前仅支持值 4。"},
    "searchlightOperateType": {"0": "关闭探照灯。", "1": "开启照明。", "2": "开启爆闪。"},
}


def _official_field(file_name: str, name: str) -> dict[str, Any] | None:
    return _OFFICIAL.get(file_name, {}).get(name) or _OFFICIAL["common"].get(name)


def annotate_fields(fields: list[dict[str, Any]], file_name: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for field in fields:
        item = dict(field)
        name = field.get("name", "")
        namespace = field.get("namespace", "")
        official = _official_field(file_name, name) if namespace.startswith("http://www.dji.com/wpmz/") else None
        curated = _FIELDS.get(name, {}) if official or (name == "coordinates" and namespace == "http://www.opengis.net/kml/2.2") else {}
        if official:
            label = curated.get("label", official["label"])
            field_type = official.get("type", "")
            if official.get("ambiguous") and not curated:
                description = "官方文档在不同节点对此字段有不同解释，请结合下方 XML 路径核对。"
            else:
                description = curated.get("description") or f"官方 WPML 文档称为「{official['label']}」" + (f"，类型：{field_type}。" if field_type and field_type != "-" else "。")
            unit = curated.get("unit", official.get("unit", ""))
            status = "官方文档"
            source = f"{official['source']}:{official['lines'][0]}"
        elif curated:
            label = curated["label"]
            description = curated["description"]
            unit = curated.get("unit", "")
            status = curated["sourceStatus"]
            source = "KML 坐标"
        else:
            label = name or "未知字段"
            description = "本地官方 WPML 字段目录未收录该字段含义，仅展示原始值。"
            unit = ""
            status = "未收录"
            source = ""
        item.update({
            "file": file_name,
            "label": label,
            "description": description,
            "unit": unit,
            "sourceStatus": status,
            "sourceReference": source,
            "valueMeaning": _VALUE_MEANINGS.get(name, {}).get(str(field.get("value")), "") if official else "",
            "catalogVersion": CATALOG_VERSION,
        })
        output.append(item)
    return output


def catalog_info() -> dict[str, str]:
    return {"version": CATALOG_VERSION, "source": CATALOG_SOURCE, "scope": CATALOG_SCOPE}

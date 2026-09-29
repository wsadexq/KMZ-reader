"""Normalized route data used by the KMZ parser and browser preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any


@dataclass
class Waypoint:
    index: int
    longitude: float
    latitude: float
    height: float | None = None
    ellipsoid_height: float | None = None
    height_mode: str | None = None
    speed: float | None = None
    heading: str | None = None
    turn_mode: str | None = None
    actions: list[str] = field(default_factory=list)
    source: str = "unknown"


@dataclass
class RouteModel:
    source_file: str
    source_files: list[str] = field(default_factory=list)
    template_type: str | None = None
    template_id: int | None = None
    wayline_id: int | None = None
    height_mode: str | None = None
    execute_height_mode: str | None = None
    global_speed: float | None = None
    waypoints: list[Waypoint] = field(default_factory=list)
    template_waypoints: list[Waypoint] = field(default_factory=list)
    lines: list[list[tuple[float, float]]] = field(default_factory=list)
    polygons: list[list[tuple[float, float]]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def all_points(self) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        points.extend((p.longitude, p.latitude) for p in self.waypoints)
        points.extend((p.longitude, p.latitude) for p in self.template_waypoints)
        points.extend(point for line in self.lines for point in line)
        points.extend(point for polygon in self.polygons for point in polygon)
        return points

    def compute_statistics(self) -> dict[str, Any]:
        active = self.waypoints or self.template_waypoints
        route_points = [(p.longitude, p.latitude) for p in active]
        total_distance = sum(
            haversine_meters(a[1], a[0], b[1], b[0])
            for a, b in zip(route_points, route_points[1:])
        )
        heights = [p.height for p in active if p.height is not None]
        speeds = [p.speed for p in active if p.speed is not None]
        all_points = self.all_points()
        bounds = None
        if all_points:
            lons, lats = zip(*all_points)
            bounds = {
                "minLongitude": min(lons),
                "minLatitude": min(lats),
                "maxLongitude": max(lons),
                "maxLatitude": max(lats),
            }
        self.statistics = {
            "waypointCount": len(self.waypoints),
            "templateWaypointCount": len(self.template_waypoints),
            "lineCount": len(self.lines),
            "polygonCount": len(self.polygons),
            "distanceMeters": round(total_distance, 3),
            "minHeight": min(heights) if heights else None,
            "maxHeight": max(heights) if heights else None,
            "minSpeed": min(speeds) if speeds else None,
            "maxSpeed": max(speeds) if speeds else None,
            "bounds": bounds,
            "warningCount": len(self.warnings),
        }
        return self.statistics

    def to_dict(self) -> dict[str, Any]:
        self.compute_statistics()
        value = asdict(self)
        value["lines"] = [
            [{"longitude": lon, "latitude": lat} for lon, lat in line]
            for line in self.lines
        ]
        value["polygons"] = [
            [{"longitude": lon, "latitude": lat} for lon, lat in polygon]
            for polygon in self.polygons
        ]
        return value


def haversine_meters(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius = 6_371_008.8
    phi_a = math.radians(latitude_a)
    phi_b = math.radians(latitude_b)
    d_phi = math.radians(latitude_b - latitude_a)
    d_lambda = math.radians(longitude_b - longitude_a)
    value = math.sin(d_phi / 2) ** 2 + math.cos(phi_a) * math.cos(phi_b) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(min(1.0, value)))

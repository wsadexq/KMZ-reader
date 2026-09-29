# Third-party notices

This project bundles Leaflet 1.9.4 in `web/vendor/leaflet/`.

Leaflet is copyright (c) 2010-2023, Vladimir Agafonkin. It is distributed under the BSD-2-Clause license. The bundled distribution and license are retained for local browser use.

This project bundles CesiumJS 1.145.0 in `web/vendor/cesium/` for the local 3D route view. CesiumJS is distributed under the Apache-2.0 license; the bundled license is retained as `web/vendor/cesium/CESIUM-LICENSE.md`.

Build-only dependencies include PyInstaller 6.16.0 and defusedxml 0.7.1. They are used to create the Windows executable and are not required on an end user's machine. NSIS is used only to create `install.exe`.

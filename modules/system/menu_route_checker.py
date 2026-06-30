from pathlib import Path
import re


class MenuRouteChecker:
    def __init__(self, root=None):
        self.root = Path(root or Path.cwd())

    def check(self):
        main = (self.root / "main.py").read_text(encoding="utf-8")
        menu_items = re.findall(r'^\s*"([^"]+)",\s*$', main, flags=re.M)
        routes = re.findall(r'^\s*"([^"]+)":\s*(\w+),\s*$', main, flags=re.M)
        route_names = {name for name, _ in routes}
        missing_routes = [m for m in menu_items if m not in route_names]
        extra_routes = [name for name, _ in routes if name not in menu_items]
        return {
            "menu_count": len(menu_items),
            "route_count": len(routes),
            "missing_routes": missing_routes,
            "extra_routes": extra_routes,
            "ok": not missing_routes and not extra_routes,
        }

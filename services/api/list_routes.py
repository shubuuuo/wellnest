from app.main import app

for route in sorted(app.routes, key=lambda r: getattr(r, "path", "")):
    methods = getattr(route, "methods", None)
    if methods:
        print(",".join(sorted(methods - {"HEAD", "OPTIONS"})).ljust(8), route.path)
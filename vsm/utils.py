import aiohttp_cors


def setup_cors(app):
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )
    # Configure CORS on all routes (including method OPTIONS)
    for route in list(app.router.routes()):
        cors.add(route)

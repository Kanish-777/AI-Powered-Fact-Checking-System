import modal

app = modal.App("ai-powered-fact-checking-system")

image = modal.Image.from_dockerfile(
    "./Dockerfile",
    context_dir="."
)

@app.function(
    image=image,
    cpu=1.0,
    memory=2048,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=300,
)
@modal.asgi_app()
def fastapi_app():
    from main import app as web_app
    return web_app
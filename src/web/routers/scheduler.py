"""Scheduler routes — view and manage scheduled jobs."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["scheduler"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/", response_class=HTMLResponse)
async def scheduler_page(request: Request):
    sched = getattr(request.app.state, "scheduler", None)
    jobs = sched.get_jobs() if sched else []

    template = _load_template("pages/scheduler.html")
    return template.render(request=request, jobs_obj=jobs)


@router.post("/pause/{job_id}", response_class=HTMLResponse)
async def pause_job(request: Request, job_id: str):
    sched = getattr(request.app.state, "scheduler", None)
    if sched:
        sched.pause_job(job_id)
    return HTMLResponse("")


@router.post("/resume/{job_id}", response_class=HTMLResponse)
async def resume_job(request: Request, job_id: str):
    sched = getattr(request.app.state, "scheduler", None)
    if sched:
        sched.resume_job(job_id)
    return HTMLResponse("")


@router.post("/run/{job_id}", response_class=HTMLResponse)
async def run_job_now(request: Request, job_id: str):
    sched = getattr(request.app.state, "scheduler", None)
    if sched:
        sched.run_job_now(job_id)
    return HTMLResponse("")

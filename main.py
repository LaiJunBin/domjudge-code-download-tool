from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import request
from utils import base64_decode, random_ascii_letters, file2blob
import zipstream
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from io import BytesIO
from typing import Optional
import threading
import asyncio


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sockets = {}

@app.websocket('/ws')
async def websocket_endpoint(socket: WebSocket):
    await socket.accept()
    token = random_ascii_letters(16)
    sockets[token] = socket
    await socket.send_json({
        'type': 'init',
        'data': token
    })
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        del sockets[token]


@app.get('/')
def index():
    return HTMLResponse(open('pages/index.html').read())


@app.get('/contests')
def get_contests():
    contests = request.get('/api/v4/contests')
    contests = [{
        'id': contest['id'],
        'name': contest['name'],
    } for contest in contests]
    return contests


@app.get('/contests/{contest_id}')
def get_contest(contest_id: int):
    contests = get_contests()
    for contest in contests:
        if int(contest['id']) == contest_id:
            submissions = request.get(f'/api/v4/contests/{contest_id}/submissions')
            contest['submission_length'] = len(submissions)
            return contest

    return None


async def run_get_contest_source_code(
        contest, teams, problems, languages, judgements, submissions, socket
):
    zip = zipstream.ZipFile()
    for i in range(len(submissions)):
        submission = submissions[i]

        id = submission['id']
        team = teams[submission['team_id']]
        name = team[0]
        if team[1]:
            name += '_' + team[1]

        problem = problems[submission['problem_id']]
        extension = languages[submission['language_id']]
        judge_type = judgements[submission['id']]
        source = base64_decode(
            request.get(f'/api/v4/contests/{contest["id"]}/submissions/{submission["id"]}/source-code')[0]['source']
        )

        filename = f'{id}_{name}_{judge_type}.{extension}'
        zip.writestr(f'{problem}/{filename}', source.encode())

        if socket:
            try:
                await socket.send_json({
                    'type': 'processing',
                    'data': i + 1
                })
            except:
                return {}

    zip_file = BytesIO()
    for zip_data in zip:
        zip_file.write(zip_data)

    zip.close()
    zip_file.seek(0)

    if socket:
        await socket.send_json({
            'type': 'success',
            'data': 'data:application/zip;base64,' + file2blob(zip_file)
        })
        return

    return StreamingResponse(zip_file, headers={
        'Content-Disposition': f'attachment; filename={contest["name"]}.zip',
        'Content-Type': 'application/zip'
    })


@app.get('/contests/{contest_id}/sources')
async def get_contest_source_code(contest_id: int, program_id: Optional[str] = ''):
    socket = sockets.get(program_id, None)
    contest = get_contest(contest_id)
    if contest is None:
        return JSONResponse({
            'message': 'The contest not found.'
        }, 404)

    default_extensions = {
        'python3': 'py'
    }

    teams = request.get(f'/api/v4/contests/{contest_id}/teams')
    teams = {team['id']: [team['name'], team['display_name']] for team in teams}

    problems = request.get(f'/api/v4/contests/{contest_id}/problems')
    problems = {problem['id']: problem['name'] for problem in problems}

    languages = request.get(f'/api/v4/contests/{contest_id}/languages')
    languages = {
        **{lang['id']: lang['extensions'][0] for lang in languages},
        **default_extensions
    }

    judgements = request.get(f'/api/v4/contests/{contest_id}/judgements')
    judgements = {
        judgement['submission_id']: judgement['judgement_type_id']
        for judgement in judgements if judgement['judgement_type_id']
    }

    submissions = request.get(f'/api/v4/contests/{contest_id}/submissions')
    if (len(submissions) == 0):
        return JSONResponse({
            'message': 'No submission record for this contest.'
        }, 404)

    args = (contest, teams, problems, languages, judgements, submissions, socket)
    if socket:
        thread = threading.Thread(target=asyncio.run, args=(run_get_contest_source_code(*args),))
        thread.start()
    else:
        return await run_get_contest_source_code(*args)

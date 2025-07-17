from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from pytube import YouTube
from io import BytesIO
import asyncio

app = FastAPI(title="YouTube Video Downloader")

@app.get("/download")
async def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        # Use pytube to get video
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
        if not stream:
            raise HTTPException(status_code=404, detail="No suitable stream found")

        # Download to bytes buffer
        buffer = BytesIO()
        
        def download_stream():
            stream.stream_to_buffer(buffer)
            buffer.seek(0)

        # Download synchronously inside thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download_stream)

        filename = yt.title + ".mp4"
        # Sanitize filename for http headers
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (" ", ".", "_")]).rstrip()

        return StreamingResponse(buffer, media_type="video/mp4", headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

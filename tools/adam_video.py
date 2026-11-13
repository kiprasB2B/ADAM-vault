#!/usr/bin/env python3
"""ADAM video pipeline: balsas + dainos priedainis + FOLLOW FOR MORE pabaiga.

Naudojimas:
  python tools/adam_video.py --video <Drive nuoroda arba kelias> --song <mp3 kelias> \
      --out media/vardas.mp4 [--max 27] [--start auto|sekundės]

Spausdina JSON su rezultatu (trukmė, dainos pradžia, failo dydis).
"""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.request

MODEL = "UVR-MDX-NET-Voc_FT.onnx"
MODEL_URL = "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/" + MODEL
FONTS = ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Klaida: {' '.join(a[:3])}…\n{r.stderr[-800:]}")
    return r.stdout.strip()


def duration(f):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f))


def fetch_video(src, workdir):
    m = re.search(r"/d/([\w-]{20,})|id=([\w-]{20,})", src)
    if not m:
        return src
    fid = m.group(1) or m.group(2)
    out = os.path.join(workdir, fid + ".mp4")
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    urllib.request.urlretrieve(url, out)
    return out


def chorus_start(song, length):
    """Labiausiai pasikartojanti ir garsiausia dainos dalis (≈ priedainis), pradžia ant ritmo."""
    import librosa, numpy as np
    y, sr = librosa.load(song, sr=22050, mono=True)
    hop = 512
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
    step = int(sr / hop * 0.5)
    n = chroma.shape[1] // step
    C = np.array([chroma[:, i*step:(i+1)*step].mean(1) for i in range(n)])
    C /= np.linalg.norm(C, axis=1, keepdims=True) + 1e-9
    E = np.array([rms[i*step:(i+1)*step].mean() for i in range(n)]); E /= E.max()
    S = C @ C.T
    W = min(int(length * 2), n - 1)
    best, bs = -1, 0
    for s in range(0, max(1, n - W)):
        reps = [np.mean([S[s+k, o+k] for k in range(0, W, 2)])
                for o in range(0, n - W, 4) if abs(o - s) >= W]
        score = 0.5 * (max(reps) if reps else 0) + 0.5 * E[s:s+W].mean()
        if score > best:
            best, bs = score, s
    t = bs * 0.5
    bt = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    if len(bt):
        t = float(bt[np.argmin(abs(bt - t))])
    return max(0.0, min(t, len(y) / sr - length))


def vocals(video, workdir):
    wav = os.path.join(workdir, "orig.wav")
    sh("ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "2", "-ar", "44100", wav)
    mdir = os.path.expanduser("~/.adam-models"); os.makedirs(mdir, exist_ok=True)
    if not os.path.exists(os.path.join(mdir, MODEL)):
        urllib.request.urlretrieve(MODEL_URL, os.path.join(mdir, MODEL))
    sh("audio-separator", wav, "--model_filename", MODEL, "--model_file_dir", mdir,
       "--output_dir", workdir, "--single_stem", "Vocals", "--output_format", "WAV")
    return next(os.path.join(workdir, f) for f in os.listdir(workdir) if "(Vocals)" in f)


def endcard(path):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 1080, 1920
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([42, 42, W-42, H-42], outline=(255, 255, 255, 235), width=5)
    font = ImageFont.truetype(next(f for f in FONTS if os.path.exists(f)), 44)
    txt = "FOLLOW FOR MORE"; tw = d.textlength(txt, font=font)
    ph, pw = 96, int(tw + 90); cx, cy = int(W*0.655), int(H*0.665)
    x0, y0 = cx - pw//2, cy - ph//2
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rounded_rectangle([x0, y0+6, x0+pw, y0+ph+6], radius=ph//2, fill=(0, 0, 0, 90))
    im = Image.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(10)), im); d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x0+pw, y0+ph], radius=ph//2, fill=(255, 79, 139, 255))
    bb = d.textbbox((0, 0), txt, font=font)
    d.text((cx-(bb[2]-bb[0])/2-bb[0], cy-(bb[3]-bb[1])/2-bb[1]), txt, font=font, fill=(17, 17, 17, 255))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--song", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--max", type=float, default=27.0)
    ap.add_argument("--start", default="auto"); ap.add_argument("--music-volume", type=float, default=0.55)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as wd:
        src = fetch_video(a.video, wd)
        D = min(a.max, duration(src))
        st = chorus_start(a.song, D) if a.start == "auto" else float(a.start)
        voc = vocals(src, wd)
        card = os.path.join(wd, "card.png"); endcard(card)
        fc = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[bv];"
              f"[2:v]scale=1080:1920[ov];[bv][ov]overlay=0:0:enable='gte(t,{D-1:.3f})'[v];"
              f"[1:a]atrim=start={st}:duration={D},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,"
              f"afade=t=out:st={max(0, D-0.6)}:d=0.6,volume={a.music_volume}[m];"
              f"[3:a]asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
              f"[md][v2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95,afade=t=out:st={D-0.4:.2f}:d=0.4[a]")
        sh("ffmpeg", "-v", "error", "-y", "-i", src, "-i", a.song, "-loop", "1", "-i", card, "-i", voc,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{D}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", a.out)
    print(json.dumps({"out": a.out, "trukme": round(D, 1), "dainos_pradzia": round(st, 1),
                      "dydis_mb": round(os.path.getsize(a.out)/1e6, 1)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

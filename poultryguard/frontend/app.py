"""
app.py

PoultryGuard frontend: a clean Gradio UI for farmers to upload a sick bird
photo and receive a diagnosis, treatment plan, priced feed formula, nearby
agrovets, and quarantine recommendation -- with an English/Twi toggle.

This talks to the backend over HTTP (see backend/main.py), so the frontend
and backend can be deployed and scaled independently (e.g. backend on a
GPU machine, frontend on a small web host).

Run with:
    python frontend/app.py
(make sure the backend is running first: uvicorn backend.main:app --port 8000)
"""

import os

import gradio as gr
import requests

BACKEND_URL = os.environ.get("POULTRYGUARD_BACKEND_URL", "http://localhost:8000")


def diagnose(image, lat, lon, flock_feed_kg, language):
    if image is None:
        return "Please upload a photo of the bird first.", "", "", "", ""

    include_twi = language == "Twi (and English)"

    files = {"image": ("upload.jpg", _to_jpeg_bytes(image), "image/jpeg")}
    data = {
        "lat": lat,
        "lon": lon,
        "flock_feed_kg": flock_feed_kg,
        "include_twi": include_twi,
    }

    try:
        response = requests.post(f"{BACKEND_URL}/diagnose", files=files, data=data, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        error_msg = f"Could not reach the diagnosis backend: {exc}"
        return error_msg, "", "", "", ""

    report = response.json()
    return _format_report(report, include_twi)


def _to_jpeg_bytes(image) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG")
    return buffer.getvalue()


def _format_report(report: dict, include_twi: bool) -> tuple:
    disease_name = report["disease_name"]
    twi_suffix = ""
    if include_twi and report.get("twi"):
        twi_suffix = f"  ({report['twi']['disease_name_twi']})"

    diagnosis_header = (
        f"### 🩺 Diagnosis: {disease_name}{twi_suffix}\n"
        f"**Confidence:** {report['confidence'] * 100:.1f}%\n\n"
        f"{report['advisory']}"
    )
    if report["symptoms"]:
        symptoms_list = "\n".join(f"- {s}" for s in report["symptoms"])
        diagnosis_md = f"{diagnosis_header}\n\n**Symptoms observed in this disease:**\n{symptoms_list}"
    else:
        diagnosis_md = diagnosis_header

    treatment_md = "### 💊 Treatment Steps\n" + "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(report["treatment_steps"])
    )

    feed = report["feed_formula"]
    feed_lines = [
        f"- {item['ingredient'].replace('_', ' ').title()}: {item['kg']} kg "
        f"× GHS {item['unit_price_ghs']}/kg = GHS {item['line_cost_ghs']}"
        for item in feed["line_items"]
    ]
    feed_md = (
        f"### 🌾 Recovery Feed Formula ({feed['total_kg']} kg batch)\n"
        + "\n".join(feed_lines)
        + f"\n\n**Total cost: GHS {feed['total_cost_ghs']}**"
    )

    agrovet_lines = [
        f"- **{shop['name']}** ({shop['area']}) — {shop['distance_km']} km away — "
        f"📞 {shop['phone']} — [Directions]({shop['directions_url']})"
        for shop in report["nearest_agrovets"]
    ]
    agrovet_md = "### 🏪 Nearest Agrovets\n" + "\n".join(agrovet_lines)

    quarantine_icon = "🔴 YES" if report["quarantine_required"] else "🟢 NO"
    twi_quarantine = ""
    if include_twi and report.get("twi"):
        twi_quarantine = f"  ({report['twi']['quarantine_twi']})"
    quarantine_md = (
        f"### 🚧 Quarantine Recommendation: {quarantine_icon}{twi_quarantine}\n"
        f"{report['quarantine_reason']}"
    )

    return diagnosis_md, treatment_md, feed_md, agrovet_md, quarantine_md


with gr.Blocks(title="PoultryGuard") as demo:
    gr.Markdown(
        "# 🐔 PoultryGuard\n"
        "Upload a photo of a sick bird to get a diagnosis, treatment plan, "
        "recovery feed formula priced for Kumasi, nearby agrovets, and a "
        "quarantine recommendation."
    )

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(type="pil", label="Photo of the sick bird")
            lat_input = gr.Number(value=6.6885, label="Farmer latitude (Kumasi default)")
            lon_input = gr.Number(value=-1.6244, label="Farmer longitude (Kumasi default)")
            feed_kg_input = gr.Number(value=10.0, label="Recovery feed batch size (kg)")
            language_input = gr.Radio(
                ["English only", "Twi (and English)"],
                value="English only",
                label="Language",
            )
            submit_btn = gr.Button("Diagnose", variant="primary")

        with gr.Column(scale=2):
            diagnosis_output = gr.Markdown()
            treatment_output = gr.Markdown()
            feed_output = gr.Markdown()
            agrovet_output = gr.Markdown()
            quarantine_output = gr.Markdown()

    submit_btn.click(
        fn=diagnose,
        inputs=[image_input, lat_input, lon_input, feed_kg_input, language_input],
        outputs=[diagnosis_output, treatment_output, feed_output, agrovet_output, quarantine_output],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

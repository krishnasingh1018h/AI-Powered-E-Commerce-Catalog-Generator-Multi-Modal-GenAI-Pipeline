import os
import io
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from model.schema import ApparelListingSchema
from model.main import pipeline, parser, vision_llm, model, prompt
import requests
from PIL import Image
import json

app = FastAPI(
    title="E-Commerce Apparel Listing Generator",
    description="A FastAPI application that transforms raw apparel specifications into structured e-commerce product listings.",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Root Route
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API is running. Frontend static/index.html not found."}

class RawAttributesRequest(BaseModel):
    raw_attributes: str
class BatchAttributesResponse(BaseModel):
    raw_specs_list: List[str]

@app.get("/status")
def get_status():
    return {"status": "online", "model": "Qwen2.5-7B-Instruct", "framework": "LangChain/FastAPI"}

@app.post("/generate-single", response_model=ApparelListingSchema)
async def generate_single(request: RawAttributesRequest):
    try:
        format_instructions = parser.get_format_instructions()
        result = pipeline.invoke({
            "raw_specs": request.raw_attributes,
            "format_instructions": format_instructions
        })
        return result
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "invalid_api_key" in err_str or "Invalid API Key" in err_str:
            raise HTTPException(status_code=401, detail="INVALID_API_KEY: Invalid Groq API key. Please update GROQ_API_KEY in your .env file with a valid key from console.groq.com.")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-single-stream")
async def generate_single_stream(request: RawAttributesRequest):
    try:
        format_instructions = parser.get_format_instructions()
        formatted_prompt = prompt.format(
            raw_specs=request.raw_attributes,
            format_instructions=format_instructions
        )

        async def stream_generator():
            async for chunk in model.astream(formatted_prompt):
                if chunk.content:
                    payload = json.dumps({"text": chunk.content})
                    yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "invalid_api_key" in err_str or "Invalid API Key" in err_str:
            raise HTTPException(status_code=401, detail="INVALID_API_KEY: Invalid Groq API key. Please update GROQ_API_KEY in your .env file with a valid key from console.groq.com.")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate-batch", response_model=List[ApparelListingSchema])
async def generate_batch(request: BatchAttributesResponse):
    try:
        format_instructions= parser.get_format_instructions()
        batch_input = [
            {"raw_specs": req_str, "format_instructions": format_instructions} 
            for req_str in request.raw_specs_list
            ]

        structured_results = pipeline.batch(batch_input, config={"max_concurrency": 3})
        return structured_results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate-image", response_model=ApparelListingSchema)
async def generate_from_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        # 2. Open the image with Pillow for on-the-fly optimization
        img = Image.open(io.BytesIO(image_bytes))
        
        # 3. Convert RGBA/PNG to RGB mode so it saves cleanly as JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # 4. Downscale if the resolution is massive (Llama vision caps processing around 1120x1120 anyway)
        max_dimension = 1200
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
        # 5. Compress and save to an in-memory byte buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)  # Quality 80 drops file size drastically with zero visible data loss
        compressed_bytes = buffer.getvalue()
        
        # 6. Encode the small, optimized byte string to Base64
        image_b64 = base64.b64encode(compressed_bytes).decode("utf-8")
        
        # 7. Enhanced Vision Prompt with Strict Clothing Validation
        vision_prompt = """You are an expert e-commerce catalog vision auditor specializing in fashion and apparel.

STEP 1: CLOTHING VALIDATION
Inspect the provided image carefully. Determine whether the image clearly depicts a garment, clothing item, apparel, footwear, or fashion accessory (e.g. shirt, t-shirt, dress, pants, jeans, jacket, saree, shoes, hoodie, skirt, shorts, sweater, suit, etc.).
If the image DOES NOT contain any clothing or apparel (for example: if it is a screenshot of code/text, a document, a building, animal, vehicle, landscape, electronics, food, etc.), reply EXACTLY with:
"NOT_CLOTHING: The uploaded image does not contain apparel or clothing. Please upload a clear photo of a garment or fashion item."

STEP 2: APPAREL EXTRACTION (Only if valid clothing item)
If the image DOES contain clothing/apparel:
Ignore any human model, mannequin, or background elements. Focus purely on the apparel item.
Describe in detail:
- Item type and style (e.g. A-line midi dress, slim fit denim jeans, oversized hoodie)
- Fabric texture, weave, and visual material quality (e.g. breathable cotton denim, silk chiffon, knit wool)
- Color, shades, pattern, and wash (e.g. indigo blue wash, floral botanical print, solid pastel pink)
- Design highlights: necklines, sleeves, pockets, closures, waistline, hemlines, embellishments, stitching.
- Intended wearing occasions and style aesthetics (casual weekend, formal office, festive, activewear).
"""

        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
        vision_response = vision_llm.invoke([message])
        raw_visual_fact = str(vision_response.content).strip()

        # Check for Non-Clothing Validation failure
        if "NOT_CLOTHING" in raw_visual_fact or raw_visual_fact.startswith("NOT_CLOTHING"):
            raise HTTPException(
                status_code=400,
                detail="NOT_CLOTHING: The uploaded image does not contain clothing or apparel. Please upload a clear product photo of a garment (e.g. shirt, dress, jeans, saree, jacket)."
            )

        format_instruction = parser.get_format_instructions()
        final_structured_output = pipeline.invoke({
            "raw_specs": raw_visual_fact,
            "format_instructions": format_instruction
        })
        return final_structured_output
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image-stream")
async def generate_from_image_stream(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        max_dimension = 1200
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        compressed_bytes = buffer.getvalue()
        image_b64 = base64.b64encode(compressed_bytes).decode("utf-8")
        
        vision_prompt = """You are an expert e-commerce catalog vision auditor specializing in fashion and apparel.

STEP 1: CLOTHING VALIDATION
Inspect the provided image carefully. Determine whether the image clearly depicts a garment, clothing item, apparel, footwear, or fashion accessory (e.g. shirt, t-shirt, dress, pants, jeans, jacket, saree, shoes, hoodie, skirt, shorts, sweater, suit, etc.).
If the image DOES NOT contain any clothing or apparel (for example: if it is a screenshot of code/text, a document, a building, animal, vehicle, landscape, electronics, food, etc.), reply EXACTLY with:
"NOT_CLOTHING: The uploaded image does not contain apparel or clothing. Please upload a clear photo of a garment or fashion item."

STEP 2: APPAREL EXTRACTION (Only if valid clothing item)
If the image DOES contain clothing/apparel:
Ignore any human model, mannequin, or background elements. Focus purely on the apparel item.
Describe in detail:
- Item type and style (e.g. A-line midi dress, slim fit denim jeans, oversized hoodie)
- Fabric texture, weave, and visual material quality (e.g. breathable cotton denim, silk chiffon, knit wool)
- Color, shades, pattern, and wash (e.g. indigo blue wash, floral botanical print, solid pastel pink)
- Design highlights: necklines, sleeves, pockets, closures, waistline, hemlines, embellishments, stitching.
- Intended wearing occasions and style aesthetics (casual weekend, formal office, festive, activewear).
"""
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
        vision_response = vision_llm.invoke([message])
        raw_visual_fact = str(vision_response.content).strip()

        if "NOT_CLOTHING" in raw_visual_fact or raw_visual_fact.startswith("NOT_CLOTHING"):
            raise HTTPException(
                status_code=400,
                detail="NOT_CLOTHING: The uploaded image does not contain clothing or apparel. Please upload a clear product photo of a garment (e.g. shirt, dress, jeans, saree, jacket)."
            )

        format_instruction = parser.get_format_instructions()
        formatted_prompt = prompt.format(
            raw_specs=raw_visual_fact,
            format_instructions=format_instruction
        )

        async def stream_generator():
            async for chunk in model.astream(formatted_prompt):
                if chunk.content:
                    payload = json.dumps({"text": chunk.content})
                    yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "invalid_api_key" in err_str or "Invalid API Key" in err_str:
            raise HTTPException(status_code=401, detail="INVALID_API_KEY: Invalid Groq API key. Please update GROQ_API_KEY in your .env file with a valid key from console.groq.com.")
        raise HTTPException(status_code=500, detail=f"Vision Pipeline Error: {str(e)}")

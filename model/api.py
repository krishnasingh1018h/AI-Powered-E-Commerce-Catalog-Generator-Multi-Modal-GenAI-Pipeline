import os
import io
import base64
from fastapi import FastAPI, HTTPException,UploadFile,File
from pydantic import BaseModel
from typing import List,Dict,Any
from model.schema import ApparelListingSchema
from model.main import pipeline,parser,vision_llm
import requests
from PIL import Image
app = FastAPI(
title="E-Commerce Apparel Listing Generator",
description="A FastAPI application that transforms raw apparel specifications into structured e-commerce product listings.",
)

class RawAttributesRequest(BaseModel):
    raw_attributes:str
class BatchAttributesResponse(BaseModel):
    raw_specs_list:List[str]

@app.get("/status")
def get_status():
    return {"status": "online", "model": "Qwen2.5-7B-Instruct", "framework": "LangChain/FastAPI"}

@app.post("/generate-single", response_model=ApparelListingSchema)
async def generate_single(request: RawAttributesRequest):
    try:
        format_instructions = parser.get_format_instructions()
        result = pipeline.invoke({
            "raw_specs": request.raw_attributes,
            "format_instructions":format_instructions})
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        
        # --- The rest of your payload execution stays exactly the same ---
        vision_prompt = "..." 
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
        vision_response = vision_llm.invoke([message])
        raw_visual_fact = vision_response.content
        format_instruction = parser.get_format_instructions()
        final_structured_output =pipeline.invoke({
            "raw_specs":raw_visual_fact,
            "format_instructions":format_instruction
        })
        return final_structured_output
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Hugging Face Vision Pipeline Error:{str(e)}")
    

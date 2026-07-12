from pydantic import BaseModel,Field
from typing import List

class ApparelListingSchema(BaseModel):
    product_title: str = Field(..., description="A single, highly searchable, click-optimized e-commerce product title incorporating fabric, pattern, and style.")
    product_description: List[str] = Field(..., description="A list containing exactly 3 distinct bullet points detailing: 1. Fabric/comfort, 2. Design/fit elements, 3. Occasion/care instructions.")
    seo_keywords: List[str] = Field(..., description="A list of exactly 5 highly relevant search keywords or short tags buyers use to find this type of clothing online.")

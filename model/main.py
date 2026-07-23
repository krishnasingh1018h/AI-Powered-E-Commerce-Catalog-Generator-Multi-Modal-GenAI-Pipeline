from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_huggingface import ChatHuggingFace,HuggingFaceEndpoint
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from model.schema import ApparelListingSchema
import os
import pandas as pd
import json
load_dotenv()

model = ChatOpenAI(
    model="openai/gpt-oss-120b",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)

parser = PydanticOutputParser(pydantic_object=ApparelListingSchema)
prompt_template = """You are an elite e-commerce catalog engineer specializing in digital clothing marketplaces like Meesho, Myntra, and Amazon.

Transform the following raw apparel specifications into a professional, highly optimized, structured product listing.

Raw Attributes: {raw_specs}

{format_instructions}
"""
prompt = PromptTemplate.from_template(prompt_template)
pipeline = (prompt | model | parser)

vision_llm =ChatOpenAI(
    model="qwen/qwen3.6-27b",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)



if __name__ == "__main__":
    input_file = "raw_attributes.csv"
    output_file = "output.csv"
    try:
        df=pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"file not found:{input_file}")
        exit()

    if "raw_attributes" not in df.columns:
        print(f"Column 'raw_attributes' not found in {input_file}")
        exit()
    input_list = df["raw_attributes"].astype(str).tolist()
    print(f"Processing {len(input_list)} items from {input_file}...")
    try:
        structured_results = pipeline.invoke(input_list,config={"max_concurrency":3})
    except Exception as e:
        print(f"Error occurred while processing items: {e}")
        exit()
    processed_results = []
    for idx,output in enumerate(structured_results):
        try:
            item_dict = output.model_dump()
            item_dict["original_id"] = idx
            processed_results.append(item_dict)
        except Exception as parse_error:
            print(f"Error reading output schema for item {idx}: {parse_error}")
    with open(output_file,'w',encoding='utf-8') as f:
        json.dump(processed_results,f,ensure_ascii=False,indent=4)
    print(f"Successfully saved {len(processed_results)} structured items to {output_file}")
